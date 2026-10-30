import numpy as np,pandas as pd,itertools,pickle,sys
from seas import P,SYMS,cost_r
from ideen import sig_don,summ,FX
from eng import wk_trend
def pyr(s,i,L,sa,tk,adds,red,N):
    """Einstieg naechster Open, Stop sa*ATR, Chandelier-Trail tk*ATR vom Extrem (ab Folgetag), Aufstocken je Stufe (R-Vielfaches,Groesse), red=(Tage,R-Schwelle) halbiert Verlierer.
    R-Einheit = anfaengliches Risiko der Basisposition (Groesse 1). Rueckgabe Gesamt-R netto, Ende-j, Start, maxsize"""
    d=P[s]['d']; n=len(d['c']); a=P[s]['a'][i]
    if i+1+N>=n or np.isnan(a): return None
    e=d['o'][i+1]; sd=sa*a; sg=1 if L else -1
    stp=e-sg*sd; units=[[e,1.0,i+1]]; ext=e; done=list(adds); r_real=0.0; cost=0.0; reduced=False
    j_end=None
    for j in range(i+1,i+1+N):
        hi,lo,cl=d['h'][j],d['l'][j],d['c'][j]
        # Stop zuerst (konservativ, mit Stop vom Vortag)
        if (lo<=stp) if L else (hi>=stp):
            px=stp; sz=sum(u[1] for u in units)
            r_real+=sum(u[1]*sg*(px-u[0])/sd for u in units)
            cost+=sum(u[1]*cost_r(s,sd,a,(P[s]['ts'][j]-P[s]['ts'][u[2]]).days) for u in units); j_end=j; units=[]; break
        # Aufstocken
        for (lv,sz) in list(done):
            lvp=e+sg*lv*sd
            if ((hi>=lvp) if L else (lo<=lvp)) and j>i+1:
                units.append([lvp,sz,j]); done.remove((lv,sz))
        ext=max(ext,hi) if L else min(ext,lo)
        stp=max(stp,ext-tk*a) if L else min(stp,ext+tk*a)
        if red and not reduced and j-(i+1)==red[0] and sg*(cl-e)/sd<red[1]:
            r_real+=sum(0.5*u[1]*sg*(cl-u[0])/sd for u in units)
            cost+=sum(0.5*u[1]*cost_r(s,sd,a,(P[s]['ts'][j]-P[s]['ts'][u[2]]).days) for u in units)
            for u in units: u[1]*=0.5
            reduced=True
    if units:
        j=i+N; px=d['c'][j]; r_real+=sum(u[1]*sg*(px-u[0])/sd for u in units)
        cost+=sum(u[1]*cost_r(s,sd,a,(P[s]['ts'][j]-P[s]['ts'][u[2]]).days) for u in units); j_end=j
    return r_real-cost,j_end,i+1
def run(sigs,**k):
    out=[];busy={}
    for (s,i,L) in sorted(sigs,key=lambda x:(P[x[0]]['ts'][x[1]],x[0])):
        if i<=busy.get(s,-1): continue
        t=pyr(s,i,L,**k)
        if not t: continue
        busy[s]=t[1]; out.append(dict(sym=s,date=str(P[s]['ts'][t[2]]),dir='long' if L else 'short',r=float(t[0]),hold=t[1]-t[2]))
    return out
def sig_ma(f,sl):
    out=[]
    for s in FX:
        c=pd.Series(P[s]['d']['c']); a=c.rolling(f).mean(); b=c.rolling(sl).mean(); tr=wk_trend(P[s]['d'])
        for i in range(sl+1,len(c)-2):
            if a[i-1]<=b[i-1] and a[i]>b[i] and tr[i]>0: out.append((s,i,True))
            if a[i-1]>=b[i-1] and a[i]<b[i] and tr[i]<0: out.append((s,i,False))
    return out
def sig_mom(Lb,hd=4):
    df=pd.DataFrame({s:(lambda x:x[~x.index.duplicated(keep='last')])(pd.Series(P[s]['d']['c'],index=pd.to_datetime(P[s]['ts']))) for s in FX}).sort_index().ffill()
    lr=np.log(df/df.shift(Lb)); out=[]
    for t in df.index:
        if t.weekday()!=hd: continue
        for s in FX:
            v=lr.loc[t,s]; i=P[s]['idx'].get(t.date())
            if i is None or np.isnan(v): continue
            tr=wk_trend(P[s]['d'])[i]
            # Top/Flop-Quintil absolut ueber Historie vermeiden: Schwelle 2 sigma der Lb-Rendite
            if v>2*lr[s].std() and tr>0: out.append((s,i,True))
            if v<-2*lr[s].std() and tr<0: out.append((s,i,False))
    return out
def sig_sq(n=20,w=6):
    """Volatilitaetskompression: ATR/ATR100 klein + Breakout"""
    out=[]
    for s in FX:
        d=P[s]['d']; a=P[s]['a']; am=pd.Series(a).rolling(100).mean().values; h=pd.Series(d['h']).rolling(n).max().shift(1).values; l=pd.Series(d['l']).rolling(n).min().shift(1).values
        for i in range(120,len(a)-2):
            if a[i]/am[i]<0.85:
                if d['c'][i]>h[i]: out.append((s,i,True))
                if d['c'][i]<l[i]: out.append((s,i,False))
    return out
if __name__=='__main__':
    sigsets={'Donchian20':sig_don(20),'Donchian55':sig_don(55),'MA20/50':sig_ma(20,50),'MA10/30':sig_ma(10,30),'Mom60':sig_mom(60),'Mom120':sig_mom(120),'Squeeze20':sig_sq(20)}
    res=[]
    for nm,sg in sigsets.items():
        for sa,tk,adds,red,N in itertools.product((2,),(3,4,5),((),((1,.5),(2,.5)),((1,1),(2,1))),(None,(5,0)),(20,40)):
            tr=run(sg,sa=sa,tk=tk,adds=adds,red=red,N=N); a,b,c=summ(tr)
            res.append(dict(name=nm,sa=sa,tk=tk,adds=adds,red=red,N=N,all=a,dev=b,test=c,_tr=tr))
            print(nm,tk,len(adds),red,N,'|',a.get('n'),a.get('wr'),a.get('avg'),'| dev',b.get('avg'),'| test',c.get('avg'),c.get('n'),flush=True)
    pickle.dump(res,open('/tmp/pyr.pkl','wb'))
