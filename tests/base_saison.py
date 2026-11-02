"""Zonen aus Base (1-3 kleine Kerzen) + Leg-out, nach Muster RBR/DBR/RBD/DBD; Kombination mit Saison (5/10/15 Jahre) und COT."""
import sys,json,bisect,datetime as dt
exec(open('/tmp/dobz.py').read())
import wob
SPL=dt.datetime(2023,1,1).timestamp()*1000
def bzones(sym):
    d=U[sym]; n=len(d['c']); out=[]; ok=[False]*n
    rng=d['h']-d['l']
    for i in range(20,n-4):
        a=A[sym][i]
        if np.isnan(a): continue
        # Basis = maximaler Lauf kleiner Kerzen (Spanne <=0.8 ATR) die bei i endet
        nb=0
        while nb<5 and i-nb>=1 and rng[i-nb]<=0.8*A[sym][i-nb]: nb+=1
        if nb<1 or nb>3: continue
        if i-nb>=1 and rng[i-nb]<=0.8*A[sym][i-nb]: continue
        s=i-nb+1; lo=d['l'][s:i+1].min(); hi=d['h'][s:i+1].max()
        if hi-lo>1.5*a: continue
        for L in (True,False):
            if L: lo_ok=(d['c'][i+1:i+4]>hi).any() and (d['h'][i+1:i+4].max()-hi)>=1.0*a
            else: lo_ok=(d['c'][i+1:i+4]<lo).any() and (lo-d['l'][i+1:i+4].min())>=1.0*a
            if not lo_ok: continue
            m=(d['c'][s-1]-d['c'][max(s-4,0)])/a
            if abs(m)<0.5: continue
            up=m>0
            typ=('RBR' if up else 'DBR') if L else ('RBD' if up else 'DBD')
            t0=None
            for k in range(i+4,min(n,i+64)):
                if (d['c'][k]<lo) if L else (d['c'][k]>hi): break
                if d['l'][k]<=hi and d['h'][k]>=lo: t0=k;break
            if t0 is None: continue
            if (d['o'][t0]<lo) if L else (d['o'][t0]>hi): continue
            a0=A[sym][t0-1]
            if np.isnan(a0): continue
            out.append(dict(sym=sym,L=L,lo=lo,hi=hi,i=i,nb=nb,typ=typ,t0=t0,a=a0,ts=d['t'][t0]))
    return out
BZ=[z for s in U for z in bzones(s)]
print('Zonen',len(BZ))
def sim(zs,tg):
    out=[]
    for z in zs:
        d=U[z['sym']]; L=z['L']; a=z['a']
        entry=z['hi'] if L else z['lo']; stop=z['lo']-0.1*a if L else z['hi']+0.1*a
        if abs(entry-stop)>3*a: continue
        r=simulate(d,z['t0'],L,entry,stop,tg,10,z['sym'])
        if r: out.append((r[0],z['ts']))
    return out
def rep(name,zs):
    res={}
    for tg in (1.5,2.0):
        t=sim(zs,tg)
        if len(t)<10: print(f'{name:46s} {tg}R n={len(t)}'); continue
        v=np.array([x[0] for x in t]); ts=np.array([x[1] for x in t]); yrs=max((ts.max()-ts.min())/86400e3/365.25,.5)
        a=v[ts<SPL]; b=v[ts>=SPL]; f=lambda x:'–' if len(x)<10 else f'{x.mean():+.2f}'
        print(f'{name:46s} {tg}R n={len(v):5d} E={v.mean():+.3f} R/J={v.sum()/yrs:+5.1f} dev={f(a)}({len(a)}) test={f(b)}({len(b)})')
def seas(z,H=20):
    d=U[z['sym']]; t=d['t']; k=z['t0']; r=[]
    for y in range(1,16):
        tt=z['ts']-y*365.25*86400e3; j=bisect.bisect_left(t,tt)
        if j<=0 or j+H>=k or t[j]-tt>4*86400e3: break
        r.append(d['c'][j+H]/d['c'][j]-1)
    if len(r)<5: return None
    return [np.sign(np.mean(r[:K])) for K in (5,10,15)]
def sok(z,need=2):
    s=seas(z)
    if s is None: return None
    want=1 if z['L'] else -1
    return sum(1 for x in s if x==want)>=need
def cok(z):
    s=z['sym']
    if len(s)!=6: return None
    date=wob.D(z['ts']); cb,cq=wob.cidx(s[:3],date),wob.cidx(s[3:],date)
    if cb is None or cq is None: return None
    return ((cb-cq) if z['L'] else (cq-cb))>=30
rep('alle Base-Zonen',BZ)
for nb in (1,2,3): rep(f'Base {nb} Kerze(n)',[z for z in BZ if z['nb']==nb])
for ty in ('DBR','RBD','RBR','DBD'): rep(f'Muster {ty}',[z for z in BZ if z['typ']==ty])
rep('Umkehr (DBR+RBD)',[z for z in BZ if z['typ'] in('DBR','RBD')])
rep('Fortsetzung (RBR+DBD)',[z for z in BZ if z['typ'] in('RBR','DBD')])
rep('Umkehr, Base 1-2',[z for z in BZ if z['typ'] in('DBR','RBD') and z['nb']<=2])
print('--- Saison (>=2 von 3 Kurven 5/10/15J, 20 Tage)')
S=[z for z in BZ if sok(z) is not None]
rep('Referenz: alle mit Saisondaten',S)
rep('Saison bestätigt',[z for z in S if sok(z)])
rep('Saison dagegen',[z for z in S if not sok(z)])
rep('Saison bestätigt, 3 von 3',[z for z in S if sok(z,3)])
rep('Umkehr + Saison bestätigt',[z for z in S if z['typ'] in('DBR','RBD') and sok(z)])
rep('Fortsetzung + Saison bestätigt',[z for z in S if z['typ'] in('RBR','DBD') and sok(z)])
print('--- COT stark')
C=[z for z in BZ if cok(z) is not None]
rep('COT stark',[z for z in C if cok(z)])
rep('Umkehr + COT stark',[z for z in C if z['typ'] in('DBR','RBD') and cok(z)])
rep('Saison + COT stark',[z for z in S if sok(z) and cok(z)])
rep('Umkehr + Saison + COT stark',[z for z in S if z['typ'] in('DBR','RBD') and sok(z) and cok(z)])
