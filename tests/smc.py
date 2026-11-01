import sys,json,random,numpy as np
from ideen import runsig,summ,P,SYMS
from eng import wk_trend
def piv(d,k=3):
    h,l=d['h'],d['l'];n=len(h);sh=np.full(n,np.nan);sl=np.full(n,np.nan);shi=np.full(n,-1);sli=np.full(n,-1)
    cs=cl=np.nan;ci=cj=-1;ph=[];pl=[]
    for i in range(n):
        j=i-k
        if j>=k:
            if h[j]==h[j-k:j+k+1].max(): cs=h[j];ci=j;ph.append(h[j])
            if l[j]==l[j-k:j+k+1].min(): cl=l[j];cj=j;pl.append(l[j])
        sh[i]=cs;sl[i]=cl;shi[i]=ci;sli[i]=cj
    return sh,sl,shi,sli
def prep(s):
    d=P[s]['d'];a=P[s]['a'];c=d['c'];n=len(c)
    sma=np.full(n,np.nan)
    for L in (100,200):
        pass
    cs=np.cumsum(np.r_[0,c]);s100=np.full(n,np.nan);s100[99:]=(cs[100:]-cs[:-100])/100;s200=np.full(n,np.nan);s200[199:]=(cs[200:]-cs[:-200])/200
    return d,a,c,n,s100,s200
def structure(d,k=3):
    """bullish wenn die letzten zwei Swing-Hochs und -Tiefs steigen"""
    h,l=d['h'],d['l'];n=len(h);ph=[];pl=[];bull=np.zeros(n);bear=np.zeros(n)
    for i in range(n):
        j=i-k
        if j>=k:
            if h[j]==h[j-k:j+k+1].max(): ph.append(h[j])
            if l[j]==l[j-k:j+k+1].min(): pl.append(l[j])
        if len(ph)>=2 and len(pl)>=2:
            bull[i]=ph[-1]>ph[-2] and pl[-1]>pl[-2]; bear[i]=ph[-1]<ph[-2] and pl[-1]<pl[-2]
    return bull,bear
def S_bos(strong=0,trend=True):
    out=[]
    for s in SYMS:
        d,a,c,n,s100,s200=prep(s);sh,sl,_,_=piv(d)
        for i in range(210,n-2):
            if np.isnan(sh[i]) or np.isnan(a[i]): continue
            rng=d['h'][i]-d['l'][i]
            if strong and rng<strong*a[i]: continue
            if c[i]>sh[i] and c[i-1]<=sh[i] and (not trend or c[i]>s100[i]): out.append((s,i,True))
            if c[i]<sl[i] and c[i-1]>=sl[i] and (not trend or c[i]<s100[i]): out.append((s,i,False))
    return out
def S_choch(wk=False):
    out=[]
    for s in SYMS:
        d,a,c,n,s100,s200=prep(s);sh,sl,_,_=piv(d);bull,bear=structure(d);wt=wk_trend(d) if wk else None
        for i in range(210,n-2):
            if np.isnan(a[i]): continue
            if bull[i-1] and c[i]<sl[i] and c[i-1]>=sl[i] and (not wk or wt[i]<0): out.append((s,i,False))
            if bear[i-1] and c[i]>sh[i] and c[i-1]<=sh[i] and (not wk or wt[i]>0): out.append((s,i,True))
    return out
def S_retest(win=15):
    out=[]
    for s in SYMS:
        d,a,c,n,s100,s200=prep(s);sh,sl,_,_=piv(d);lv=None
        for i in range(210,n-2):
            if np.isnan(a[i]): continue
            if c[i]>sh[i] and c[i-1]<=sh[i] and c[i]>s100[i]: lv=(i,sh[i],True)
            elif c[i]<sl[i] and c[i-1]>=sl[i] and c[i]<s100[i]: lv=(i,sl[i],False)
            elif lv and 2<=i-lv[0]<=win:
                if lv[2] and d['l'][i]<=lv[1]+0.2*a[i] and c[i]>lv[1]: out.append((s,i,True)); lv=None
                elif (not lv[2]) and d['h'][i]>=lv[1]-0.2*a[i] and c[i]<lv[1]: out.append((s,i,False)); lv=None
            elif lv and i-lv[0]>win: lv=None
    return out
def S_sweep(lb=20,trend=False,thr=0.1):
    out=[]
    for s in SYMS:
        d,a,c,n,s100,s200=prep(s);h,l=d['h'],d['l']
        for i in range(210,n-2):
            if np.isnan(a[i]): continue
            lo=l[i-lb:i].min();hi=h[i-lb:i].max()
            if l[i]<lo-thr*a[i] and c[i]>lo and (not trend or c[i]>s200[i]): out.append((s,i,True))
            if h[i]>hi+thr*a[i] and c[i]<hi and (not trend or c[i]<s200[i]): out.append((s,i,False))
    return out
