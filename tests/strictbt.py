"""(Kopf aus dob.py) Daily-Orderblock-Test: Zonen aus Tageskerzen (Regeln wie ob_check.find_obs, ohne Berührungszähler), Varianten A/B/C, alle Instrumente in marktdaten/.
Aufruf: python3 dob.py  -> schreibt Test 'lab-dailyob' in strategietests.json (privat) und die Bilder."""
import sys,json,datetime,collections,os
sys.path.insert(0,"/home/claude/journal-daten/tests")
import eng
from eng import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
PIPS={'GOLD':0.1,'SILBER':0.01,'PLATIN':1.0,'KUPFER':0.002,'OEL':0.03,'ERDGAS':0.003}
eng.pip=lambda s: PIPS.get(s,0.01 if s.endswith('JPY') else 0.0001)
U=load_all(); A={s:atr(U[s]) for s in U}
def load4(sym):
    f=f'{HOME}/marktdaten/{sym}_4H.json'
    if not os.path.exists(f): return None
    r=np.array(json.load(open(f))['rows'],float)
    return dict(t=r[:,0],o=r[:,1],h=r[:,2],l=r[:,3],c=r[:,4])
U4={s:load4(s) for s in U}
SPLIT=datetime.datetime(2024,10,29).timestamp()*1000

import datetime as dt
SPL='2023-01-01'
def imp(sym,x,L):
    d=U[sym]; r=d['h'][x]-d['l'][x]
    if r<=0 or np.isnan(A[sym][x-1]): return False
    b=(d['c'][x]-d['o'][x]) if L else (d['o'][x]-d['c'][x])
    return b>=0.7*r and abs(d['c'][x]-d['o'][x])>=0.9*A[sym][x-1]
def strict(sym,maxb=6,minz=0.3):
    """Lag-In (impulsiv, beide Richtungen) / Basis (<=maxb kleine Kerzen) / Lag-Out (Koerper>=70 %, >=1,1 ATR, schliesst jenseits der Basis + Strukturbruch)."""
    d=U[sym]; n=len(d['c']); out=[]
    for j in range(20,n-2):
        a=A[sym][j-1]
        if np.isnan(a): continue
        for L in (True,False):
            if not imp(sym,j,L) or abs(d['c'][j]-d['o'][j])<1.1*a: continue
            b=[]; k=j-1
            while k>=j-maxb-1 and abs(d['c'][k]-d['o'][k])<0.6*a and (d['h'][k]-d['l'][k])<1.3*a: b.append(k); k-=1
            if not b or len(b)>maxb: continue
            li=b[-1]-1
            if not (imp(sym,li,True) or imp(sym,li,False)): continue
            b=b[::-1]; hi=d['h'][b].max(); lo=d['l'][b].min()
            bt=max(max(d['o'][x],d['c'][x]) for x in b); bb=min(min(d['o'][x],d['c'][x]) for x in b)
            c=d['c'][j]
            if (L and c<=hi) or ((not L) and c>=lo): continue
            ref=d['h'][b[0]-8:b[0]].max() if L else d['l'][b[0]-8:b[0]].min()
            if (L and c<=ref) or ((not L) and c>=ref): continue
            if hi-lo<minz*a or hi-lo>2.5*a: continue
            out.append(dict(sym=sym,L=L,j=j,hi=hi,lo=lo,bt=bt,bb=bb,a=a))
    return out
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
def entries(zs,mode,wait=20):
    """mode: 'ref_mid' (50 % verfeinerte Zone), 'ref_edge' (Rand der verfeinerten Zone), 'ext_mid' (50 % erweiterte Zone). Stop 0,1 ATR hinter dem Tief/Hoch der Basis."""
    out=[]
    for z in zs:
        s=z['sym']; d=U[s]; L=z['L']; lo,hi=z['lo'],z['hi']
        top=z['bt'] if L else hi; bot=lo if L else z['bb']          # verfeinerte Zone
        if mode=='ref_mid': en=(top+bot)/2
        elif mode=='ref_edge': en=top if L else bot
        else: en=(lo+hi)/2
        st=lo-0.1*z['a'] if L else hi+0.1*z['a']
        for q in range(z['j']+1,min(z['j']+1+wait,len(d['c'])-1)):
            if (d['c'][q]<lo) if L else (d['c'][q]>hi): break
            if (d['l'][q]<=en) if L else (d['h'][q]>=en):
                if (d['o'][q]<st) if L else (d['o'][q]>st): break
                out.append((s,q,L,en,st,dt.datetime.fromtimestamp(d['t'][q]/1000,dt.timezone.utc).strftime('%Y-%m-%d'))); break
    return out
VARS={'alles 2R':([(1,2)],False),'alles 3R':([(1,3)],False),'alles 4R':([(1,4)],False),'alles 6R':([(1,6)],False),
 '50 % 2R, Rest 6R, BE':([(.5,2),(.5,6)],True),'50 % 1R, Rest 3R, BE':([(.5,1),(.5,3)],True)}
if __name__=='__main__':
    ZS=[z for s in U if s not in PIPS for z in strict(s)]
    print('Zonen',len(ZS))
    for mode in ('ref_mid','ref_edge','ext_mid'):
        ent=entries(ZS,mode); ds=[e[5] for e in ent]; yrs=(dt.date.fromisoformat(max(ds))-dt.date.fromisoformat(min(ds))).days/365.25
        print(f'\n{mode}: n={len(ent)} ueber {yrs:.1f} J')
        for vn,(parts,be) in VARS.items():
            r=np.array([psim(U[s],q,L,en,st,parts,be,40,s) for s,q,L,en,st,dd in ent])
            a=np.array([x for x,e in zip(r,ent) if e[5]<SPL]); b=np.array([x for x,e in zip(r,ent) if e[5]>=SPL])
            print(f'  {vn:24s} E={r.mean():+.3f} R  wr={100*(r>0).mean():.0f}%  {r.sum()/yrs:+5.1f} R/Jahr  dev={a.mean():+.2f} test={b.mean():+.2f}')
