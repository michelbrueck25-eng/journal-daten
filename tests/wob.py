"""Weekly-Orderblock-Engine (Zone aus Wochenkerzen nach ob_check.find_obs, Einstieg/Verlauf auf Tageskerzen). Fuer fw2-w-* und Varianten."""
import sys,os,io,contextlib,datetime as dt,importlib.util,numpy as np,bisect
sys.path.insert(0,'/home/claude/journal-daten/tests')
with contextlib.redirect_stdout(io.StringIO()):
    import eng
    from eng import *
    import gen
sp=importlib.util.spec_from_file_location('ob_check','/home/claude/journal-privat/ob_check.py'); OC=importlib.util.module_from_spec(sp)
with contextlib.redirect_stdout(io.StringIO()): sp.loader.exec_module(OC)
PIPS={'GOLD':0.1,'SILBER':0.01,'PLATIN':1.0,'KUPFER':0.002,'OEL':0.03,'ERDGAS':0.003}
eng.pip=lambda s: PIPS.get(s,0.01 if s.endswith('JPY') else 0.0001)
U=load_all(); A={s:atr(U[s]) for s in U}
def D(ms): return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).strftime('%Y-%m-%d')
def cidx(cur,date):
    d=(dt.date.fromisoformat(date)-dt.timedelta(days=3)).isoformat()   # Report (Dienstag) ist ab Freitag nutzbar
    return gen.cot_idx(cur,d)
def zones():
    Z=[]
    for s in U:
        W=[list(r[:5]) for r in U[s]['W']]
        for dr in ('long','short'):
            for z in OC.find_obs(W,dr): Z.append(dict(sym=s,L=dr=='long',lo=z['lo'],hi=z['hi'],i=z['i'],W=W))
    return Z
_Z=[]
def run(tg,md,cot,weeks=40,stopb=0.1):
    if not _Z: _Z.extend(zones())
    out=[]
    for z in _Z:
        s=z['sym']; d=U[s]; W=z['W']; L=z['L']; t=d['t']; found=False
        for k in range(z['i']+4,min(len(W),z['i']+4+weeks)):
            t0=W[k][0]; t1=t0+7*86400e3
            lo_i=bisect.bisect_left(t,t0); hi_i=bisect.bisect_left(t,t1)
            for q in range(max(lo_i,1),hi_i):
                if d['l'][q]<=z['hi'] and d['h'][q]>=z['lo']:
                    a=A[s][q-1]
                    if np.isnan(a): found=True; break
                    date=D(t[q])
                    if cot!='ohne':
                        cb,cq=cidx(s[:3],date),cidx(s[3:],date)
                        if cb is None or cq is None: found=True; break
                        df=(cb-cq) if L else (cq-cb)
                        ok={'stark':df>=30,'schwach':df<=-30,'extrem':(cb>75 and cq<25) if L else (cb<25 and cq>75)}[cot]
                        if not ok: found=True; break
                    en=z['hi'] if L else z['lo']; stop=z['lo']-stopb*a if L else z['hi']+stopb*a
                    r=simulate(d,q,L,en,stop,tg,md,s)
                    if r: out.append(dict(r=r[0],date=date,sym=s,bars=r[1],L=L,entry=float(en),why=r[2],offen=(r[2]=='Zeit' and q+1+md>len(d['c'])),last=D(t[min(q+r[1],len(t)-1)])))
                    found=True; break
            if found: break
            if (W[k][4]<z['lo']) if L else (W[k][4]>z['hi']): break
    return out
if __name__=='__main__':
    for cot in ('ohne','stark','schwach','extrem'):
        tr=run(1.5,7,cot); r=np.array([x['r'] for x in tr]); print(cot,len(r),round(r.mean(),3))
