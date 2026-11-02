"""Daily-Zonen (alte Regel A/alle, Nutzerdefinition) mit 4H- bzw. 1H-Break+Retest, Ziel 1R/2R."""
import sys,glob,json,io,contextlib,datetime as dt
sys.path.insert(0,'/home/claude/journal-daten/tests')
import numpy as np
import h4
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('/home/claude/journal-daten/tests/strictbt.py').read().split("if __name__")[0])
    _ns={}; exec(open('/tmp/dobzraw.py').read(),_ns)
Zold=[z for z in _ns['Z'] if z['sym'] not in PIPS]
Znew=[z for s in U if s not in PIPS for z in strict(s)]
def h1(sym):
    r=[]
    for f in sorted(glob.glob(f'/home/claude/journal-privat/marktdaten/intra/{sym}_1H_*.json')): r+=json.load(open(f))['rows']
    if not r: return None
    r=np.array(sorted({x[0]:x for x in r}.values()),float); return dict(t=r[:,0],o=r[:,1],h=r[:,2],l=r[:,3],c=r[:,4])
H1={s:h1(s) for s in U}
A1={s:h4.atr4(H1[s]) for s in H1 if H1[s] is not None}
H4s,A4s=h4.H4,h4.A4
def run(zs,tf,lookb,wait):
    h4.H4,h4.A4=(H4s,A4s) if tf=='4H' else (H1,A1)
    data=h4.H4; res=[]
    for z in zs:
        s=z['sym']
        if data.get(s) is None: continue
        d=U[s]; L=z['L']; lo,hi=z['lo'],z['hi']
        j=z['i']+3 if 'i' in z else z['j']
        t0=d['t'][min(j+1,len(d['t'])-1)]; tfr=max(t0,data[s]['t'][0]+7*86400e3)
        if tfr>data[s]['t'][-1]: continue
        q0=j+1; q1=int(np.searchsorted(d['t'],tfr))
        if any((d['c'][q]<lo) if L else (d['c'][q]>hi) for q in range(q0,min(q1,len(d['c'])))): continue
        r=h4.trade(s,L,lo,hi,tfr,lookb=lookb,wait=wait)
        if r: res.append(r)
    return res
for nm,zs in (('alte Regel alle',Zold),('alte Regel A',[z for z in Zold if z['q']=='A']),('Nutzerdefinition',Znew)):
    for tf,lb,w in (('4H',6,40),('1H',8,60)):
        r=run(zs,tf,lb,w)
        for tg in (1,2):
            if r:
                x=np.array([a[tg] for a in r]); print(f'{nm:16s} {tf} Ziel {tg}R: n={len(x)} E={x.mean():+.3f} R wr={100*(x>0).mean():.0f}% Summe={x.sum():+.1f} R')
            else: print(nm,tf,'keine Trades')
