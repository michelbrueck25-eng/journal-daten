import sys,os,io,contextlib,pickle,numpy as np,json,datetime as dt
t=open('obsearch.py').read(); t=t[:t.index('rows=[]')]
with contextlib.redirect_stdout(io.StringIO()): exec(t)
rows=pickle.load(open('/tmp/pf/obrows.pkl','rb'))
def mon(tr):
    m={}
    for x in tr: m[x['date'][:7]]=m.get(x['date'][:7],0)+x['r']
    return m
F=json.load(open('../forwardtest.json')); S={x['id']:x for x in F['strategien']}
def kmon(i):
    m={}
    for a in S[i]['backtest']['monate']: k=(dt.date(1970,1,1)+dt.timedelta(days=a[0])).strftime('%Y-%m'); m[k]=m.get(k,0)+a[2]
    return m
K={i:kmon(i) for i in ('fw3-k1','fw3-k2','fw3-k3')}
top=[r for r in rows if r[0]>=0.25][:60]
M=[mon(run(*r[1])) for r in top]
ks=sorted(set().union(*M,*K.values())); V=lambda m:np.array([m.get(k,0) for k in ks])
kref=sum(V(m) for m in K.values())
sel=[]
for i,r in enumerate(top):
    v=V(M[i]); 
    if all(abs(np.corrcoef(v,V(M[j]))[0,1])<0.8 for j in sel): sel.append(i)
    if len(sel)==6: break
print(len(top),'Kandidaten mit min(Entw,Pruef)>=0,25; Auswahl mit Korrelation <0,8 untereinander:')
for i in sel:
    r=top[i]; v=V(M[i]); print(f'{r[0]:+.3f}',r[1],'n%d E%+.3f'%r[2][:2],'Korr zu k1-3 %.2f'%np.corrcoef(v,kref)[0,1],' | Korr zu Auswahl',[round(float(np.corrcoef(v,V(M[j]))[0,1]),2) for j in sel if j!=i])
print('Korrelation k1..k3 untereinander zum Vergleich: 0,78 / 0,40 / 0,28')
pickle.dump([top[i] for i in sel],open('/tmp/pf/obsel.pkl','wb'))
