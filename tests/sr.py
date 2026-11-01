import sys,datetime as dt,numpy as np
sys.path.insert(0,'/tmp/ix')
import lvl
M=lvl.M
def levels(m,i,A,w=3,look=150,tol=0.5,minT=2):
    h,l=m['h'],m['l'];pts=[]
    for k in range(max(w,i-look),i-w):
        if h[k]==max(h[k-w:k+w+1]):pts.append(h[k])
        if l[k]==min(l[k-w:k+w+1]):pts.append(l[k])
    pts=sorted(pts);out=[];cur=[]
    for p in pts:
        if cur and p-cur[0]>tol*A:
            if len(cur)>=minT:out.append((np.mean(cur),len(cur)))
            cur=[]
        cur.append(p)
    if len(cur)>=minT:out.append((np.mean(cur),len(cur)))
    return out
def run(kind,rr,minT=2,syms=None):
    out=[]
    for s,m in M.items():
        if syms and s not in syms:continue
        A=lvl.atr(m);c,o,h,l,D=m['c'],m['o'],m['h'],m['l'],m['D'];n=len(c);busy=-1;i=200
        for i in range(200,n-12):
            if i<=busy or np.isnan(A[i]):continue
            for Lv,cnt in levels(m,i,A[i],minT=minT):
                tl=0.3*A[i];L=0
                if kind=='bounce':
                    if l[i]<=Lv+tl and l[i]>=Lv-0.5*A[i] and c[i]>Lv and c[i]>o[i]:L=1;ref=min(l[i],Lv)
                    elif h[i]>=Lv-tl and h[i]<=Lv+0.5*A[i] and c[i]<Lv and c[i]<o[i]:L=-1;ref=max(h[i],Lv)
                else:   # Ausbruch und Retest: gestern Schluss über Niveau (+0.3 ATR), heute Berührung von oben und Schluss darüber
                    if c[i-1]>Lv+0.3*A[i] and c[i-2]<=Lv+0.1*A[i] and False:pass
                    if c[i-3]<Lv<c[i-1] and l[i]<=Lv+tl and c[i]>Lv and c[i]>o[i]:L=1;ref=min(l[i],Lv)
                    elif c[i-3]>Lv>c[i-1] and h[i]>=Lv-tl and c[i]<Lv and c[i]<o[i]:L=-1;ref=max(h[i],Lv)
                if L==0:continue
                r=lvl.trade(m,A[i],i,L,ref,rr)
                if r:out.append((r[0],s,r[1]));busy=r[2];break
    return out
if __name__=='__main__':
    for kind in ('bounce','retest'):
        for minT in (2,3):
            for rr in (1.5,2.0,3.0):
                x=lvl.st(run(kind,rr,minT))
                if x:print(f'S/R {kind:7} Berührungen≥{minT} RR{rr} n{x[0]:5} E{x[1]:+.3f} dev{x[2]:+.3f} test{x[3]:+.3f} (n{x[4]}) Win{x[5]*100:.0f}%',flush=True)
