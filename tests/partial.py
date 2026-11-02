"""Teilprofite/BE-Varianten fuer Weekly-OB (Mitte) und Daily-OB (Qualitaet A, Mitte)."""
import bisect,numpy as np,datetime as dt,sys
exec(open('/tmp/dobz.py').read())
import wob
SPL='2023-01-01'
def psim(d,i0,L,en,stop,parts,be,md,sym):
    risk=abs(en-stop); sp=eng.SPREAD_PIPS*eng.pip(sym)/risk
    if (d['l'][i0]<=stop) if L else (d['h'][i0]>=stop): return -1-sp
    tg=[(sh,en+r*risk if L else en-r*risk) for sh,r in parts]; done=[False]*len(parts); cur=stop; real=0.0; rest=1.0; n=len(d['c'])
    end=min(i0+1+md,n)
    for j in range(i0+1,end):
        if (d['l'][j]<=cur) if L else (d['h'][j]>=cur):
            real+=rest*((cur-en)/risk if L else (en-cur)/risk); return real-sp
        for k,(sh,px) in enumerate(tg):
            if not done[k] and ((d['h'][j]>=px) if L else (d['l'][j]<=px)):
                done[k]=True; real+=sh*parts[k][1]; rest-=sh
                if be and k==0: cur=en
        if rest<=1e-9: return real-sp
    c=d['c'][end-1]; real+=rest*((c-en)/risk if L else (en-c)/risk); return real-sp
VARS={'alles 1R':([(1,1)],False),'alles 2R':([(1,2)],False),'alles 3R':([(1,3)],False),
 '50 % 1R, Rest 2R, danach BE':([(.5,1),(.5,2)],True),'50 % 1R, Rest 3R, danach BE':([(.5,1),(.5,3)],True),
 '50 % 1R, Rest 3R, ohne BE':([(.5,1),(.5,3)],False),'50 % 1R, Rest 5R, danach BE':([(.5,1),(.5,5)],True),
 '33 % 1R, 33 % 2R, 33 % 4R, BE':([(1/3,1),(1/3,2),(1/3,4)],True),'50 % 2R, Rest 6R, BE':([(.5,2),(.5,6)],True)}
# ---- Einstiege Weekly (Mitte)
def wentries(weeks=40):
    out=[]
    for z in wob.zones():
        s=z['sym']; d=wob.U[s]; W=z['W']; L=z['L']; t=d['t']; lo,hi=z['lo'],z['hi']; mid=(lo+hi)/2; found=False
        for k in range(z['i']+4,min(len(W),z['i']+4+weeks)):
            a_i=bisect.bisect_left(t,W[k][0]); b_i=bisect.bisect_left(t,W[k][0]+7*86400e3)
            for q in range(max(a_i,1),b_i):
                if (d['c'][q]<lo) if L else (d['c'][q]>hi): found=True; break
                if (d['l'][q]<=mid) if L else (d['h'][q]>=mid):
                    if (d['o'][q]<lo) if L else (d['o'][q]>hi): found=True; break
                    a=wob.A[s][q-1]
                    if not np.isnan(a): out.append((s,q,L,mid,lo-0.1*a if L else hi+0.1*a,wob.D(t[q])))
                    found=True; break
            if found: break
    return out
def dentries():
    out=[]
    for z in Z:
        if z['q']!='A' or z['sym'] in PIPS or np.isnan(z['a']): continue
        d=U[z['sym']]; L=z['L']; lo,hi=z['lo'],z['hi']; mid=(lo+hi)/2; kk=None
        for q in range(z['t0'],min(z['t0']+6,len(d['c'])-1)):
            if (d['c'][q]<lo) if L else (d['c'][q]>hi): break
            if (d['l'][q]<=mid) if L else (d['h'][q]>=mid): kk=q; break
        if kk is None: continue
        a=z['a']; out.append((z['sym'],kk,L,mid,lo-0.1*a if L else hi+0.1*a,dt.datetime.utcfromtimestamp(d['t'][kk]/1000).strftime('%Y-%m-%d')))
    return out
for nm,ent in (('Weekly-OB, Einstieg Mitte, alle Qualitäten',wentries()),('Daily-OB, Qualität A, Einstieg Mitte (FX)',dentries())):
    print('\n'+nm,len(ent))
    for md in (20,40):
        for vn,(parts,be) in VARS.items():
            r=np.array([psim(U[s],q,L,en,st,parts,be,md,s) for s,q,L,en,st,dd in ent]); ds=[e[5] for e in ent]
            a=np.array([x for x,e in zip(r,ent) if e[5]<SPL]); b=np.array([x for x,e in zip(r,ent) if e[5]>=SPL])
            yrs=(dt.date.fromisoformat(max(ds))-dt.date.fromisoformat(min(ds))).days/365.25
            print(f'md{md} {vn:34s} E={r.mean():+.3f} wr={100*(r>0).mean():.0f}% R/J={r.sum()/yrs:+5.1f} dev={a.mean():+.2f} test={b.mean():+.2f}')
