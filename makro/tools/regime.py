"""Referenzlogik des Regime-Indikators (identisch zur Pine-Version)."""
import math
def ema(x,n):
    a=2/(n+1); o=[]; p=None
    for v in x:
        p=v if p is None else a*v+(1-a)*p; o.append(p)
    return o
def rma(x,n):
    o=[];p=None
    for i,v in enumerate(x):
        if i<n-1: o.append(None); continue
        if p is None: p=sum(x[:n])/n
        else: p=(p*(n-1)+v)/n
        o.append(p)
    return o
def adx(h,l,c,n=14):
    tr=[0];pdm=[0];ndm=[0]
    for i in range(1,len(c)):
        up=h[i]-h[i-1];dn=l[i-1]-l[i]
        pdm.append(up if up>dn and up>0 else 0); ndm.append(dn if dn>up and dn>0 else 0)
        tr.append(max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])))
    atr=rma(tr[1:],n);ps=rma(pdm[1:],n);ns=rma(ndm[1:],n)
    atr=[None]+atr;ps=[None]+ps;ns=[None]+ns
    dx=[None]*len(c)
    for i in range(len(c)):
        if atr[i] and atr[i]>0:
            pi=100*ps[i]/atr[i];ni=100*ns[i]/atr[i]
            dx[i]=100*abs(pi-ni)/(pi+ni) if pi+ni>0 else 0
    first=next((i for i,v in enumerate(dx) if v is not None),None)
    ad=[None]*len(c)
    if first is None: return ad,atr
    seg=[v for v in dx[first:]]
    r=rma(seg,n)
    for k,v in enumerate(r): ad[first+k]=v
    return ad,atr
def regime(o,h,l,c,emaN=50,slopeN=10,adxMin=20,adxN=14):
    """+1 gruen (Aufwaerts), -1 rot (Abwaerts), 0 gelb (Range/Uebergang); None = zu wenig Daten"""
    e=ema(c,emaN); ad,atr=adx(h,l,c,adxN); out=[]
    for i in range(len(c)):
        if i<emaN+slopeN or ad[i] is None: out.append(None); continue
        up=c[i]>e[i] and e[i]>e[i-slopeN]; dn=c[i]<e[i] and e[i]<e[i-slopeN]
        out.append(1 if up and ad[i]>=adxMin else -1 if dn and ad[i]>=adxMin else 0)
    return out
def profile(h,l,v,i,n=120,bins=30,va=0.70):
    """Volumenprofil der letzten n Kerzen bis einschliesslich i. Gibt (poc,vah,val) zurueck."""
    s=max(0,i-n+1); hi=max(h[s:i+1]); lo=min(l[s:i+1])
    if hi<=lo: return None
    st=(hi-lo)/bins; vol=[0.0]*bins
    for j in range(s,i+1):
        a=min(bins-1,int((l[j]-lo)/st)); b=min(bins-1,int((h[j]-lo)/st)); k=b-a+1
        for q in range(a,b+1): vol[q]+=v[j]/k
    p=max(range(bins),key=lambda q:(vol[q],-abs(q-bins/2)))
    tot=sum(vol); acc=vol[p]; lo_i=hi_i=p
    while acc<va*tot and (lo_i>0 or hi_i<bins-1):
        dn=vol[lo_i-1] if lo_i>0 else -1; up=vol[hi_i+1] if hi_i<bins-1 else -1
        if up>=dn: hi_i+=1; acc+=vol[hi_i]
        else: lo_i-=1; acc+=vol[lo_i]
    return lo+(p+.5)*st, lo+(hi_i+1)*st, lo+lo_i*st
