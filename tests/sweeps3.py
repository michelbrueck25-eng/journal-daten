import warnings;warnings.filterwarnings('ignore')
from sweeps import *
import random
random.seed(5)
def base(tf,tgt,maxb,cond):
    out=[]
    for s in SYMS:
        d=load(s,tf);A=atr(d);n=len(d['c']);D=[str(day(t)) for t in d['t']]
        for i in range(51,n-1):
            if np.isnan(A[i]):continue
            for L in(1,-1):
                c=cond(d,i,L)
                if not c:continue
                stop=d['l'][i] if L>0 else d['h'][i];entry=d['o'][i+1];risk=abs(entry-stop)
                if risk<0.3*A[i] or risk>3*A[i] or (stop-entry)*L>0:continue
                r=sim(d,i+1,L,entry,stop,tgt,maxb,s)
                if r:out.append(dict(s=s,d=D[i],L=L,r=r[0]))
    return out
for tf,mb in(('D',5),('4H',6)):
    for tg in(1,2):
        rep(base(tf,tg,mb,lambda d,i,L:True),f'BASIS {tf} jede Kerze, Stopp am Kerzenende, Ziel {tg}R (Zufallsvergleich)')
        # Umkehr-Sweep = Bedingung wie zuvor
        rep(base(tf,tg,mb,lambda d,i,L:(L<0 and d['h'][i]>d['h'][i-1] and d['c'][i]<d['h'][i-1]) or (L>0 and d['l'][i]<d['l'][i-1] and d['c'][i]>d['l'][i-1])),f'{tf} Sweep-Umkehr, Ziel {tg}R (gleiches Regelwerk)')
