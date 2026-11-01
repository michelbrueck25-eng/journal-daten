import sys,os,io,contextlib,pickle,json,numpy as np,datetime as dt,collections
t=open('obsearch.py').read(); t=t[:t.index('rows=[]')]
with contextlib.redirect_stdout(io.StringIO()): exec(t)
SEL=sys.argv[1] if len(sys.argv)>1 else '/tmp/pf/obsel.pkl'; OFF=int(sys.argv[2]) if len(sys.argv)>2 else 0
sel=pickle.load(open(SEL,'rb'))
PRIV='/home/claude/journal-privat/forwardtest.json'; PUB='/home/claude/journal-daten'
F=json.load(open(PRIV)); bt=json.load(open(f'{PUB}/backtest-trades.json'))
S={x['id']:x for x in F['strategien']}
for n,(m,c,a,dv,te) in enumerate(sel,1+OFF):
    en,sb,tg,md,qs,age,grp=c[:7]; flt=c[7] if len(c)>7 else ''; tr=run(*c); sid=f'fw10-o{n}'
    fxs=[x for x in tr if x['sym'] not in PIPS]; swr=float(np.mean([0.3*(0.01 if x['sym'].endswith('JPY') else 0.0001)*x['bars']*7/5/x['risk'] for x in fxs])) if fxs else 0.0
    r=np.array([x['r'] for x in tr]); w=(r>0).mean()*100; gw=r[r>0].sum(); gl=-r[r<0].sum(); eq=np.cumsum(r); dd=float((np.maximum.accumulate(eq)-eq).max())
    mo=collections.OrderedDict()
    for x in sorted(tr,key=lambda x:x['date']):
        k=dt.date.fromisoformat(x['date'][:7]+'-01'); v=mo.setdefault(k,[0,0.0]); v[0]+=1; v[1]+=x['r']
    monate=[[(k-dt.date(1970,1,1)).days,v[0],round(v[1],2)] for k,v in mo.items()]
    yrs=(max(mo)-min(mo)).days/365.25+1/12; jahr=round(float(r.sum()/yrs),1)
    yj=collections.defaultdict(list)
    for x in tr: yj[x['date'][:4]].append(x['r'])
    je=', '.join(f"{y}: {np.mean(v):+.2f} R ({len(v)})" for y,v in sorted(yj.items()))
    regeln=(f"Zeitebene Daily. Daily-Orderblock Qualität {'A' if qs=='A' else 'A und B'}, Bewegung danach mindestens 2 ATR, Strukturbruch (Schluss über das Hoch der letzten 8 Kerzen, short darunter). {'Einstieg als Limit in der Zonenmitte, bei erster Berührung innerhalb von 5 Tagen ab Zonenberührung.' if en=='mid' else 'Einstieg als Limit am Zonenrand (long oben, short unten) bei der ersten Berührung.'} Stopp {sb} ATR hinter der Zone, Ziel {tg} R, höchstens {md} Tage. "
            +(f"Nur Zonen, die höchstens {age} Tage nach ihrer Entstehung berührt werden. " if age else '')+('Nur Devisenpaare, keine Metalle. ' if grp=='FX' else 'Alle Instrumente inkl. Gold und Silber. ')+({'weekly_trend':'Filter: nur in Richtung des Weekly-Trends (Wochenschluss gegen SMA20). ','cot_stark30':'Filter: COT-Index Basis minus Quote mindestens 30 in Handelsrichtung (nur Devisenpaare). '}.get(flt,''))+"Stopp zuerst bei gleicher Kerze, 1 Pip Spread (Metalle geschätzt).")
    ent=dict(id=sid,gruppe='Daily-Orderblock-Familie (Suchlauf 01.11.2026)',tf='Daily',status='Backtest vorhanden',
      name=f"Daily-OB A · {'Mitte' if en=='mid' else 'Rand'} · {tg} R · Stopp {sb} ATR · {md} Tage"+(f" · Alter ≤{age}" if age else '')+(' · nur FX' if grp=='FX' else '')+{'weekly_trend':' · Weekly-Trend','cot_stark30':' · COT stark'}.get(flt,''),
      beschreibung=regeln,regeln=regeln,
      notiz="Gleiche Familie wie Kandidat 1 bis 3 (Korrelation der Monatsergebnisse zu diesen zwischen 0,4 und 0,85). Aus 384 bzw. 270 (mit Filter) Varianten ausgewählt, die in Entwicklung und Prüfung je über 0,25 R lagen.",
      bericht=f"Zeitebene Daily. {len(r)} Trades, Winrate {w:.1f} %, E: {r.mean():+.3f} R netto, Profitfaktor {gw/gl:.2f}, Drawdown {dd:.1f} R, {jahr:+.1f} R pro Jahr. Entwicklung (bis 2022): {dv[0]} Trades, E {dv[1]:+.3f} R. Prüfung (ab 2023): {te[0]} Trades, E {te[1]:+.3f} R. Je Jahr: {je}. Einschränkungen: Variante aus 384 getesteten ausgewählt, Zonen benachbarter Paare sind korreliert, kein Zufallsvergleich für diese Variante gerechnet. Kosten: 1 Pip Spread; Swaps (0,3 Pip je Kalendertag) sind in den Zahlen noch nicht abgezogen und kosten im Mittel etwa {swr:.3f} R je Trade, E läge dann bei etwa {r.mean()-swr:+.2f} R.",
      plan="Im Forward-Test beobachten. Für diese Familie fehlt noch die Forward-Engine, bis dahin nur Backtest.",
      backtest=dict(n=len(r),wr=round(float(w),1),avg=round(float(r.mean()),3),pf=round(float(gw/gl),2),dd=round(dd,1),jahr=jahr,monate=monate),
      forward=dict(n=0,offen=0,equity=[],kennzahlen={'n':0},testStart='2026-10-30',testEnde='2026-12-30',datenstand=str(F.get('forwardDatenstand','')),offen_r=0.0),
      offene=[],trades=[],cfg=dict(typ='ob',entry=en,stop=sb,tg=tg,md=md,q=qs,alter=age,grp=grp,filter=flt))
    if sid in S: S[sid].update(ent)
    else: F['strategien'].append(ent)
    bt[sid]=[[x['date'],x['sym'],'L' if x['L'] else 'S',round(float(x['r']),2),int(x['bars'])] for x in sorted(tr,key=lambda x:x['date'])]
    print(sid,ent['name'],len(r),round(w),round(r.mean(),3),dd,jahr)
json.dump(F,open(PRIV,'w'),ensure_ascii=False,separators=(',',':'))
G=dict(F);G['strategien']=[x for x in F['strategien'] if not x['gruppe'].startswith('Alter Test')]
json.dump(G,open(f'{PUB}/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump(bt,open(f'{PUB}/backtest-trades.json','w'),separators=(',',':'),ensure_ascii=False)
