"""Daily-OB in Weekly-OB, Level-on-Level, COT-, Oszillator- und Saison-Bestaetigung (Variante A: Limit an der Zonenkante)."""
import sys,json,bisect,datetime as dt
exec(open('/tmp/dobzraw.py').read())
ZRAW=Z; Z=[z for z in ZRAW if z['t0'] is not None]
import pandas as pd
import wob
SPL=dt.datetime(2023,1,1).timestamp()*1000
TG=(1.5,2.0); MD=10
# ---- Wochenzonen (aus wob) mit Lebensdauer
WZ=[]
for z in wob.zones():
    W=z['W']; i=z['i']
    if i+4>=len(W): continue
    t_start=W[i+4][0]; t_end=t_start+40*7*86400e3
    for k in range(i+4,min(len(W),i+44)):
        if (W[k][4]<z['lo']) if z['L'] else (W[k][4]>z['hi']): t_end=W[k][0]+7*86400e3; break
    WZ.append(dict(sym=z['sym'],L=z['L'],lo=z['lo'],hi=z['hi'],t0=t_start,t1=t_end))
WBY={}
for w in WZ: WBY.setdefault((w['sym'],w['L']),[]).append(w)
# ---- Tageszonen: nur mit gueltiger Beruehrung wie runA
D=[]
for z in Z:
    d=U[z['sym']]; L=z['L']; k=z['t0']
    if np.isnan(z['a']): continue
    if (d['o'][k]<z['lo']) if L else (d['o'][k]>z['hi']): continue
    D.append(z)
for z in D: z['ts']=U[z['sym']]['t'][z['t0']]
def inwz(z,mode):
    for w in WBY.get((z['sym'],z['L']),[]):
        if w['t0']<=z['ts']<w['t1']:
            if mode=='innen' and z['lo']>=w['lo']-1e-12 and z['hi']<=w['hi']+1e-12: return True
            if mode=='ueberlapp' and z['lo']<=w['hi'] and z['hi']>=w['lo']: return True
    return False
# ---- Level on Level (ohne Zukunftswissen): Paar entsteht, wenn ein neuer Level ueber/unter einem noch lebenden, unberuehrten Level gleicher Richtung entsteht und der Raum dazwischen < Zonenhoehe ist
BYS={}
for z in ZRAW: BYS.setdefault((z['sym'],z['L']),[]).append(z)
for z in ZRAW: z['inner']=False; z['outer']=False
for (s,L),zs in BYS.items():
    for I in zs:
        for O in zs:
            if O is I or O['i']>=I['i']: continue           # O frueher entstanden
            tI=I['i']+4
            if O['i']+4>tI or O['e']<=tI or (O['t0'] is not None and O['t0']<=tI): continue   # O muss zu dem Zeitpunkt leben und unberuehrt sein
            h=I['hi']-I['lo']
            gap=(I['lo']-O['hi']) if L else (O['lo']-I['hi'])
            if -h<=gap<max(h,0.5*I['a']): I['inner']=True; O['outer']=True
for z in D: z['stk']=z['inner']
# ---- COT
def cotok(z,mode):
    s=z['sym']
    if len(s)!=6: return None
    date=wob.D(z['ts']); cb,cq=wob.cidx(s[:3],date),wob.cidx(s[3:],date)
    if cb is None or cq is None: return None
    L=z['L']; df=(cb-cq) if L else (cq-cb)
    return {'stark':df>=30,'extrem':(cb>75 and cq<25) if L else (cb<25 and cq>75)}[mode]
# ---- Waehrungs-Vergleichs-Oszillator (eigener Nachbau)
FXS=[s for s in U if len(s)==6 and s!='GOLD' and not s.startswith('XAU')]
cl=pd.DataFrame({s:pd.Series(U[s]['c'],index=pd.to_datetime(U[s]['t'],unit='ms').normalize()) for s in FXS})
cl=cl[~cl.index.duplicated()]
ret=np.log(cl).diff(20)
CC=['AUD','CAD','CHF','EUR','GBP','JPY','NZD','USD']
strn=pd.DataFrame(index=ret.index,columns=CC,dtype=float)
for c in CC:
    cols=[]
    for s in FXS:
        if s[:3]==c: cols.append(ret[s])
        elif s[3:]==c: cols.append(-ret[s])
    strn[c]=pd.concat(cols,axis=1).mean(axis=1)
def osc_pct(s):
    o=strn[s[:3]]-strn[s[3:]]
    return o.rolling(250,min_periods=120).apply(lambda x:(x[:-1]<x[-1]).mean(),raw=True)
OSC={s:osc_pct(s) for s in FXS}
def oscv(z):
    s=z['sym']
    if s not in OSC: return None
    ix=OSC[s].index.searchsorted(pd.Timestamp(z['ts'],unit='ms').normalize())-1   # Stand vom Vortag
    if ix<0: return None
    v=OSC[s].iloc[ix]; return None if np.isnan(v) else v
# ---- Saison (nur Vorjahre)
def seas(z,H=10):
    d=U[z['sym']]; t=d['t']; k=z['t0']; fr=[]
    for y in range(1,12):
        tt=z['ts']-y*365.25*86400e3; j=bisect.bisect_left(t,tt)
        if j<=0 or j+H>=k or t[j]-tt>4*86400e3: continue
        fr.append(1 if d['c'][j+H]>d['c'][j] else 0)
    if len(fr)<5: return None
    return np.mean(fr)
