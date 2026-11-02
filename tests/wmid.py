"""Weekly-OB: Einstieg bei 50 % der Zone (Limit), Stop hinter der Zone, Ziele 1-8 R, Haltedauer 10-60 Tage."""
import bisect,numpy as np,datetime as dt
import wob
from wob import U,A,D,simulate,OC
SPL='2023-01-01'
Z=wob.zones()
def run(entry,tg,md,stopb=0.1,weeks=40):
    out=[]
    for z in Z:
        s=z['sym']; d=U[s]; W=z['W']; L=z['L']; t=d['t']; lo,hi=z['lo'],z['hi']
        mid=(lo+hi)/2; found=False
        for k in range(z['i']+4,min(len(W),z['i']+4+weeks)):
            t0=W[k][0]; t1=t0+7*86400e3
            a_i=bisect.bisect_left(t,t0); b_i=bisect.bisect_left(t,t1)
            for q in range(max(a_i,1),b_i):
                if (d['c'][q]<lo) if L else (d['c'][q]>hi): found=True; break
                px=mid if entry=='mid' else (hi if L else lo)
                touched=(d['l'][q]<=px) if L else (d['h'][q]>=px)
                if touched:
                    if entry=='mid' and ((d['o'][q]<lo) if L else (d['o'][q]>hi)): found=True; break
                    a=A[s][q-1]
                    if np.isnan(a): found=True; break
                    stop=lo-stopb*a if L else hi+stopb*a
                    r=simulate(d,q,L,px,stop,tg,md,s)
                    if r: out.append((r[0],D(t[q]),s,L))
                    found=True; break
            if found: break
    return out
if __name__=='__main__':
    for entry in ('edge','mid'):
        for md in (20,40,60):
            for tg in (1,2,3,4,5,6,8):
                tr=run(entry,tg,md)
                if len(tr)<40: continue
                r=np.array([x[0] for x in tr]); ds=[x[1] for x in tr]
                a=np.array([x[0] for x in tr if x[1]<SPL]); b=np.array([x[0] for x in tr if x[1]>=SPL])
                yrs=(dt.date.fromisoformat(max(ds))-dt.date.fromisoformat(min(ds))).days/365.25
                f=lambda v:'–' if len(v)<10 else f'{v.mean():+.2f}'
                print(f'{entry:4s} md{md:3d} {tg}R n={len(r):4d} E={r.mean():+.3f} wr={100*(r>0).mean():.0f}% R/J={r.sum()/yrs:+5.1f} dev={f(a)}({len(a)}) test={f(b)}({len(b)})',flush=True)
