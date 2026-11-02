import warnings;warnings.filterwarnings('ignore')
from sweeps import *
def pivots(d,w=3):
    h,l=d['h'],d['l'];n=len(h);ph=[None]*n;pl=[None]*n;chi=cli=None
    for i in range(n):
        k=i-w
        if k>=w:
            if h[k]==max(h[k-w:k+w+1]):chi=(k,h[k])
            if l[k]==min(l[k-w:k+w+1]):cli=(k,l[k])
        ph[i]=chi;pl[i]=cli
    return ph,pl
def run(tf,entry_mode,tgt,valid,hold,trend=False,w=3):
    out=[]
    for s in SYMS if tf=='4H' else sorted(os.path.basename(f).split('_')[0] for f in glob.glob(f'{HOME}/marktdaten/*_D.json') if len(os.path.basename(f).split('_')[0])==6 and 'XAU' not in os.path.basename(f)):
        d=load(s,tf);A=atr(d);n=len(d['c']);ph,pl=pivots(d,w);D=[str(day(t)) for t in d['t']]
        sma=np.full(n,np.nan)
        for i in range(100,n):sma[i]=d['c'][i-100:i].mean()
        lastbos=-99;used=set()
        for j in range(60,n-2):
            if np.isnan(A[j]):continue
            for L in(1,-1):
                if L>0:
                    if not(ph[j] and d['c'][j]>ph[j][1] and d['c'][j-1]<=ph[j][1] and pl[j]):continue
                    lo_i=pl[j][0];cand=[k for k in range(lo_i,j) if d['c'][k]<d['o'][k]]
                else:
                    if not(pl[j] and d['c'][j]<pl[j][1] and d['c'][j-1]>=pl[j][1] and ph[j]):continue
                    lo_i=ph[j][0];cand=[k for k in range(lo_i,j) if d['c'][k]>d['o'][k]]
                if not cand or j-lo_i>40:continue
                if trend and (L>0)!=(d['c'][j]>sma[j]):continue
                k=cand[-1];top,bot=max(d['h'][k],d['o'][k],d['c'][k]) if False else d['h'][k],d['l'][k]
                zt,zb=(top,bot);zm=(zt+zb)/2
                if zt-zb<0.2*A[j] or zt-zb>3*A[j]:continue
                key=(s,k)
                if key in used:continue
                stop=zb-0.1*A[j] if L>0 else zt+0.1*A[j]
                if entry_mode in('mid','edge'):
                    ent=zm if entry_mode=='mid' else (zt if L>0 else zb)
                    # Limit fuellen
                    f=None
                    for i in range(j+1,min(j+1+valid,n-1)):
                        if (d['l'][i]<=ent if L>0 else d['h'][i]>=ent):f=i;break
                        if (d['c'][i]<zb if L>0 else d['c'][i]>zt):break   # Zone verletzt
                    if f is None:continue
                    risk=abs(ent-stop)
                    if risk<0.3*A[j] or risk>4*A[j]:continue
                    # Stopp in Fuellkerze pruefen (pessimistisch), dann sim ab naechster
                    if (d['l'][f]<=stop if L>0 else d['h'][f]>=stop):r=(-1-1.2*pip(s)/risk,0)
                    else:
                        tp=ent+L*tgt*risk
                        if (d['h'][f]>=tp if L>0 else d['l'][f]<=tp) and False:r=(tgt,0)
                        r=sim(d,f+1,L,ent,stop,tgt,hold,s) if f+1<n else None
                    ft=f
                else:  # confirm: Beruehrung der Zone, dann Kerze schliesst zurueck in Trendrichtung ausserhalb der Zone
                    f=None;touched=False
                    for i in range(j+1,min(j+1+valid,n-2)):
                        if (d['l'][i]<=zt if L>0 else d['h'][i]>=zb):touched=True
                        if touched and ((d['c'][i]>zt and d['c'][i]>d['o'][i]) if L>0 else (d['c'][i]<zb and d['c'][i]<d['o'][i])):f=i;break
                        if (d['c'][i]<zb if L>0 else d['c'][i]>zt):break
                    if f is None:continue
                    ent=d['o'][f+1];risk=abs(ent-stop)
                    if risk<0.3*A[j] or risk>4*A[j] or (stop-ent)*L>0:continue
                    r=sim(d,f+1,L,ent,stop,tgt,hold,s);ft=f
                if r:used.add(key);out.append(dict(s=s,d=D[ft],L=L,r=r[0]))
    return out
if __name__=='__main__':
    R=[]
    for tf,valid,hold in(('D',20,15),('4H',30,20)):
        for em in('mid','edge','confirm'):
            for tg in(1,2,3):
                for tr_ in(False,True):
                    x=rep(run(tf,em,tg,valid,hold,tr_),f'BOS+OB-Retest {tf} Einstieg {em}, Ziel {tg}R{", Trend" if tr_ else ""}');R.append(x) if x else None
    json.dump(R,open('/tmp/fx/bosob.json','w'))
