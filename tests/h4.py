"""Weekly-OB-Hit -> 4H-Break + Retest -> Ziel 1R / 2R. (a) alle Weekly-Zonen (alte Regel, wob.zones), (b) Nutzer-Trades mit eigener Zone. 4H-Daten ab 2025-04."""
import sys,json,os,io,contextlib,bisect,datetime as dt
sys.path.insert(0,'/home/claude/journal-daten/tests')
with contextlib.redirect_stdout(io.StringIO()):
    import wob
import numpy as np
from eng import SPREAD_PIPS
pip=wob.eng.pip; U=wob.U; A=wob.A
def d4(sym):
    f=f'/home/claude/journal-privat/marktdaten/{sym}_4H.json'
    if not os.path.exists(f): return None
    r=np.array(json.load(open(f))['rows'],float); return dict(t=r[:,0],o=r[:,1],h=r[:,2],l=r[:,3],c=r[:,4])
H4={s:d4(s) for s in U}
def atr4(h,n=14):
    tr=np.maximum(h['h'][1:]-h['l'][1:],np.maximum(abs(h['h'][1:]-h['c'][:-1]),abs(h['l'][1:]-h['c'][:-1])))
    a=np.full(len(h['c']),np.nan)
    for i in range(n,len(h['c'])): a[i]=tr[i-n:i].mean()
    return a
A4={s:atr4(H4[s]) for s in H4 if H4[s] is not None}
def trade(sym,L,lo,hi,t_from,t_to=None,tgs=(1,2),lookb=6,wait=40,tol=0.1):
    """liefert dict {tg:R} oder None. t_from = Zeitpunkt ab dem der Hit gesucht wird (ms)."""
    h=H4.get(sym)
    if h is None: return None
    n=len(h['c']); a4=A4[sym]; sp=SPREAD_PIPS*pip(sym)
    i0=int(np.searchsorted(h['t'],t_from))
    if i0<=lookb+1 or i0>=n-5: return None
    t=None
    for i in range(i0,n if t_to is None else min(n,int(np.searchsorted(h['t'],t_to)))):
        if (h['c'][i]<lo) if L else (h['c'][i]>hi): return None
        if (h['l'][i]<=hi) if L else (h['h'][i]>=lo): t=i; break
    if t is None: return None
    sw=h['h'][t-lookb:t+1].max() if L else h['l'][t-lookb:t+1].min()   # Swing, der gebrochen werden muss
    j=None
    for i in range(t+1,min(n,t+60)):
        if (h['c'][i]<lo) if L else (h['c'][i]>hi): return None
        if (h['c'][i]>sw) if L else (h['c'][i]<sw): j=i; break
    if j is None: return None
    tolr=tol*a4[j] if not np.isnan(a4[j]) else 0
    k=None
    for i in range(j+1,min(n-1,j+1+wait)):
        if (h['c'][i]<lo) if L else (h['c'][i]>hi): return None
        if (h['l'][i]<=sw+tolr) if L else (h['h'][i]>=sw-tolr): k=i; break
    if k is None: return None
    en=sw
    ext=h['l'][t:k+1].min() if L else h['h'][t:k+1].max()
    st=ext-pip(sym) if L else ext+pip(sym)
    risk=abs(en-st)
    if risk<=0 or risk>3*(a4[k] if not np.isnan(a4[k]) else risk): return None
    if (h['l'][k]<=st) if L else (h['h'][k]>=st): return {tg:-1-sp/risk for tg in tgs}|{'when':h['t'][k]}
    out={'when':h['t'][k]}
    for tg in tgs:
        tp=en+tg*risk if L else en-tg*risk; r=None
        for m in range(k+1,min(n,k+201)):
            if (h['l'][m]<=st) if L else (h['h'][m]>=st): r=-1-sp/risk; break
            if (h['h'][m]>=tp) if L else (h['l'][m]<=tp): r=tg-sp/risk; break
        if r is None:
            c=h['c'][min(n-1,k+200)]; r=((c-en) if L else (en-c))/risk-sp/risk
        out[tg]=r
    return out
def summ(nm,res):
    if not res: print(nm,'keine Trades'); return
    for tg in (1,2):
        x=np.array([r[tg] for r in res]); print(f'{nm} Ziel {tg}R: n={len(x)} E={x.mean():+.3f} R wr={100*(x>0).mean():.0f}% Summe={x.sum():+.1f} R')
if __name__=='__main__':
    # (a) alle Weekly-Zonen (alte Regel), Hit nach Bildung (i+4) im 4H-Zeitraum
    res=[]; seen=set()
    for z in wob.zones():
        s=z['sym']; W=z['W']
        if H4.get(s) is None or z['i']+4>=len(W): continue
        # Zone muss bis zum Hit auf Tagesbasis unverletzt sein
        t0=W[z['i']+4][0]
        if t0>H4[s]['t'][-1]: continue
        t_start=max(t0,H4[s]['t'][0]+10*86400e3)
        d=U[s]; q0=bisect.bisect_left(d['t'],W[z['i']+4][0]); q1=bisect.bisect_left(d['t'],t_start)
        broken=any((d['c'][q]<z['lo']) if z['L'] else (d['c'][q]>z['hi']) for q in range(q0,q1))
        if broken: continue
        r=trade(s,z['L'],z['lo'],z['hi'],t_start)
        if r: res.append(r)
    summ('alle Weekly-Zonen (alte Regel)',res)
    # (b) Nutzer-Trades mit eigener Zone und 4H-Daten
    E=json.load(open('/home/claude/journal-privat/journal-export.json'))['trades']
    res2=[]; info=[]
    for x in E:
        c=x.get('chart')
        if not c or x['instrument'] not in H4 or H4[x['instrument']] is None: continue
        ent=dt.datetime.fromisoformat(x.get('entryDate') or x['analysisDate']).replace(tzinfo=dt.timezone.utc).timestamp()*1000
        rects=[d for d in c['drs'] if d['type']=='rect']
        if not rects: continue
        t_use=max(d['t1'] for d in rects)
        ref=ent if abs(t_use-ent)>120*86400e3*0+120*86400e3 and False else None
        # Zeitbezug: Zeichnung, falls Journaldatum weit abweicht
        ts=[d['t0'] for d in c['drs']]+[d['t1'] for d in c['drs']]
        a=ent if abs(np.median(ts)-ent)<=120*86400e3 else np.median(ts)
        if not (H4[x['instrument']]['t'][0]<=a-14*86400e3 and a<=H4[x['instrument']]['t'][-1]): continue
        L=x['dir']=='long'; pos=[d for d in c['drs'] if d['type']=='pos']
        if pos:
            e0=pos[-1]['entry']; rr=min(rects,key=lambda d:abs((d['p0']+d['p1'])/2-e0))
        else: rr=rects[-1]
        lo,hi=sorted((rr['p0'],rr['p1']))
        r=trade(x['instrument'],L,lo,hi,a-14*86400e3,a+60*86400e3)
        if r: res2.append(r); info.append((x['instrument'],x['source'],x.get('r'),r[1],r[2]))
    summ('Nutzer-Zonen mit 4H-Daten',res2)
    rr=[i[2] for i in info if isinstance(i[2],(int,float))]
    print('Nutzer: Trades mit Signal',len(info),'davon eigener Ø R',np.mean(rr) if rr else None)
