import sys,csv,bisect,datetime as dt,numpy as np
sys.path.insert(0,'/tmp/ix')
import lvl
M=lvl.M
cot={}
for r in csv.DictReader(open('/home/claude/journal-daten/cot.csv',encoding='utf-8')):
    try:cot.setdefault(r['waehrung'],[]).append((r['datum'],int(r['comm_long'])-int(r['comm_short'])))
    except:pass
for k in cot:cot[k].sort()
CK={'GOLD':'GOLD','SPX':'ES','NDX':'NQ','SILBER':'SILBER','OEL':'OEL'}
def ci(cur,date,n=26):
    v=cot.get(cur,[]);ds=[x[0] for x in v];k=bisect.bisect_right(ds,date)-1
    if k<n-1:return None
    w=[x[1] for x in v[k-n+1:k+1]]
    return None if max(w)==min(w) else 100*(w[-1]-min(w))/(max(w)-min(w))
def cotdir(s,date,thr):
    d=date.isoformat()
    # Meldung (Dienstag) ist ab Freitag bekannt: 4 Tage Verzögerung
    d=(date-dt.timedelta(days=4)).isoformat()
    if s in CK:
        x=ci(CK[s],d)
        if x is None:return 0
        return 1 if x>=100-thr else (-1 if x<=thr else 0)
    if len(s)==6 and not s.startswith('GOLD'):
        a,b=ci(s[:3],d),ci(s[3:],d)
        if a is None or b is None:return 0
        return 1 if a-b>=thr+10 else (-1 if b-a>=thr+10 else 0)
    return 0
def pivots(m,w=3):
    h,l=m['h'],m['l'];n=len(h);ph=np.full(n,np.nan);pl=np.full(n,np.nan);ih=np.full(n,-1);il=np.full(n,-1);ch=cl=np.nan;chi=cli=-1
    for i in range(n):
        k=i-w
        if k>=w:
            if h[k]==max(h[k-w:k+w+1]):ch=h[k];chi=k
            if l[k]==min(l[k-w:k+w+1]):cl=l[k];cli=k
        ph[i]=ch;pl[i]=cl;ih[i]=chi;il[i]=cli
    return ph,pl,ih,il
def finish(m,A,i0,e_idx,e,st,L,tgt,maxd=15,entry_at_open=True):
    n=len(m['c']);risk=abs(e-st)
    if risk<=0.3*A[i0] or risk>5*A[i0]:return None
    tp=e+L*tgt*risk;j=e_idx
    while j<n and j<=e_idx+maxd:
        lo,hi=m['l'][j],m['h'][j]
        if (j>e_idx or entry_at_open) and ((L>0 and lo<=st) or (L<0 and hi>=st)):r=-1.0;break
        if (L>0 and hi>=tp) or (L<0 and lo<=tp):r=tgt;break
        j+=1
    else:
        j=min(j,n-1);r=L*(m['c'][j]-e)/risk
    j=min(j,n-1);days=(m['D'][j]-m['D'][e_idx]).days
    return m['D'][e_idx],r-lvl.cost(m,A[i0],risk,days),j
def scan(mode,thr=25,tgt=2.0,fib=0.7,syms=None):
    out=[]
    for s,m in M.items():
        if syms and s not in syms:continue
        if not(s in CK or (len(s)==6 and m['fx'])):continue
        A=lvl.atr(m);c,o,h,l,D=m['c'],m['o'],m['h'],m['l'],m['D'];n=len(c);ph,pl,ih,il=pivots(m);busy=-1
        for i in range(260,n-25):
            if i<=busy or np.isnan(A[i]) or D[i]<dt.date(2017,8,1):continue
            L=cotdir(s,D[i],thr)
            if L==0:continue
            if mode=='open':
                e=o[i+1];st=(min(l[i-2:i+1]) if L>0 else max(h[i-2:i+1]))-L*0.2*A[i]
                r=finish(m,A,i,i+1,e,st,L,tgt)
                if r:out.append((r[0],s,r[1]));busy=r[2]
                continue
            # Strukturbruch (Tagesschluss über letztes bestätigtes Pivot-Hoch/-Tief)
            k1=None
            for k in range(i+1,i+11):
                lvl_=ph[k-1] if L>0 else pl[k-1]
                if not np.isnan(lvl_) and ((L>0 and c[k]>lvl_) or (L<0 and c[k]<lvl_)):k1=k;level=lvl_;break
            if k1 is None:continue
            sw=pl[k1] if L>0 else ph[k1]
            if np.isnan(sw):continue
            if mode.startswith('fib'):
                f=float(mode[3:])/100;ext=h[k1] if L>0 else l[k1]
                for q in range(k1+1,k1+9):
                    if (L>0 and l[q]<sw) or (L<0 and h[q]>sw):break
                    E=ext-L*f*(abs(ext-sw))
                    if (L>0 and l[q]<=E) or (L<0 and h[q]>=E):
                        r=finish(m,A,i,q,E,sw-L*0.2*A[i],L,tgt,entry_at_open=False)
                        if r:out.append((r[0],s,r[1]));busy=r[2]
                        break
                    ext=max(ext,h[q]) if L>0 else min(ext,l[q])
            elif mode=='retest':
                for q in range(k1+1,k1+9):
                    if (L>0 and l[q]<=level+0.2*A[i] and c[q]>level) or (L<0 and h[q]>=level-0.2*A[i] and c[q]<level):
                        e=o[q+1];st=(min(l[q],level) if L>0 else max(h[q],level))-L*0.2*A[i]
                        r=finish(m,A,i,q+1,e,st,L,tgt)
                        if r:out.append((r[0],s,r[1]));busy=r[2]
                        break
            elif mode=='double':
                # zweiter Bruch nach Rücksetzer
                for q in range(k1+2,k1+14):
                    lvl2=ph[q-1] if L>0 else pl[q-1]
                    if ih[q-1]>k1 if L>0 else il[q-1]>k1:
                        if (L>0 and c[q]>lvl2) or (L<0 and c[q]<lvl2):
                            sw2=pl[q] if L>0 else ph[q]
                            e=o[q+1];r=finish(m,A,i,q+1,e,sw2-L*0.2*A[i],L,tgt)
                            if r:out.append((r[0],s,r[1]));busy=r[2]
                            break
            elif mode=='dbl_retest':
                pass
    return out
st=lvl.st
if __name__=='__main__':
    for thr in (25,15):
      for mode in ('open','fib50','fib62','fib70','fib79','retest','double'):
        for tgt in (2.0,3.0):
            x=st(scan(mode,thr,tgt))
            if x:print(f'COT {thr:2} {mode:7} {tgt}R n{x[0]:5} E{x[1]:+.3f} dev{x[2]:+.3f} test{x[3]:+.3f} (n{x[4]}) Win{x[5]*100:.0f}%',flush=True)
