"""Daily-OB (Nutzerdefinition strictbt + alte Qualitaet-A-Zonen) mit 1H-Bestaetigung: Zone beruehrt -> 1H-Schluss ueber das Hoch der letzten 5 1H-Kerzen (Long, Short gespiegelt)."""
import glob,json,sys
exec(open('/home/claude/journal-daten/tests/strictbt.py').read().split("if __name__")[0])
HOME2='/home/claude/journal-privat/marktdaten/intra'
def h1(sym):
    r=[]
    for f in sorted(glob.glob(f'{HOME2}/{sym}_1H_*.json')): r+=json.load(open(f))['rows']
    r=np.array(sorted({x[0]:x for x in r}.values()),float)
    return dict(t=r[:,0],o=r[:,1],h=r[:,2],l=r[:,3],c=r[:,4])
Zloose=[]
_ns={}
exec(open('/tmp/dobzraw.py').read(),_ns); Zloose=[z for z in _ns['Z'] if z['sym'] not in PIPS]
H={s:h1(s) for s in U if glob.glob(f'{HOME2}/{s}_1H_*.json')}
T0=min(H[s]['t'][0] for s in H)
def sim1(h,i,L,en,st,tg,maxb,sym):
    risk=abs(en-st); sp=eng.SPREAD_PIPS*eng.pip(sym)/risk; tp=en+tg*risk if L else en-tg*risk
    for j in range(i+1,min(i+1+maxb,len(h['c']))):
        if (h['l'][j]<=st) if L else (h['h'][j]>=st): return -1-sp
        if (h['h'][j]>=tp) if L else (h['l'][j]<=tp): return tg-sp
    c=h['c'][min(i+maxb,len(h['c'])-1)]; return ((c-en) if L else (en-c))/risk-sp
def ltf(zs,tg,N=5,days=10,mode='ref'):
    res=[]
    for z in zs:
        s=z['sym']
        if s not in H: continue
        d=U[s]; h=H[s]; L=z['L']; lo,hi=z['lo'],z['hi']
        top=(z['bt'] if L else hi) if mode=='ref' else (hi if L else lo); 
        k0=None
        for k in range(z['j']+1,min(len(d['c']),z['j']+60)):
            if (d['c'][k]<lo) if L else (d['c'][k]>hi): break
            if (d['l'][k]<=top) if L else (d['h'][k]>=(z['bb'] if mode=='ref' else lo)): k0=k; break
        if k0 is None or d['t'][k0]<T0: continue
        i0=int(np.searchsorted(h['t'],d['t'][k0])); t_end=d['t'][k0]+days*86400e3
        touched=None; i=i0
        while i<len(h['c']) and h['t'][i]<t_end:
            if (h['c'][i]<lo) if L else (h['c'][i]>hi): break
            if touched is None and ((h['l'][i]<=top) if L else (h['h'][i]>=(z['bb'] if mode=='ref' else lo))): touched=i
            if touched is not None and i-touched>=N:
                bull=h['c'][i]>h['o'][i] if L else h['c'][i]<h['o'][i]
                brk=(h['c'][i]>h['h'][i-N:i].max()) if L else (h['c'][i]<h['l'][i-N:i].min())
                if bull and brk:
                    en=h['c'][i]; ext=h['l'][touched:i+1].min() if L else h['h'][touched:i+1].max()
                    st=ext-0.05*z['a'] if L else ext+0.05*z['a']; risk=abs(en-st)
                    if 0<risk<1.5*z['a']: res.append((s,sim1(h,i,L,en,st,tg,300,s),dt.datetime.fromtimestamp(h['t'][i]/1000,dt.timezone.utc)))
                    break
            i+=1
    return res
if __name__=='__main__':
    ZA=[z for s in U if s not in PIPS for z in strict(s)]
    ZB=[dict(sym=z['sym'],L=z['L'],j=z['i'],hi=z['hi'],lo=z['lo'],bt=max(z['hi']-0,z['lo']),bb=z['lo'],a=z['a'] if not np.isnan(z['a']) else A[z['sym']][z['i']]) for z in Z0] if False else None
    print('1H-Daten ab',dt.datetime.fromtimestamp(T0/1000,dt.timezone.utc).date(),'Paare',sorted(H))
    ZL=[]
    for z in Zloose:
        d=U[z['sym']]; i=z['i']; a=z['a'] if not np.isnan(z['a']) else A[z['sym']][i]
        ZL.append(dict(sym=z['sym'],L=z['L'],j=i+3,hi=z['hi'],lo=z['lo'],bt=max(d['o'][i],d['c'][i]),bb=min(d['o'][i],d['c'][i]),a=a))
    ZLA=[z for z,o in zip(ZL,Zloose) if o['q']=='A']
    for nm,zs in (('Nutzerdefinition',ZA),('alte Regel alle Qualitaeten',ZL),('alte Regel Qualitaet A',ZLA)):
        for mode in ('ref','ext'):
            for tg in (2,3,4):
                r=ltf(zs,tg,mode=mode); x=np.array([a[1] for a in r])
                if len(x): print(f'{nm} {mode} Ziel {tg}R: n={len(x)} E={x.mean():+.2f} R wr={100*(x>0).mean():.0f}% Summe={x.sum():+.1f} R')
