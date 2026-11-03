import warnings;warnings.filterwarnings('ignore')
import numpy as np,json,math
from model import S,HZ,FN
SETS={'A_Carry':[0],'B_Realzins':[2],'C_Infl+Arbeit':[1,3],'D_Zinsdynamik':[0,4,7],'E_AllMakro':list(range(8)),'F_Makro+Mom':list(range(8))+[8,9,10],'G_Nur_Momentum':[8,10,9],'H_Real+Dyn+Mom':[2,5,6,8]}
def X(d): return np.concatenate([d['x'],d['mom']])
XA=np.array([X(d) for d in S]);T=np.array([d['t'] for d in S]);SD=np.array([d['sd'] for d in S]);PX=np.array([d['px'] for d in S]);PV=np.array([d['pv'] for d in S])
months=sorted({d['m'] for d in S});MI=np.array([months.index(d['m']) for d in S])
def run(h,cols,alpha=50.0,start='2018-01'):
    y=np.array([d['fut'][h]/(d['sd']*math.sqrt(h)) if d['fut'][h] is not None else np.nan for d in S])
    out=[]; 
    for m in months:
        if m<start: continue
        idx=np.where(MI==np.array(months.index(m)))[0]
        if not len(idx): continue
        td=T[idx[0]]
        tr=np.where((T+h*86400000*1.5<=td)&~np.isnan(y))[0]
        if len(tr)<300: continue
        A=XA[tr][:,cols];mu=A.mean(0);sg=A.std(0)+1e-9;A=(A-mu)/sg
        w=np.linalg.solve(A.T@A+alpha*np.eye(len(cols)),A.T@(y[tr]-y[tr].mean()));b=y[tr].mean()
        p=((XA[idx][:,cols]-mu)/sg)@w+b
        for ii,pp in zip(idx,p): out.append((ii,pp,y[ii]))
    return out
def stats(out):
    o=[(i,p,yy) for i,p,yy in out if not np.isnan(yy)]
    if len(o)<5: return None
    P=np.array([x[1] for x in o]);Y=np.array([x[2] for x in o]);I=[x[0] for x in o]
    cost=np.array([1.0*PV[i]/(SD[i]*PX[i]) for i in I])  # 1 Pip in Einheiten sd*sqrt(h): grob, h-Skalierung unten
    return P,Y,I
RES={}
for nm,cols in SETS.items():
    for h in HZ:
        out=run(h,cols)
        o=[(i,p,y) for i,p,y in out if not np.isnan(y)]
        RES[(nm,h)]=o
def report(sel,cut='2023-01'):
    rows=[]
    for (nm,h),o in RES.items():
        for part in ('dev','test'):
            oo=[(i,p,y) for i,p,y in o if (S[i]['m']<cut)==(part=='dev')]
            if not oo: continue
            P=np.array([x[1] for x in oo]);Y=np.array([x[2] for x in oo]);I=[x[0] for x in oo]
            cost=np.array([PV[i]/(SD[i]*PX[i]*math.sqrt(h)) for i in I])
            R=np.sign(P)*Y-cost
            ic=np.corrcoef(P,Y)[0,1]
            rows.append(dict(modell=nm,h=h,teil=part,n=len(oo),netR=float(R.mean()),treffer=float((np.sign(P)==np.sign(Y)).mean()),ic=float(ic)))
    return rows
rows=report(None)
json.dump(rows,open('res.json','w'))
import collections
print('Test-Ergebnisse (>=2023), nach Netto-R:')
for r in sorted([r for r in rows if r['teil']=='test'],key=lambda r:-r['netR'])[:12]: print(r)
for nm in SETS:
    tt=[r for r in rows if r['modell']==nm and r['teil']=='test'];dd=[r for r in rows if r['modell']==nm and r['teil']=='dev']
    print(nm,'dev netR %.3f test netR %.3f'%(np.mean([r['netR'] for r in dd]),np.mean([r['netR'] for r in tt])))
