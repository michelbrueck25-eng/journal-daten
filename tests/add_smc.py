"""Traegt die fuenf COT-bestaetigten Struktur-/SMC-Strategien als Beobachtung in forwardtest.json ein (einmalig, idempotent)."""
import os,sys,json,io,contextlib
os.environ['FW_START']='2010-01-01'
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()):
    import fwd
from fwd import *
import collections,datetime as dt
D={
'fw9-s1':('Sweep 20','Liquiditäts-Sweep (20 Tage)','Kurs sticht im Tagechart unter das 20-Tage-Tief (long) bzw. über das 20-Tage-Hoch (short) und schließt wieder zurück in die Range.',20,'Stopp 3 ATR, kein Ziel, 15 Tage'),
'fw9-s2':('FVG Retest','Fair-Value-Gap-Retest','Tageschart: Dreikerzen-Lücke (Fair Value Gap) in Trendrichtung, Einstieg beim ersten Rücklauf in die Lücke.',20,'Stopp 2 ATR, kein Ziel, 15 Tage'),
'fw9-s3':('OB nach BOS','Orderblock nach Strukturbruch','Tageschart: Orderblock, der einen Strukturbruch (BOS) ausgelöst hat, Einstieg beim ersten Rücklauf in die Zone.',20,'Stopp 2 ATR, kein Ziel, 25 Tage'),
'fw9-s4':('BOS Trend','Strukturbruch in Trendrichtung (BOS)','Tageschart: Schluss über das letzte Swing-Hoch (long) bzw. unter das Swing-Tief (short) in Richtung des Trends.',40,'Stopp 3 ATR, Ziel 1,5 R, 40 Tage'),
'fw9-s5':('BOS Retest','Strukturbruch-Retest','Tageschart: nach einem BOS Einstieg beim Rücklauf auf das durchbrochene Niveau.',40,'Stopp 2 ATR, Ziel 1,5 R, 40 Tage'),
}
F=json.load(open(f'{PRIV}/forwardtest.json')); bt=json.load(open(f'{PUB}/backtest-trades.json'))
S={x['id']:x for x in F['strategien']}
for sid,(nm,name,desc,win,par) in D.items():
    fn,kind,p=FW[sid]; busy={}; tr=[]
    for (s,i,L) in sorted(fn(),key=lambda z:(P[z[0]]['ts'][z[1]],z[0])):
        if i<=busy.get(s,-1) or i+1>=len(P[s]['d']['c']): continue
        t=fsim(s,i,L,**p)
        if not t: continue
        t.update(sym=s,dir='long' if L else 'short',date=t['open_date']); busy[s]=i+t['bars']
        if t['closed']: tr.append(t)
    K=stats(tr)
    mo=collections.OrderedDict()
    for t in tr:
        d=dt.date.fromisoformat(str(t['open_date'])[:10]); k=dt.date(d.year,d.month,1)
        a=mo.setdefault(k,[0,0.0]); a[0]+=1; a[1]+=t['r']
    monate=[[(k-dt.date(1970,1,1)).days,v[0],round(v[1],2)] for k,v in mo.items()]
    yrs=(max(mo)-min(mo)).days/365.25+1/12 if mo else 1
    n=len(tr); avg=round(float(np.mean([t['r'] for t in tr])),3)
    wr=round(100*float(np.mean([t['r']>0 for t in tr])),1)
    gw=sum(t['r'] for t in tr if t['r']>0); gl=-sum(t['r'] for t in tr if t['r']<0)
    eq=np.cumsum([t['r'] for t in tr]); dd=round(float(max(np.maximum.accumulate(eq)-eq)),1)
    jahr=round(float(sum(t['r'] for t in tr))/yrs,1)
    split='2023-01-01'; dv=[t['r'] for t in tr if str(t['open_date'])[:10]<split]; te=[t['r'] for t in tr if str(t['open_date'])[:10]>=split]
    f=lambda a:f"{np.mean(a):+.3f} R ({len(a)} Trades)" if a else 'keine Trades'
    cot='Commercial-Netto-Signal (156 Wochen, Extrem ab Abstand 70) oder Gold-Umkehr'
    regeln=(f"Zeitebene Daily. Signal: {desc} Filter: Das Setup zählt nur, wenn innerhalb der letzten {win} Tage ein COT-Signal in gleicher Richtung vorlag ({cot}). {par}. 1 Pip Spread plus 0,3 Pip Swap je Kalendertag, Stopp zuerst bei gleicher Kerze, ein Trade je Paar gleichzeitig.")
    ent=dict(id=sid,gruppe='Struktur und Smart Money mit COT-Filter 01.11.2026',tf='Daily',status='Backtest vorhanden',
      name=f"{name} + COT · {par}",beschreibung=regeln,regeln=regeln,
      notiz="Beobachtung: weniger als 300 Trades und Expectancy unter oder knapp an der Schwelle. Reine Preisstruktur hat im Test keinen Vorteil, nur mit COT-Bestätigung ergibt sich ein kleiner.",
      bericht=f"Zeitebene Daily. {n} Trades, Winrate {wr} %, E: {avg:+.3f} R netto, Profitfaktor {gw/gl:.2f}, Drawdown {dd} R, {jahr:+.1f} R pro Jahr. Entwicklung (bis 2022): E {f(dv)}. Prüfung (ab 2023): E {f(te)}. Einschränkungen: unter 300 Trades, Entwicklung und Prüfung weichen stark ab, aus vielen Varianten ausgewählt. Kosten: 1 Pip Spread plus 0,3 Pip Swap je Kalendertag.",
      plan="Reine Testphase bis ca. 30.12.2026. Danach entscheidest du: verlängern oder verwerfen.",
      backtest=dict(n=n,wr=wr,avg=avg,pf=round(gw/gl,2),dd=dd,jahr=jahr,monate=monate),
      forward=dict(n=0,offen=0,equity=[],kennzahlen={'n':0},testStart='2026-10-30',testEnde='2026-12-30',datenstand=str(F.get('forwardDatenstand','')),offen_r=0.0),
      offene=[],trades=[],cfg=dict(typ='smc',signal=nm,cot_fenster=win))
    if sid in S: S[sid].update(ent)
    else: F['strategien'].append(ent)
    bt[sid]=[[str(t['open_date'])[:10],t['sym'],'L' if t['dir']=='long' else 'S',round(float(t['r']),2),round(float(t['bars']))] for t in tr]
    print(sid,n,wr,avg,dd,jahr)
json.dump(F,open(f'{PRIV}/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
G=dict(F);G['strategien']=[x for x in F['strategien'] if not x['gruppe'].startswith('Alter Test')]
json.dump(G,open(f'{PUB}/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump(bt,open(f'{PUB}/backtest-trades.json','w'),separators=(',',':'),ensure_ascii=False)
