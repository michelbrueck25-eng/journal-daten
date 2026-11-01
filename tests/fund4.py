import warnings;warnings.filterwarnings('ignore')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from fund3 import *
rng=random.Random(7)
days=[dt.date(2026,1,5)+dt.timedelta(days=7*i) for i in range(40)]
def F(lb,hold,rand):
    tr=[]
    for d in days:
        sc={c:sum(e['s'] for e in E if e['c']==c and d-dt.timedelta(days=lb)<=e['d']<d) for c in CCY}
        r=sorted(sc.items(),key=lambda z:z[1])
        if r[-1][1]==r[0][1]:continue
        a,b=(r[-1][0],r[0][0]) if not rand else rng.sample(CCY,2)
        p=pair(a,b)
        if p:
            t=trade(p[0],p[1],d,hold)
            if t:tr.append(t['r'])
    return tr
for lb,h in[(28,5),(28,10),(28,20)]:
    o=np.mean(F(lb,h,False));base=[np.mean(F(lb,h,True)) for _ in range(300)]
    print(lb,h,'E_beob',round(o,2),'Zufall Ø',round(np.mean(base),3),'95%-Perz',round(np.percentile(base,95),2),'p=',round(np.mean([b>=o for b in base]),3))
# Ueberlappungsfrei: nur jede 4. Woche
tr=[]
for k,d in enumerate(days):
    if k%2:continue
    sc={c:sum(e['s'] for e in E if e['c']==c and d-dt.timedelta(days=28)<=e['d']<d) for c in CCY}
    r=sorted(sc.items(),key=lambda z:z[1])
    if r[-1][1]==r[0][1]:continue
    p=pair(r[-1][0],r[0][0])
    if p:
        t=trade(p[0],p[1],d,10)
        if t:tr.append(t)
summ(tr,'F lb28 hold10 überlappungsfrei (jede 2. Woche)')
h=len([1 for e in E if e['d']<dt.date(2026,6,1)])
E1=[e for e in E if e['d']<dt.date(2026,6,1)]
