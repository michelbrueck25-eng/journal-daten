import sys,datetime as dt,numpy as np
sys.path.insert(0,'/tmp/ix')
import lvl
M=lvl.M
def sim(m,A,i,L,stopm,H,tgtm=None):
    n=len(m['c']);e=m['o'][i+1];risk=stopm*A[i];st=e-L*risk;j=i+1;res=None
    tp=None if tgtm is None else e+L*tgtm*A[i]
    while j<n and j<=i+H:
        if (L>0 and m['l'][j]<=st) or (L<0 and m['h'][j]>=st):res=-1.0;break
        if tp is not None and ((L>0 and m['h'][j]>=tp) or (L<0 and m['l'][j]<=tp)):res=tgtm*A[i]/risk;break
        j+=1
    else:
        j=min(j,n-1);res=L*(m['c'][j]-e)/risk
    j=min(j,n-1);days=(m['D'][j]-m['D'][i+1]).days
    return m['D'][i+1],res-lvl.cost(m,A[i],risk,days),j
def scan(n,k,fade,H,stopm=2.5,tgtm=None,months=None,syms=None,trend=None):
    out=[]
    for s,m in M.items():
        if syms and s not in syms:continue
        A=lvl.atr(m);c=m['c'];N=len(c);i=260;busy=-1
        for i in range(260,N-H-2):
            if i<=busy or np.isnan(A[i]) or A[i]<=0:continue
            if months and m['D'][i].month not in months:continue
            z=(c[i]-c[i-n])/A[i]
            if abs(z)<k:continue
            L=(-1 if z>0 else 1)*(1 if fade else -1)
            if trend=='with200' and (L>0)!=(c[i]>np.mean(c[i-200:i])):continue
            if trend=='against200' and (L>0)==(c[i]>np.mean(c[i-200:i])):continue
            d,r,j=sim(m,A,i,L,stopm,H,tgtm);out.append((d,s,r));busy=j
    return out
st=lvl.st
if __name__=='__main__':
    FXS=[s for s,m in M.items() if m['fx']];NF=[s for s,m in M.items() if not m['fx']]
    for fade in (True,False):
      for n in (3,5,10):
        for k in (3,4,6):
          for H in (5,10):
            for grp,sy in (('FX',FXS),('NichtFX',NF)):
                x=st(scan(n,k,fade,H,syms=sy))
                if x and x[0]>=100:print(f'{"fade" if fade else "folgen":6} n{n:2} k{k} H{H:2} {grp:8} N{x[0]:5} E{x[1]:+.3f} dev{x[2]:+.3f} test{x[3]:+.3f} (n{x[4]})',flush=True)
