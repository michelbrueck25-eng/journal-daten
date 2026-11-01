import sys,csv,datetime as dt,numpy as np
sys.path.insert(0,'/home/claude/journal-daten/tests')
import eng
U=eng.load_all()
r=list(csv.reader(open('/mnt/user-data/uploads/Downloads/fredgraph.csv')));h=r[0]
CUR=['USD','EUR','GBP','JPY','CHF','AUD','CAD','NZD'];col={c:h.index('IR3TIB01%sM156N'%c[:2] if c not in('EUR',) else 'IR3TIB01EZM156N') for c in CUR}
col['USD']=h.index('IR3TIB01USM156N');col['JPY']=h.index('IR3TIB01JPM156N');col['CHF']=h.index('IR3TIB01CHM156N');col['AUD']=h.index('IR3TIB01AUM156N');col['CAD']=h.index('IR3TIB01CAM156N');col['NZD']=h.index('IR3TIB01NZM156N');col['GBP']=h.index('IR3TIB01GBM156N')
rate={c:{} for c in CUR};last={c:None for c in CUR}
for row in r[1:]:
    d=dt.date.fromisoformat(row[0])
    if d.year<2007:continue
    for c in CUR:
        v=row[col[c]]
        if v not in('','.'):last[c]=float(v)
        rate[c][(d.year,d.month)]=last[c]
def rt(c,d,lag=2,back=0):
    y,m=d.year,d.month-lag-back
    while m<=0:m+=12;y-=1
    return rate[c].get((y,m))
INV=1
def run(thr,mode,stopm=3.0,filt=None,back=3):
    out=[]
    for s,u in U.items():
        if len(s)!=6 or s[:3] not in CUR or s[3:] not in CUR:continue
        t=u['t'];o,hh,l,c=u['o'],u['h'],u['l'],u['c'];A=eng.atr(u);pp=eng.pip(s)
        D=[dt.datetime.fromtimestamp(x/1000,dt.timezone.utc).date() for x in t]
        sma=np.convolve(c,np.ones(50)/50,'valid');sma=np.r_[np.full(49,np.nan),sma]
        i=60
        while i<len(c)-25:
            if D[i+1].month!=D[i].month:
                a,b=s[:3],s[3:];d0=D[i]
                ra,rb,ra0,rb0=rt(a,d0),rt(b,d0),rt(a,d0,back=back),rt(b,d0,back=back)
                if None in(ra,rb,ra0,rb0) or np.isnan(A[i]):i+=1;continue
                diff=ra-rb;chg=diff-(ra0-rb0)
                x=diff if mode=='carry' else chg
                if abs(x)>=thr:
                    L=(1 if x>0 else -1)*INV
                    if filt=='trend' and not((c[i]>sma[i])==(L>0)):i+=1;continue
                    e=o[i+1];risk=stopm*A[i];st=e-L*risk;j=i+1;res=None
                    while j<len(c) and j<i+25:
                        if (L>0 and l[j]<=st) or (L<0 and hh[j]>=st):res=-1.0;break
                        if D[j].month!=D[i+1].month and j>i+1:res=L*(o[j]-e)/risk;break
                        j+=1
                    if res is None:i+=1;continue
                    days=(D[min(j,len(D)-1)]-D[i+1]).days;res-=(eng.SPREAD_PIPS*pp+0.3*pp*days)/risk
                    out.append((D[i+1],s,res,j-i));i=j
                    continue
            i+=1
    return out
def st(tr):
    if not tr:return None
    R=np.array([x[2] for x in tr]);dv=[x[2] for x in tr if x[0]<dt.date(2023,1,1)];te=[x[2] for x in tr if x[0]>=dt.date(2023,1,1)]
    return len(R),R.mean(),np.mean(dv),np.mean(te) if te else float('nan'),len(te)
for mode,thrs in (('carry',(0.5,1,2,3)),('chg',(0.25,0.5,1))):
    for thr in thrs:
        for f in (None,'trend'):
            for sm in (2,3):
                s=st(run(thr,mode,sm,f,3))
                if s:print(f'{mode:5} thr{thr:4} {str(f):6} stop{sm}: n{s[0]:5} E{s[1]:+.3f} dev{s[2]:+.3f} test{s[3]:+.3f} (n{s[4]})')
