import json,numpy as np,datetime,sys
SY=['DAX','SPX','NDX','NKX','FTSE','SILBER','OEL','GOLD']
def load(s):
    r=json.load(open('/home/claude/journal-privat/marktdaten/%s_D.json'%s))['rows']
    a=np.array(r,float);d=[datetime.datetime.fromtimestamp(x/1000,datetime.timezone.utc).date() for x in a[:,0]]
    return d,a[:,1],a[:,2],a[:,3],a[:,4]
def sma(x,n):
    o=np.full(len(x),np.nan);c=np.cumsum(np.insert(x,0,0));o[n-1:]=(c[n:]-c[:-n])/n;return o
def atr(h,l,c,n=14):
    tr=np.maximum(h-l,np.maximum(abs(h-np.roll(c,1)),abs(l-np.roll(c,1))));tr[0]=h[0]-l[0];return sma(tr,n)
def rsi(c,n=2):
    d=np.diff(c,prepend=c[0]);g=np.where(d>0,d,0);l=np.where(d<0,-d,0)
    ag=np.zeros(len(c));al=np.zeros(len(c))
    ag[n]=g[1:n+1].mean();al[n]=l[1:n+1].mean()
    for i in range(n+1,len(c)):ag[i]=(ag[i-1]*(n-1)+g[i])/n;al[i]=(al[i-1]*(n-1)+l[i])/n
    rs=ag/np.where(al==0,1e-9,al);return 100-100/(1+rs)
COST=0.05;SW=0.012
def run(s,sig,exitf,stopm=2.0,short=False,maxd=30):
    d,o,h,l,c=load(s);A=atr(h,l,c);out=[];i=250;n=len(c)
    while i<n-2:
        if A[i]>0 and sig(i,d,o,h,l,c,A):
            e=o[i+1];risk=stopm*A[i];st=e-risk;j=i+1;res=None
            while j<n:
                if l[j]<=st:res=(st-e)/risk;break
                if j>=i+1+maxd or exitf(j,d,o,h,l,c,A,i+1):res=(c[j]-e)/risk;break
                j+=1
            if res is None:break
            days=(d[j]-d[i+1]).days
            res-= (COST+SW*days)*A[i]/risk
            out.append((d[i+1],s,res,j-i));i=j+1
        else:i+=1
    return out
def stats(tr):
    if not tr:return None
    r=np.array([t[2] for t in tr]);dev=[t[2] for t in tr if t[0]<datetime.date(2023,1,1)];te=[t[2] for t in tr if t[0]>=datetime.date(2023,1,1)]
    return len(r),r.mean(),np.mean(dev) if dev else float('nan'),np.mean(te) if te else float('nan'),len(te)
def prep(s):
    d,o,h,l,c=load(s);return dict(s200=sma(c,200),s5=sma(c,5),s50=sma(c,50),r2=rsi(c,2),r3=rsi(c,3))
