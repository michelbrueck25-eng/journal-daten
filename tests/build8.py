import json,random,datetime as dt
from h4b import sg2,D,run,summ,pip,cut,itertools,np
rnd=random.Random(5);rng=np.random.default_rng(9)
CF={'fw8-h1':(3,0.8,12,'RSI(3) Rücksetzer · Ziel 0,8 R · 12 Bars (Winrate 60 %)'),
    'fw8-h2':(3,0.6,36,'RSI(3) Rücksetzer · Ziel 0,6 R · 36 Bars (Winrate 71 %)'),
    'fw8-h3':(3,0.3,24,'RSI(3) Rücksetzer · Ziel 0,3 R · 24 Bars (Winrate 87 %, verdächtig hoch)')}
sg=sg2(5,False,20,None);P_='/home/claude/journal-privat/forwardtest.json';F=json.load(open(P_));F['strategien']=[x for x in F['strategien'] if not x['id'].startswith('fw8-')]
for sid,(sa,tg,N,name) in CF.items():
    tr=run(sg,sa,tg,N);a=summ(tr);r=np.array([x['r'] for x in tr]);t=[x['t'] for x in tr];yrs=(max(t)-min(t))/864e5/365.25
    dev=summ([x for x in tr if x['t']<cut]);te=summ([x for x in tr if x['t']>=cut])
    nulls=[]
    for _ in range(100):
        sh=[(s,i+rnd.randint(30,600),L) for (s,i,L) in sg if i+700<len(D[s]['c'])-N-3]
        q=run(sh,sa,tg,N)
        if q: nulls.append(np.mean([x['r'] for x in q]))
    nulls=np.array(nulls);ci=np.percentile([np.mean(rng.choice(r,len(r))) for _ in range(2000)],[5,95])
    py=len(r)/yrs;d=[]
    for _ in range(2000):
        x=rng.choice(r,int(round(py)));eq=np.cumsum(x);d.append(float((np.maximum.accumulate(np.r_[0,eq])[1:]-eq).max()))
    d50,d95=np.percentile(d,[50,95]);risk=round(min(1.5,5/max(d95,1e-9))*20)/20
    mo={}
    for x in tr:
        dd=dt.datetime.fromtimestamp(x['t']/1000,dt.timezone.utc);k=(dt.date(dd.year,dd.month,1)-dt.date(1970,1,1)).days;n0,s0=mo.get(k,(0,0));mo[k]=(n0+1,s0+x['r'])
    reg=f"4-Stunden-Kerzen, alle 28 Paare. Signal nach Schluss einer 4h-Kerze. Long: RSI(3) unter 5 und Schlusskurs über SMA(200) der 4h-Kerzen. Short: RSI(3) über 95 und Schlusskurs unter SMA(200). Nur Paare, deren ATR(14) mindestens 20 Pips beträgt (Spread-Anteil klein). Einstieg zur Eröffnung der nächsten 4h-Kerze, ein Trade je Paar gleichzeitig. Stopp {sa} ATR(14), Ziel {str(tg).replace('.',',')} R, Ausstieg spätestens nach {N} Kerzen ({N*4} Stunden) zum Schlusskurs. Stopp zuerst bei gleicher Kerze."
    rep=f"Zeitebene 4 Stunden. {a['n']} Trades in {yrs:.1f} Jahren, Winrate {a['wr']} %, E: {a['avg']:+.3f} R netto, Profitfaktor {a['pf']}, Drawdown {a['dd']} R, {r.sum()/yrs:+.1f} R pro Jahr. Erste 60 % der Zeit: E: {dev.get('avg')} R ({dev['n']} Trades), letzte 40 %: E: {te.get('avg')} R ({te['n']} Trades). Zufallsvergleich (gleiche Signale an verschobener Zeit, 100 Läufe): Mittel {nulls.mean():+.3f} R, 95. Perzentil {np.percentile(nulls,95):+.3f} R, Anteil Läufe mit gleich gutem Ergebnis {(nulls>=r.mean()).mean()*100:.0f} %. 90-%-Intervall der Expectancy: {ci[0]:.2f} bis {ci[1]:.2f} R. Einschränkungen: weniger als 300 Trades, nur rund 1,4 Jahre 4h-Daten (Apr 2025 bis Nov 2026) und eine Marktphase, E unter deiner Schwelle von 0,15 R, aus rund 150 Varianten ausgewählt. Kosten: 1 Pip Spread plus 0,3 Pip Swap je Kalendertag (Annahme)."
    F['strategien'].append(dict(id=sid,gruppe='4-Stunden-Strategien mit hoher Winrate 01.11.2026',tf='4H',status='Backtest vorhanden',name=name,beschreibung=reg,regeln=reg,
      notiz='Beobachtung auf Wunsch des Nutzers: E unter 0,15 R und weniger als 300 Trades.'+(' Winrate über 80 Prozent ist verdächtig hoch.' if a['wr']>80 else ''),bericht=rep,plan='Reine Testphase bis ca. 30.12.2026, keine Signale. Danach entscheidest du: verlängern, Signale oder verwerfen.',
      backtest=dict(n=a['n'],wr=a['wr'],avg=a['avg'],pf=a['pf'],dd=a['dd'],jahr=round(float(r.sum()/yrs),1),monate=[[k,v[0],round(v[1],2)] for k,v in sorted(mo.items())]),
      forward=dict(n=0,offen=0,equity=[]),offene=[],trades=[],cfg=dict(typ='h4',id=sid,th=5,minatr=20,sa=sa,tg=tg,N=N),
      risiko=dict(empfohlen_pct=risk,dd_median_pct=round(float(d50*risk),1),dd95_pct=round(float(d95*risk),1),monat_pct=round(float(r.mean()*py*risk/12),2),trades_pro_jahr=int(round(py)),annahme='Gesamtverlust-Limit 10 %, Ziel-Drawdown (95 %) höchstens 5 %, Deckel 1,5 % je Trade. Aus den echten Backtest-Trades.')))
    print(sid,a['n'],a['wr'],a['avg'],round(r.sum()/yrs,1),'null',round(nulls.mean(),3),'risk',risk,'monat%',round(float(r.mean()*py*risk/12),2))
F['stand']=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M')
json.dump(F,open(P_,'w'),ensure_ascii=False,separators=(',',':'))
G=dict(F);G['strategien']=[x for x in F['strategien'] if not x['gruppe'].startswith('Alter Test')]
json.dump(G,open('/home/claude/journal-daten/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
