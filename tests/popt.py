"""Portfolio-Optimierung auf Monatsebene: Gewichte/Auswahl nur aus Entwicklung (<2023) schaetzen, auf Pruefung (>=2023) auswerten."""
import json,numpy as np,datetime as dt,itertools
D='/home/claude/journal-daten'; F=json.load(open(f'{D}/forwardtest.json')); S={x['id']:x for x in F['strategien']}
def mon(x):
    m={}
    for a in x['backtest']['monate']:
        k=(dt.date(1970,1,1)+dt.timedelta(days=a[0])).strftime('%Y-%m'); m[k]=m.get(k,0)+a[2]
    return m
C=[i for i,x in S.items() if (x.get('backtest') or {}).get('monate') and x['tf']!='4H' and x['backtest']['avg']>=0.15 and x['backtest']['n']>=30 and not x['gruppe'].startswith('Alter Test')]
M={i:mon(S[i]) for i in C}
lo=min(k for m in M.values() for k in m); ks=[]; y,m=map(int,lo.split('-'))
while (y,m)<=(2026,10): ks.append(f'{y}-{m:02d}'); m+=1; y+=(m>12); m=1 if m>12 else m
X=np.array([[M[i].get(k,0) for k in ks] for i in C]); dev=np.array([k<'2023-01' for k in ks]); te=~dev
def met(r):
    eq=np.cumsum(r); dd=float(max(np.maximum.accumulate(np.r_[0,eq])[1:]-eq)) if len(r) else 0; yrs=len(r)/12
    return dict(Rj=round(r.sum()/yrs,1),dd=round(dd,1),cal=round(r.sum()/yrs/dd,2) if dd>0 else 0,worst=round(float(r.min()),1),pos=round(float((r>0).mean()*100)))
def show(nm,w):
    w=np.array(w,float); w=w/w.sum(); r=w@X
    md,mt=met(r[dev]),met(r[te]); print(f'{nm:34} Entw {md}\n{"":34} Pruef {mt}')
    return w,r
print(len(C),'Kandidaten (Daily/Weekly, E>=0,15, n>=30),',len(ks),'Monate; Entwicklung',int(dev.sum()),'Pruefung',int(te.sum()))
W={}
W['gleich']=show('Gleich gewichtet, alle',np.ones(len(C)))[0]
# Inverse Volatilitaet (Entwicklung)
sd=X[:,dev].std(axis=1)+1e-9; W['invvol']=show('Inverse Volatilitaet',1/sd)[0]
# Mittelwert/Varianz geschrumpft
mu=X[:,dev].mean(axis=1); w=np.clip(mu/(sd**2),0,None)**0.5; w=0.5*w/w.sum()+0.5/len(C); W['mv']=show('Rendite/Varianz (geschrumpft)',w)[0]
# Greedy-Auswahl (Entwicklung, Calmar), gleich gewichtet
sel=[]; best=-9
for _ in range(8):
    cand=None
    for j in range(len(C)):
        if j in sel: continue
        r=X[sel+[j]].mean(axis=0)[dev]; m=met(r); v=m['cal']
        if v>best*1.02 and (cand is None or v>cand[0]): cand=(v,j)
    if not cand: break
    best,j=cand; sel.append(j)
w=np.zeros(len(C)); w[sel]=1; W['greedy']=show('Auswahl (Greedy auf Entwicklung)',w)[0]
print('  gewaehlt:',[C[j] for j in sel])
# Mix: Greedy-Auswahl, Gewicht invvol
w2=np.zeros(len(C)); w2[sel]=1/sd[sel]; W['greedyiv']=show('Auswahl + inverse Vol.',w2)[0]
# Korrelationsbereinigt: Top E aus Entwicklung je Cluster (k1/k2) 
print('\nKorrelation Auswahl (Gesamt):')
for a,b in itertools.combinations(sel,2): 
    c=np.corrcoef(X[a],X[b])[0,1]
    if abs(c)>0.6: print('  ',C[a],C[b],round(float(c),2))
json.dump({'ids':C,'w':{k:[round(float(v),4) for v in w] for k,w in W.items()}},open('/tmp/pf/popt.json','w'))