# ---- Simulation
def trades(zs,tg):
    out=[]
    for z in zs:
        d=U[z['sym']]; L=z['L']; k=z['t0']; a=z['a']
        entry=z['hi'] if L else z['lo']; stop=z['lo']-0.1*a if L else z['hi']+0.1*a
        r=simulate(d,k,L,entry,stop,tg,MD,z['sym'])
        if r: out.append((r[0],z['ts']))
    return out
def rep(name,zs,res):
    row=dict(name=name,n=len(zs))
    for tg in TG:
        t=trades(zs,tg)
        if not t: row[str(tg)]=None; continue
        v=np.array([x[0] for x in t]); ts=np.array([x[1] for x in t])
        yrs=max((ts.max()-ts.min())/86400e3/365.25,0.5)
        a=v[ts<SPL]; b=v[ts>=SPL]
        row[str(tg)]=dict(n=len(v),E=float(v.mean()),rj=float(v.sum()/yrs),dev=float(a.mean()) if len(a)>=10 else None,test=float(b.mean()) if len(b)>=10 else None,nd=len(a),nt=len(b))
    res.append(row)
    f=lambda x:'–' if x is None else f'{x:+.2f}'
    for tg in TG:
        r=row[str(tg)]
        if r: print(f"{name:52s} {tg}R n={r['n']:5d} E={r['E']:+.3f} R/J={r['rj']:+5.1f} dev={f(r['dev'])}({r['nd']}) test={f(r['test'])}({r['nt']})")
res=[]
base=D
rep('Daily-OB (Basis)',base,res)
rep('Daily-OB in Weekly-OB (vollst. innen)',[z for z in D if inwz(z,'innen')],res)
rep('Daily-OB mit Überlappung zu Weekly-OB',[z for z in D if inwz(z,'ueberlapp')],res)
rep('Daily-OB ausserhalb jeder Weekly-OB',[z for z in D if not inwz(z,'ueberlapp')],res)
wt=wob.run(1.5,MD,'ohne'); w2=wob.run(2.0,MD,'ohne')
for nm,t in (('Weekly-OB allein 1.5',wt),('Weekly-OB allein 2.0',w2)):
    v=np.array([x['r'] for x in t]); print(nm,len(v),round(v.mean(),3))
res.append(dict(name='Weekly-OB allein',w15=float(np.mean([x['r'] for x in wt])),w20=float(np.mean([x['r'] for x in w2])),n=len(wt)))
S=[z for z in D if z['stk']]; N=[z for z in D if not z['stk']]
rep('Level-on-Level: innerer Level (hat Level dahinter)',S,res)
rep('Level-on-Level: Zone ohne Stapel',N,res)
# aeusserer Level handelt statt des inneren: dessen eigene Beruehrung
outer_ok=[o for o in D if o['outer'] and not np.isnan(o['a']) and ((U[o['sym']]['o'][o['t0']]>=o['lo']) if o['L'] else (U[o['sym']]['o'][o['t0']]<=o['hi']))]
for o in outer_ok: o['ts']=U[o['sym']]['t'][o['t0']]
rep('Level-on-Level: äusserer Level (hat inneren darüber)',outer_ok,res)
rep('Level-on-Level: Regel (innere weglassen, äussere handeln)',[z for z in D if not z['inner']],res)
rep('Weekly-Innen + kein Stapel',[z for z in D if inwz(z,'innen') and not z['stk']],res)
for nm,pred in (('COT stark',lambda z:cotok(z,'stark')),('COT extrem',lambda z:cotok(z,'extrem'))):
    rep('Daily-OB + '+nm,[z for z in D if pred(z)],res)
    rep('Daily-OB in Weekly-OB + '+nm,[z for z in D if inwz(z,'innen') and pred(z)],res)
rep('Osz: Pullback (Long unteres, Short oberes Quartil)',[z for z in D if (v:=oscv(z)) is not None and ((v<=0.25) if z['L'] else (v>=0.75))],res)
rep('Osz: Trend (Long oberes, Short unteres Quartil)',[z for z in D if (v:=oscv(z)) is not None and ((v>=0.75) if z['L'] else (v<=0.25))],res)
rep('Osz Pullback + Weekly-Innen',[z for z in D if inwz(z,'innen') and (v:=oscv(z)) is not None and ((v<=0.25) if z['L'] else (v>=0.75))],res)
for th in (0.6,0.7):
    rep(f'Saison dafür (≥{int(th*100)} % der Vorjahre)',[z for z in D if (v:=seas(z)) is not None and ((v>=th) if z['L'] else (v<=1-th))],res)
    rep(f'Saison dagegen (≥{int(th*100)} % der Vorjahre)',[z for z in D if (v:=seas(z)) is not None and ((v<=1-th) if z['L'] else (v>=th))],res)
rep('Saison dafür 60 % + Weekly-Innen',[z for z in D if inwz(z,'innen') and (v:=seas(z)) is not None and ((v>=.6) if z['L'] else (v<=.4))],res)
rep('Saison dafür 60 % + COT stark',[z for z in D if cotok(z,'stark') and (v:=seas(z)) is not None and ((v>=.6) if z['L'] else (v<=.4))],res)
json.dump(res,open('/tmp/fx/mtf.json','w'),indent=1)
