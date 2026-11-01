import sys;sys.path.insert(0,'/tmp/ix')
from idx import *
import numpy as np
P={s:prep(s) for s in SY}
def mk(name,sigf,exitf,stopm,maxd,syms=SY):
    tr=[]
    for s in syms:
        p=P[s]
        tr+=run(s,lambda i,d,o,h,l,c,A:sigf(p,i,d,o,h,l,c,A),lambda j,d,o,h,l,c,A,i0:exitf(p,j,d,o,h,l,c,A,i0),stopm,maxd=maxd)
    return tr
def hh(c,i,n):return c[i]>=max(c[i-n:i])
R={}
for sl in (True,):
  for thr in (5,10,20):
    for sm,md in ((3,10),(3,20)):
        R['rsi2<%d sma200 stop%d md%d'%(thr,sm,md)]=lambda syms=SY,thr=thr,sm=sm,md=md:mk('x',lambda p,i,d,o,h,l,c,A:c[i]>p['s200'][i] and p['r2'][i]<thr,lambda p,j,d,o,h,l,c,A,i0:c[j]>p['s5'][j],sm,md,syms)
for n in (55,100):
    for sm in (2,3):
        R['breakout%d sma200 stop%d exit20low'%(n,sm)]=lambda syms=SY,n=n,sm=sm:mk('x',lambda p,i,d,o,h,l,c,A:c[i]>p['s200'][i] and hh(c,i,n),lambda p,j,d,o,h,l,c,A,i0:c[j]<min(c[j-20:j]),sm,250,syms)
R['turn-of-month']=lambda syms=SY:mk('x',lambda p,i,d,o,h,l,c,A:d[i+1].month!=d[i].month and c[i]>p['s200'][i],lambda p,j,d,o,h,l,c,A,i0:d[j].day>=3 and d[j].month==d[i0].month%12+1 or (d[j]-d[i0]).days>6,3,10,syms)
R['3down sma200']=lambda syms=SY:mk('x',lambda p,i,d,o,h,l,c,A:c[i]>p['s200'][i] and c[i]<c[i-1]<c[i-2]<c[i-3],lambda p,j,d,o,h,l,c,A,i0:c[j]>c[j-1],3,5,syms)
IDX=['DAX','SPX','NDX','NKX','FTSE']
for k,f in R.items():
    for lab,sy in (('alle',SY),('Indizes',IDX)):
        s=stats(f(sy));
        if s:print('%-40s %-8s n%5d E%+.3f dev%+.3f test%+.3f (n%d)'%(k,lab,*s))
