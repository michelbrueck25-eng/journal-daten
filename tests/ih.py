import sys,json,glob,os,datetime as dt,numpy as np
sys.path.insert(0,'/tmp/ix');sys.path.insert(0,'/home/claude/journal-daten/tests')
import eng,idx
H4={}
for f in sorted(glob.glob('/home/claude/journal-privat/marktdaten/*_4H.json')):
    s=os.path.basename(f).split('_')[0];r=np.array(json.load(open(f))['rows'],float)
    H4[s]=dict(T=r[:,0],o=r[:,1],h=r[:,2],l=r[:,3],c=r[:,4],hr=np.array([dt.datetime.fromtimestamp(x/1000,dt.timezone.utc).hour for x in r[:,0]]),fx=(s!='GOLD'),pp=eng.pip(s))
def atr(m,n=14):return idx.atr(m['h'],m['l'],m['c'],n)
def ema(x,n):
    a=2/(n+1);o=np.empty(len(x));o[0]=x[0]
    for i in range(1,len(x)):o[i]=a*x[i]+(1-a)*o[i-1]
    return o
def cost(m,A,risk,bars):
    d=bars*4/24
    return ((1.0*m['pp']+0.3*m['pp']*d) if m['fx'] else (0.05+0.012*d)*A)/risk
def fin(m,A,i,L,e_idx,e,st,rr,maxb=18):
    n=len(m['c']);risk=abs(e-st)
    if risk<0.4*A[i] or risk>4*A[i]:return None
    tp=e+L*rr*risk;j=e_idx
    while j<n and j<=e_idx+maxb:
        if (L>0 and m['l'][j]<=st) or (L<0 and m['h'][j]>=st):r=-1.0;break
        if (L>0 and m['h'][j]>=tp) or (L<0 and m['l'][j]<=tp):r=rr;break
        j+=1
    else:
        j=min(j,n-1);r=L*(m['c'][j]-e)/risk
    j=min(j,n-1);return (dt.datetime.fromtimestamp(m['T'][e_idx]/1000,dt.timezone.utc).date(),r-cost(m,A[i],risk,j-e_idx),j)
SES={'alle':None,'London':{8,12},'NY':{12,16},'ohneAsien':{8,12,16}}
def run(kind,rr,ses='alle',stopm=1.5):
    out=[];S=SES[ses]
    for s,m in H4.items():
        A=atr(m);c,o,h,l=m['c'],m['o'],m['h'],m['l'];n=len(c);e1,e2=ema(c,20),ema(c,50);busy=-1
        hi20=np.array([np.nan]*n);lo20=hi20.copy()
        for i in range(21,n):hi20[i]=h[i-20:i].max();lo20[i]=l[i-20:i].min()
        for i in range(60,n-20):
            if i<=busy or np.isnan(A[i]):continue
            if S and m['hr'][i+1] not in S:continue
            L=0
            if kind=='cross':
                if e1[i-1]<=e2[i-1] and e1[i]>e2[i]:L=1
                elif e1[i-1]>=e2[i-1] and e1[i]<e2[i]:L=-1
            elif kind=='donch':
                if c[i]>hi20[i]:L=1
                elif c[i]<lo20[i]:L=-1
            elif kind=='pullback':   # Trend EMA50, Rücksetzer an EMA20 mit Umkehrkerze
                up=e1[i]>e2[i] and c[i]>e2[i]
                dn=e1[i]<e2[i] and c[i]<e2[i]
                if up and l[i]<=e1[i] and c[i]>o[i] and c[i]>e1[i]:L=1
                elif dn and h[i]>=e1[i] and c[i]<o[i] and c[i]<e1[i]:L=-1
            elif kind=='open':   # Tageseröffnung (0 UTC) Reaktion: Kerze berührt Open und schließt zurück
                if m['hr'][i]==0:continue
                k=i
                while k>0 and m['hr'][k]!=0:k-=1
                dopen=o[k]
                if l[i]<=dopen<c[i] and c[i]>o[i] and c[i-1]>dopen:L=1
                elif h[i]>=dopen>c[i] and c[i]<o[i] and c[i-1]<dopen:L=-1
            if L==0:continue
            e=o[i+1];st=e-L*stopm*A[i]
            r=fin(m,A,i,L,i+1,e,st,rr)
            if r:out.append((r[0],s,r[1]));busy=r[2]
    return out
def st(tr):
    if not tr:return None
    R=np.array([x[2] for x in tr]);h=len(R)//2
    return len(R),R.mean(),R[:h].mean(),R[h:].mean(),np.mean(R>0)
if __name__=='__main__':
    for kind in ('cross','donch','pullback','open'):
        for ses in ('alle','London','NY'):
            for rr in (1.0,1.5,2.0,3.0):
                x=st(run(kind,rr,ses))
                if x and x[0]>=60:print(f'{kind:8} {ses:6} RR{rr} n{x[0]:5} E{x[1]:+.3f} 1.Hälfte{x[2]:+.3f} 2.Hälfte{x[3]:+.3f} Win{x[4]*100:.0f}%',flush=True)
