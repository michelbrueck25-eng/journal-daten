import sys,json,random,datetime as dt,numpy as np,itertools
from eng import load_all,atr
from seas import cost_r
U=load_all(); SYMS=sorted(U)
P={}
for s in SYMS:
    d=U[s]; ts=np.array([dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).date() for t in d['t']])
    P[s]=dict(d=d,ts=ts,a=atr(d),ord=np.array([x.toordinal() for x in ts]),yr=np.array([x.year for x in ts]),
              md=np.array([(x.month,x.day) for x in ts]))
def sim_all(s,N,stopm,tpm,L):
    """r netto fuer Einstieg an Schluss jeder Bar i. Stopp stopm*ATR, TP tpm*stop (0=kein TP), Zeitausstieg N Bars"""
    d=P[s]['d']; a=P[s]['a']; c=d['c']; n=len(c); h=d['h']; l=d['l']
    sd=stopm*a; ok=~np.isnan(a); ok[n-N-1:]=False
    r=np.full(n,np.nan); done=np.zeros(n,bool); ex=np.zeros(n,int)
    idx=np.arange(n)
    for k in range(1,N+1):
        j=np.minimum(idx+k,n-1)
        if L: hit=(l[j]<=c-sd); tp=(h[j]>=c+tpm*sd) if tpm else np.zeros(n,bool)
        else: hit=(h[j]>=c+sd); tp=(l[j]<=c-tpm*sd) if tpm else np.zeros(n,bool)
        new=ok&~done&hit; r[new]=-1; ex[new]=j[new]; done|=new
        new=ok&~done&tp; r[new]=tpm; ex[new]=j[new]; done|=new
    j=np.minimum(idx+N,n-1); rest=ok&~done
    r[rest]=((c[j]-c) if L else (c-c[j]))[rest]/sd[rest]; ex[rest]=j[rest]
    cal=P[s]['ord'][ex]-P[s]['ord']
    if s=='GOLD': cost=(0.05*a+0.012*a*cal)/sd
    else:
        p=0.01 if s.endswith('JPY') else 0.0001; cost=(1.0+0.3*cal)*p/sd
    r=r-cost; r[~ok]=np.nan
    return r,ex
def run(N,stopm,tpm,thr,minyrs=6,mean_min=0.05,step=3,start_year=None,null=0,seed=0):
    rnd=random.Random(seed); trades=[]
    for s in SYMS:
        RL,EL=sim_all(s,N,stopm,tpm,True); RS,ES=sim_all(s,N,stopm,tpm,False)
        md=P[s]['md']; yr=P[s]['yr']; ts=P[s]['ts']; n=len(yr)
        # Zelle (m,dd) -> erste Bar >= Datum je Jahr
        cell={}
        for i in range(n):
            m,dd=md[i]
            if dd>28: continue
            key=(m,(dd-1)//step*step+1)
            if (dd-1)%step: continue   # nur Ankertage
            cell.setdefault(key,{})
            if yr[i] not in cell[key]: cell[key][yr[i]]=i
        years=sorted(set(yr)); busy=-1
        for y in years:
            if y<years[0]+minyrs or (start_year and y<start_year): continue
            sig=[]
            for key,byy in cell.items():
                past=[byy[yy] for yy in byy if yy<y]
                if len(past)<minyrs: continue
                for L,R in ((True,RL),(False,RS)):
                    rs=np.array([R[i] for i in past]); rs=rs[~np.isnan(rs)]
                    if len(rs)<minyrs: continue
                    wr=(rs>0).mean()
                    if wr>=thr and rs.mean()>=mean_min: sig.append((wr,rs.mean(),key,L))
            sig.sort(key=lambda x:(-x[0],-x[1]))
            for wr,mn,key,L in sig:
                if y not in cell[key]: continue
                i=cell[key][y]
                if null:
                    k=i+rnd.randint(40,250)
                    if k>=n-N-1: continue
                    i=k
                R,E=(RL,EL) if L else (RS,ES)
                if np.isnan(R[i]) or i<=busy: continue
                busy=E[i]; trades.append(dict(sym=s,date=str(ts[i]),dir='long' if L else 'short',r=float(R[i]),key=f'{key[0]:02d}-{key[1]:02d}',N=N))
    return trades
def summ(tr):
    if not tr: return None
    r=np.array([x['r'] for x in tr]); eq=np.cumsum(r); ys=max(1,len(set(x['date'][:4] for x in tr)))
    return dict(n=len(r),wr=round(float((r>0).mean()*100),1),avg=round(float(r.mean()),3),jahr=round(float(r.sum()/ys),2),dd=round(float((np.maximum.accumulate(eq)-eq).max()),1))
if __name__=='__main__':
    out=[]
    for N in (3,5,10,15,20,30):
      for stopm in (1.5,2.5):
        for tpm in (0,1.0,2.0):
          for thr in (0.75,0.85):
            tr=run(N,stopm,tpm,thr); 
            if len(tr)<40: continue
            nl=run(N,stopm,tpm,thr,null=1,seed=3)
            sm=summ(tr); sn=summ(nl); h1=summ([x for x in tr if x['date']<'2024-07-01']); h2=summ([x for x in tr if x['date']>='2024-07-01'])
            row=dict(N=N,stop=stopm,tp=tpm,thr=thr,all=sm,null=sn,h1=h1,h2=h2); out.append(row)
            print(N,stopm,tpm,thr,sm,'null',sn and sn['avg'],'h1',h1 and h1['avg'],'h2',h2 and h2['avg'],flush=True)
    json.dump(out,open('/tmp/seas2.json','w'))
