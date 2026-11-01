import sys,datetime as dt,numpy as np,bisect
sys.path.insert(0,'/tmp/ix')
import lvl,cotstr
from lvl import M,st
orig=cotstr.cotdir
NF=['GOLD','SPX','NDX','SILBER','OEL']
FX=[s for s,m in M.items() if m['fx']]
def pr(tag,tr):
    x=st(tr)
    if x:print(f'{tag:44} n{x[0]:5} E{x[1]:+.3f} dev{x[2]:+.3f} test{x[3]:+.3f} (n{x[4]}) Win{x[5]*100:.0f}%',flush=True)
# H1/H2: COT + fib79 nach Gruppe
for grp,sy in (('FX',FX),('Gold/Indizes/Silber/Öl',NF),('nur Rohstoffe',['GOLD','SILBER','OEL']),('nur Indizes',['SPX','NDX'])):
    for thr in (15,25):
        pr(f'H1/2 COT {thr} fib79 2R {grp}',cotstr.scan('fib79',thr,2.0,syms=sy))
        pr(f'H1   COT {thr} offen  2R {grp}',cotstr.scan('open',thr,2.0,syms=sy))
# H2 Stabilität: Ziel/Haltedauer
for tgt in (1.5,2.0,2.5,3.0):
    pr(f'H2 fib79 thr20 tgt{tgt} alle',cotstr.scan('fib79',20,tgt))
# H3: COT-Veränderung 8 Wochen
def chg(s,date,thr,w=8):
    d=(date-dt.timedelta(days=4)).isoformat();d0=(date-dt.timedelta(days=4+7*w)).isoformat()
    def g(cur):
        a,b=cotstr.ci(cur,d),cotstr.ci(cur,d0);return None if a is None or b is None else a-b
    if s in cotstr.CK:
        x=g(cotstr.CK[s])
    elif len(s)==6 and s!='GOLD':
        a,b=g(s[:3]),g(s[3:]);x=None if a is None or b is None else a-b
    else:return 0
    if x is None:return 0
    return 1 if x>=thr*2 else (-1 if x<=-thr*2 else 0)
cotstr.cotdir=chg
for thr in (25,35):
    for mode in ('open','fib79','fib62'):
        pr(f'H3 COT-Veränderung 8W {thr*2} {mode} 2R alle',cotstr.scan(mode,thr,2.0))
cotstr.cotdir=orig
# H5: Risiko-Stimmung: Index über SMA50 -> long Yen-Kreuze (XXXJPY), Pullback-Einstieg
def idxtrend():
    out={}
    for s in ('SPX','NDX','DAX'):
        m=M[s];c=m['c'];sm=np.convolve(c,np.ones(50)/50,'valid');sm=np.r_[np.full(49,np.nan),sm]
        out[s]={m['D'][i]:(c[i]>sm[i] and sm[i]>sm[i-10]) for i in range(60,len(c))}
    return out
IT=idxtrend()
def risk(pairs,short=False,H=15,stopm=3.0,pull=False):
    out=[]
    for s in pairs:
        m=M[s];A=lvl.atr(m);c,o,h,l,D=m['c'],m['o'],m['h'],m['l'],m['D'];n=len(c);i=60;busy=-1
        for i in range(260,n-H-2):
            if i<=busy or np.isnan(A[i]):continue
            on=all(IT[k].get(D[i],False) for k in ('SPX','NDX'))
            off=all((not IT[k].get(D[i],True)) for k in ('SPX','NDX'))
            if not (on or (short and off)):continue
            L=1 if on else -1
            if pull and not(((c[i]<c[i-3]) if L>0 else (c[i]>c[i-3]))):continue
            e=o[i+1];risk_=stopm*A[i];stp=e-L*risk_;j=i+1;r=None
            while j<n and j<=i+H:
                if (L>0 and l[j]<=stp) or (L<0 and h[j]>=stp):r=-1.0;break
                j+=1
            else:
                j=min(j,n-1);r=L*(c[j]-e)/risk_
            j=min(j,n-1);r-=lvl.cost(m,A[i],risk_,(D[j]-D[i+1]).days)
            out.append((D[i+1],s,r));busy=j
    return out
JPY=[s for s in FX if s.endswith('JPY') and s!='USDJPY']
for H in (10,20):
    pr(f'H5 Risiko an: long Yen-Kreuze H{H}',risk(JPY,H=H))
    pr(f'H5 dito mit Rücksetzer H{H}',risk(JPY,H=H,pull=True))
    pr(f'H5 +Risiko aus: short Yen-Kreuze H{H}',risk(JPY,short=True,H=H))
# H7: Index Q4 Long
def saison(months,syms,trend=True,stopm=3.0):
    out=[]
    for s in syms:
        m=M[s];A=lvl.atr(m);c,o,l,D=m['c'],m['o'],m['l'],m['D'];n=len(c);i=250;busy=-1
        for i in range(250,n-3):
            if i<=busy or D[i].month not in months or D[i-1].month in months:continue
            if trend and c[i]<np.mean(c[i-200:i]):continue
            e=o[i+1];risk_=stopm*A[i];stp=e-risk_;j=i+1
            while j<n-1 and D[j].month in months and l[j]>stp:j+=1
            r=-1.0 if l[min(j,n-1)]<=stp else (c[min(j,n-1)]-e)/risk_
            r-=lvl.cost(m,A[i],risk_,(D[min(j,n-1)]-D[i+1]).days);out.append((D[i+1],s,r));busy=j
    return out
IDXS=['SPX','NDX','DAX','NKX','FTSE']
pr('H7 Index Okt-Dez long (Trend)',saison({10,11,12},IDXS))
pr('H7 Index Okt-Dez long (ohne Trend)',saison({10,11,12},IDXS,False))
pr('H7 Index Nov-Apr long (Trend)',saison({11,12,1,2,3,4},IDXS))
pr('H6 Gold Dez-Jan long',saison({12,1},['GOLD'],False))
# H9: Monatsende-Umkehr
def monatsende(thr=2.5,H=4,stopm=2.5,syms=FX,fade=True):
    out=[]
    for s in syms:
        m=M[s];A=lvl.atr(m);c,o,h,l,D=m['c'],m['o'],m['h'],m['l'],m['D'];n=len(c)
        for i in range(260,n-H-2):
            nxt=[k for k in range(i+1,min(i+8,n)) if D[k].month!=D[i].month]
            if not nxt or nxt[0]-i>3 or D[i-1].month!=D[i].month:continue
            if nxt[0]-i!=3 and False:continue
            if nxt[0]-i!=3:continue   # drittletzter Handelstag
            z=(c[i]-c[i-21])/A[i]
            if abs(z)<thr:continue
            L=(-1 if z>0 else 1)*(1 if fade else -1);e=o[i+1];risk_=stopm*A[i];stp=e-L*risk_;j=i+1;r=None
            while j<=i+H and j<n:
                if (L>0 and l[j]<=stp) or (L<0 and h[j]>=stp):r=-1.0;break
                j+=1
            else:
                j=min(j,n-1);r=L*(c[j]-e)/risk_
            j=min(j,n-1);r-=lvl.cost(m,A[i],risk_,(D[j]-D[i+1]).days);out.append((D[i+1],s,r))
    return out
for thr in (1.5,2.5,3.5):
    pr(f'H9 Monatsende fade 21T≥{thr} ATR',monatsende(thr))
    pr(f'H9 Monatsende folgen 21T≥{thr} ATR',monatsende(thr,fade=False))