def S_fvg(win=10,trend=True):
    out=[]
    for s in SYMS:
        d,a,c,n,s100,s200=prep(s);h,l,o=d['h'],d['l'],d['o'];zones=[]
        for i in range(210,n-2):
            if np.isnan(a[i]): continue
            if l[i]>h[i-2] and c[i-1]-o[i-1]>=0.8*a[i]: zones.append([i,h[i-2],l[i],True])
            if h[i]<l[i-2] and o[i-1]-c[i-1]>=0.8*a[i]: zones.append([i,h[i],l[i-2],False])
            keep=[]
            for z in zones:
                if i-z[0]>win or i==z[0]: keep.append(z) if i-z[0]<=win else None; continue
                if z[3] and l[i]<=z[2] and c[i]>z[1] and (not trend or c[i]>s100[i]): out.append((s,i,True)); continue
                if (not z[3]) and h[i]>=z[1] and c[i]<z[2] and (not trend or c[i]<s100[i]): out.append((s,i,False)); continue
                keep.append(z)
            zones=keep
    return out
def S_ob(win=15):
    out=[]
    for s in SYMS:
        d,a,c,n,s100,s200=prep(s);sh,sl,_,_=piv(d);h,l,o=d['h'],d['l'],d['o'];zs=[]
        for i in range(210,n-2):
            if np.isnan(a[i]): continue
            if c[i]>sh[i] and c[i-1]<=sh[i]:
                for k in range(i-1,i-9,-1):
                    if c[k]<o[k]: zs.append([i,l[k],h[k],True]);break
            if c[i]<sl[i] and c[i-1]>=sl[i]:
                for k in range(i-1,i-9,-1):
                    if c[k]>o[k]: zs.append([i,l[k],h[k],False]);break
            keep=[]
            for z in zs:
                if i-z[0]>win: continue
                if i>z[0] and z[3] and l[i]<=z[2] and c[i]>z[1]: out.append((s,i,True)); continue
                if i>z[0] and (not z[3]) and h[i]>=z[1] and c[i]<z[2]: out.append((s,i,False)); continue
                keep.append(z)
            zs=keep
    return out
def S_eql(lb=30):
    out=[]
    for s in SYMS:
        d,a,c,n,s100,s200=prep(s);h,l=d['h'],d['l']
        for i in range(210,n-2):
            if np.isnan(a[i]): continue
            w=l[i-lb:i];m=w.min()
            if (w<=m+0.2*a[i]).sum()>=2 and l[i]<m-0.05*a[i] and c[i]>m: out.append((s,i,True))
            w=h[i-lb:i];m=w.max()
            if (w>=m-0.2*a[i]).sum()>=2 and h[i]>m+0.05*a[i] and c[i]<m: out.append((s,i,False))
    return out
CAND={'BOS Trend':lambda:S_bos(0,True),'BOS stark':lambda:S_bos(1.3,True),'CHoCH':lambda:S_choch(False),'CHoCH+Weekly':lambda:S_choch(True),'BOS Retest':lambda:S_retest(15),
 'Sweep 20':lambda:S_sweep(20,False),'Sweep 20+Trend':lambda:S_sweep(20,True),'FVG Retest':lambda:S_fvg(10,True),'OB nach BOS':lambda:S_ob(15),'Equal Lows Sweep':lambda:S_eql(30)}
if __name__=='__main__':
    rnd=random.Random(4);res={}
    for nm,fn in CAND.items():
        sg=fn();rows=[]
        for sa in (1.5,2,3):
            for tg in (None,1,1.5,2):
                for N in (10,20,40):
                    tr=runsig(sg,sa,tg,N);a,dv,te=summ(tr)
                    if a.get('avg') is None or a['n']<150: continue
                    rows.append((a['avg'],sa,tg,N,a,dv,te))
        rows.sort(key=lambda x:-(x[5].get('avg') or -9)) # nach Dev waehlen
        print(nm,len(sg),'Signale',flush=True)
        for r in rows[:3]: print('   ',r[1:4],r[4],'dev',r[5].get('avg'),'test',r[6].get('avg'),flush=True)
        res[nm]=[(r[1],r[2],r[3]) for r in rows[:1]]
    json.dump({k:v for k,v in res.items()},open('/tmp/smc_best.json','w'))
