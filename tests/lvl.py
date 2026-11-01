import sys,datetime as dt,numpy as np,collections
sys.path.insert(0,'/home/claude/journal-daten/tests');sys.path.insert(0,'/tmp/ix')
import eng,idx
U=eng.load_all()
def mk(t,o,h,l,c,fx,pp):
    D=[dt.datetime.fromtimestamp(x/1000,dt.timezone.utc).date() for x in t]
    return dict(D=D,o=o,h=h,l=l,c=c,fx=fx,pp=pp)
M={}
for s,u in U.items():
    M[s]=mk(u['t'],u['o'],u['h'],u['l'],u['c'],len(s)==6 and s!='GOLD',eng.pip(s))
for s in ['DAX','SPX','NDX','NKX','FTSE','SILBER','OEL']:
    d,o,h,l,c=idx.load(s);M[s]=dict(D=d,o=o,h=h,l=l,c=c,fx=False,pp=0)
def atr(m):return idx.atr(m['h'],m['l'],m['c'])
PC={}
def profile(m,i,n=250,bins=60):
    k=(id(m),i)
    if k not in PC:PC[k]=_profile(m,i,n,bins)
    return PC[k]
def _profile(m,i,n=250,bins=60):
    lo=m['l'][i-n:i].min();hi=m['h'][i-n:i].max()
    if hi<=lo:return None
    ed=np.linspace(lo,hi,bins+1);cnt=np.zeros(bins)
    A_=np.clip(np.searchsorted(ed,m['l'][i-n:i],'right')-1,0,bins-1);B_=np.clip(np.searchsorted(ed,m['h'][i-n:i],'right')-1,0,bins-1)
    for a,b in zip(A_,B_):cnt[a:b+1]+=1.0/(b-a+1)
    pk=int(cnt.argmax());tot=cnt.sum();acc=cnt[pk];a=b=pk
    while acc<0.7*tot:
        up=cnt[b+1] if b+1<bins else -1;dn=cnt[a-1] if a-1>=0 else -1
        if up>=dn:b+=1;acc+=up
        else:a-=1;acc+=dn
    return ed[a],(ed[pk]+ed[pk+1])/2,ed[b+1]
def cost(m,A,risk,days):
    return ((1.0*m['pp']+0.3*m['pp']*days) if m['fx'] else (0.05+0.012*days)*A)/risk
def trade(m,A,i,L,ref,tgt,maxd=10):  # ref=Stopp-Referenz
    n=len(m['c']);e=m['o'][i+1];st=ref-L*0.2*A;risk=abs(e-st)
    if risk<=0.3*A or risk>4*A:return None
    tp=e+L*tgt*risk;j=i+1
    while j<n and j<=i+maxd:
        if (L>0 and m['l'][j]<=st) or (L<0 and m['h'][j]>=st):r=-1.0;break
        if (L>0 and m['h'][j]>=tp) or (L<0 and m['l'][j]<=tp):r=tgt;break
        j+=1
    else:
        if j>=n:return None
        j=min(j,n-1);r=L*(m['c'][j]-e)/risk
    j=min(j,n-1);days=(m['D'][j]-m['D'][i+1]).days
    return (m['D'][i+1],r-cost(m,A,risk,days),j)
