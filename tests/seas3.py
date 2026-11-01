import random,datetime as dt,numpy as np,json
from seas2 import P,SYMS
def pct_series(s,N,L):
    d=P[s]['d'];c=d['c'];n=len(c);idx=np.arange(n);j=np.minimum(idx+N,n-1)
    cal=P[s]['ord'][j]-P[s]['ord']
    pip=0.01 if s.endswith('JPY') else 0.0001
    gross=((c[j]-c)/c) if L else ((c-c[j])/c)
    cost=((0.05*P[s]['a']+0.012*P[s]['a']*cal)/c) if s=='GOLD' else ((1.0+0.3*cal)*pip/c)
    r=gross-cost; r[n-N-1:]=np.nan; return r*100,j   # Prozent Kursbewegung netto
def run(N,thr,mean_min,minyrs=6,step=3,null=0,seed=0):
    rnd=random.Random(seed);tr=[]
    for s in SYMS:
        RL,E=pct_series(s,N,True);RS,_=pct_series(s,N,False)
        md=P[s]['md'];yr=P[s]['yr'];ts=P[s]['ts'];n=len(yr);cell={}
        for i in range(n):
            m,dd=md[i]
            if dd>28 or (dd-1)%step: continue
            cell.setdefault((m,dd),{}).setdefault(yr[i],i)
        years=sorted(set(yr));busy=-1
        for y in years:
            if y<years[0]+minyrs: continue
            sig=[]
            for key,byy in cell.items():
                past=[byy[q] for q in byy if q<y]
                if len(past)<minyrs: continue
                for L,R in ((True,RL),(False,RS)):
                    rs=np.array([R[i] for i in past]);rs=rs[~np.isnan(rs)]
                    if len(rs)<minyrs: continue
                    wr=(rs>0).mean(); lo=rs[rs<=0]
                    if wr>=thr and rs.mean()>=mean_min and len(lo): sig.append((wr,rs.mean(),abs(lo.mean()),key,L))
            sig.sort(key=lambda x:(-x[0],-x[1]))
            for wr,mn,al,key,L in sig:
                if y not in cell[key]: continue
                i=cell[key][y]
                if null:
                    k=i+rnd.randint(40,250)
                    if k>=n-N-1: continue
                    i=k
                R=RL if L else RS
                if np.isnan(R[i]) or i<=busy: continue
                busy=E[i]; tr.append(dict(sym=s,date=str(ts[i]),dir='long' if L else 'short',pct=float(R[i]),rr=float(R[i]/max(al,0.05)),exp=float(mn),key=key))
    return tr
def summ(tr):
    if not tr: return None
    p=np.array([x['pct'] for x in tr]);r=np.array([x['rr'] for x in tr]);eq=np.cumsum(r);ys=max(1,len(set(x['date'][:4] for x in tr)))
    return dict(n=len(p),wr=round(float((p>0).mean()*100),1),pct=round(float(p.mean()),3),R=round(float(r.mean()),3),Rjahr=round(float(r.sum()/ys),2),dd=round(float((np.maximum.accumulate(eq)-eq).max()),1),worst=round(float(p.min()),2))
if __name__=='__main__':
    for N in (10,20,30):
      for thr in (0.7,0.8):
        for mm in (0.3,0.6):
            tr=run(N,thr,mm)
            if len(tr)<30: print(N,thr,mm,'zu wenige',len(tr));continue
            nl=run(N,thr,mm,null=1,seed=5); h=[x for x in tr if x['date']<'2024-07-01'];h2=[x for x in tr if x['date']>='2024-07-01']
            print(N,thr,mm,summ(tr),'| null',(summ(nl) or {}).get('pct'),'| H1',(summ(h) or {}).get('pct'),'H2',(summ(h2) or {}).get('pct'),flush=True)
