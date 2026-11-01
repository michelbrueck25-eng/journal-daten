import sys,csv,bisect,datetime as dt,itertools,re
import numpy as np
sys.path.insert(0,'/home/claude/journal-daten/tests')
import eng
U=eng.load_all()
FX=[s for s in U if len(s)==6 and not s.startswith(('XAU','GOLD'))]
for s in U: U[s]['D']=[dt.datetime.utcfromtimestamp(t/1000).date() for t in U[s]['t']]; U[s]['A']=eng.atr(U[s])
CCY=['AUD','CAD','CHF','EUR','GBP','JPY','NZD','USD']
SPLIT=dt.date(2023,1,1)
def idx_on_or_after(s,d):
    k=bisect.bisect_left(U[s]['D'],d); return k if k<len(U[s]['D']) else None
def trade(s,L,d0,hold,stop_atr=2.0):
    """Einstieg Open des ersten Handelstags >= d0, Zeitausstieg Close nach hold Tagen, Stopp stop_atr*ATR, Kosten 1 Pip + 0.3 Pip/Tag"""
    m=U[s];i=idx_on_or_after(s,d0)
    if i is None or i<20 or i+hold>=len(m['c']) or np.isnan(m['A'][i-1]):return None
    e=m['o'][i];A=m['A'][i-1];risk=stop_atr*A;st=e-L*risk;P=eng.pip(s)
    r=None
    for j in range(i,i+hold):
        if (L>0 and m['l'][j]<=st) or (L<0 and m['h'][j]>=st): r=-1.0;jj=j;break
    if r is None: jj=i+hold-1;r=L*(m['c'][jj]-e)/risk
    days=(m['D'][jj]-m['D'][i]).days
    cost=(1.0+0.3*max(days,1))*P/risk
    return dict(date=m['D'][i].isoformat(),r=r-cost,days=max(days,1),sym=s,L=L,gross=r)
def pair(a,b):
    """Paar mit a lang, b kurz -> (symbol, L) oder None"""
    if a+b in U:return a+b,1
    if b+a in U:return b+a,-1
    return None
def summ(tr,name):
    if len(tr)<5:print(f'{name:50s} n={len(tr)}');return None
    r=np.array([x['r'] for x in tr]);g=np.array([x['gross'] for x in tr])
    dev=[x['r'] for x in tr if x['date']<SPLIT.isoformat()];tst=[x['r'] for x in tr if x['date']>=SPLIT.isoformat()]
    d0=min(x['date'] for x in tr);d1=max(x['date'] for x in tr)
    yrs=max((dt.date.fromisoformat(d1)-dt.date.fromisoformat(d0)).days/365.25,0.5)
    se=r.std(ddof=1)/np.sqrt(len(r))
    f=lambda v:(f'{np.mean(v):+.2f}({len(v)})' if len(v) else '-')
    print(f'{name:50s} n={len(r):4d} E_net={r.mean():+.3f} brutto={g.mean():+.3f} t={r.mean()/se:+.1f} wr={100*(r>0).mean():.0f}% R/J={r.sum()/yrs:+.1f} dev={f(dev)} test={f(tst)}')
    return dict(name=name,n=len(r),avg=float(r.mean()),gross=float(g.mean()),t=float(r.mean()/se),rj=float(r.sum()/yrs),dev=float(np.mean(dev)) if dev else None,test=float(np.mean(tst)) if tst else None)
# ---------- COT
cot={}
for r in csv.DictReader(open('/home/claude/journal-daten/cot.csv',encoding='utf-8')):
    if r['waehrung'] in CCY:
        cot.setdefault(r['waehrung'],{})[r['datum']]=dict(cn=int(r['comm_long'])-int(r['comm_short']),nn=int(r['noncomm_long'])-int(r['noncomm_short']),rn=int(r['nonrep_long'])-int(r['nonrep_short']))
dates=sorted(set.intersection(*[set(cot[c]) for c in CCY]))
def cot_scores(kind,k,norm=156):
    out={}
    for i,d in enumerate(dates):
        if i<max(k,26):continue
        sc={}
        for c in CCY:
            v=[cot[c][x][kind] for x in dates[max(0,i-norm+1):i+1]];rg=max(v)-min(v)
            if rg==0:continue
            sc[c]=(cot[c][d][kind]-cot[c][dates[i-k]][kind])/rg*100
        out[d]=sc
    return out
def run_cot(kind,k,sign,hold,topn,stop=2.0):
    tr=[]
    for d,sc in cot_scores(kind,k).items():
        d0=dt.date.fromisoformat(d)+dt.timedelta(days=6)   # Montag nach Freitags-Veroeffentlichung
        cand=[]
        for a,b in itertools.permutations(CCY,2):
            if a>b and False:continue
            p=pair(a,b)
            if p and a<b or (p and False):pass
        seen=set();ranked=[]
        for a,b in itertools.combinations(CCY,2):
            if a in sc and b in sc:ranked.append((abs(sc[a]-sc[b]),a,b,sc[a]-sc[b]))
        ranked.sort(reverse=True)
        for _,a,b,diff in ranked[:topn]:
            lng,sht=(a,b) if diff*sign>0 else (b,a)
            p=pair(lng,sht)
            if p:
                t=trade(p[0],p[1],d0,hold,stop)
                if t:tr.append(t)
    return tr
if __name__=='__main__':
    R=[]
    print('--- COT-Veränderung (Wochen k), Richtung +1=mit Veränderung, -1=dagegen')
    for kind in['cn','nn','rn']:
        for k in[1,2,4,8]:
            for sg in[1,-1]:
                for hold in[5,10,20]:
                    tr=run_cot(kind,k,sg,hold,3)
                    x=summ(tr,f'COT {kind} k={k} sg={sg:+d} hold={hold}')
                    if x:R.append(x)
    import json;json.dump(R,open('/tmp/fx/cot_chg.json','w'))