def scan(kind,tol=0.25,tgt=2.0,vaf=None,mode='plain'):
    out=[]
    for s,m in M.items():
        o,h,l,c,D=m['o'],m['h'],m['l'],m['c'],m['D'];A=atr(m);n=len(c);i=260;busy=-1
        yo=mo=wo=None;
        # Eröffnungen
        yopen={};mopen={};wopen={}
        for k in range(n):
            yopen.setdefault(D[k].year,o[k]);mopen.setdefault((D[k].year,D[k].month),o[k]);wk=D[k].isocalendar()[:2];wopen.setdefault(wk,o[k])
        for i in range(260,n-12):
            if i<=busy or np.isnan(A[i]):continue
            lv=[]
            if kind in('VAH','VAL','POC','VA'):
                P=profile(m,i)
                if P is None:continue
                val,poc,vah=P
                if kind in('VAH','VA'):lv.append((vah,-1))
                if kind in('VAL','VA'):lv.append((val,1))
                if kind=='POC':lv+= [(poc,1),(poc,-1)]
            elif kind=='Y':lv=[(yopen[D[i].year],1),(yopen[D[i].year],-1)]
            elif kind=='M':lv=[(mopen[(D[i].year,D[i].month)],1),(mopen[(D[i].year,D[i].month)],-1)]
            elif kind=='W':lv=[(wopen[D[i].isocalendar()[:2]],1),(wopen[D[i].isocalendar()[:2]],-1)]
            for Lv,L in lv:
                tl=tol*A[i]
                if L>0 and l[i]<=Lv+tl and c[i]>Lv and c[i]>o[i] and c[i-1]>Lv-tl:ok=True;ref=l[i]
                elif L<0 and h[i]>=Lv-tl and c[i]<Lv and c[i]<o[i] and c[i-1]<Lv+tl:ok=True;ref=h[i]
                else:continue
                if vaf=='yo_in_va':
                    P=profile(m,i);yo_=yopen[D[i].year]
                    if P is None or not(P[0]<=yo_<=P[2]):continue
                if vaf=='trend':
                    sm=np.mean(c[i-50:i]);
                    if (L>0)!=(c[i]>sm):continue
                if mode=='bos':
                    r=bos(m,A,i,L,ref,tgt)
                else:r=trade(m,A[i],i,L,ref,tgt)
                if r:out.append((r[0],s,r[1]));busy=r[2];break
    return out
def bos(m,A,i,L,ref,tgt):
    # Strukturbruch (Tagesschluss über/unter Hoch/Tief der letzten 3 Kerzen) binnen 5 Tagen, dann Fib-Retest 50 %
    h,l,c,o=m['h'],m['l'],m['c'],m['o'];n=len(c)
    lvl=(max(h[i-2:i+1]) if L>0 else min(l[i-2:i+1]))
    for k in range(i+1,min(i+6,n-8)):
        if (L>0 and c[k]>lvl) or (L<0 and c[k]<lvl):
            ext=max(h[i:k+1]) if L>0 else min(l[i:k+1]);fib=ext-L*0.5*(ext-ref) if True else 0
            for q in range(k+1,min(k+6,n-8)):
                if (L>0 and l[q]<=fib) or (L<0 and h[q]>=fib):
                    # Einstieg am Fib-Limit
                    e=fib;st=ref-L*0.2*A[i];risk=abs(e-st)
                    if risk<=0.3*A[i] or risk>4*A[i]:return None
                    tp=e+L*tgt*risk;j=q
                    while j<n and j<=q+10:
                        if (L>0 and l[j]<=st and j>q) or (L<0 and h[j]>=st and j>q):r=-1.0;break
                        if (L>0 and h[j]>=tp) or (L<0 and l[j]<=tp):r=tgt;break
                        j+=1
                    else:
                        j=min(j,n-1);r=L*(c[j]-e)/risk
                    j=min(j,n-1);days=(m['D'][j]-m['D'][q]).days
                    return (m['D'][q],r-cost(m,A[i],risk,days),j)
            return None
    return None
def st(tr):
    if not tr:return None
    R=np.array([x[2] for x in tr]);dv=[x[2] for x in tr if x[0]<dt.date(2023,1,1)];te=[x[2] for x in tr if x[0]>=dt.date(2023,1,1)]
    return len(R),R.mean(),np.mean(dv) if dv else np.nan,np.mean(te) if te else np.nan,len(te),np.mean(R>0)
if __name__=='__main__':
    import pickle
    res={}
    for kind in ('VAH','VAL','VA','POC','Y','M','W'):
        for mode in ('plain','bos'):
            for vaf in (None,'trend'):
                tr=scan(kind,mode=mode,vaf=vaf);res[(kind,mode,vaf)]=tr;x=st(tr)
                if x:print(f'{kind:4} {mode:5} {str(vaf):6} n{x[0]:5} E{x[1]:+.3f} dev{x[2]:+.3f} test{x[3]:+.3f} (n{x[4]}) Win{x[5]*100:.0f}%',flush=True)
    pickle.dump(res,open('/tmp/ix/lvl.pkl','wb'))
