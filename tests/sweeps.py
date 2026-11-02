import warnings,sys,os,json,glob,datetime as dt,bisect
warnings.filterwarnings('ignore')
import numpy as np
HOME='/home/claude/journal-privat'
def pip(s): return 0.01 if s.endswith('JPY') else 0.0001
SYMS=sorted(os.path.basename(f).split('_')[0] for f in glob.glob(f'{HOME}/marktdaten/*_4H.json'))
SYMS=[s for s in SYMS if len(s)==6 and not s.startswith(('XAU','GOLD'))]
def load(s,tf):
    a=np.array(json.load(open(f'{HOME}/marktdaten/{s}_{tf}.json'))['rows'],float)
    return dict(t=a[:,0],o=a[:,1],h=a[:,2],l=a[:,3],c=a[:,4])
def atr(d,n=14):
    h,l,c=d['h'],d['l'],d['c'];pc=np.r_[c[0],c[:-1]];tr=np.maximum(h-l,np.maximum(abs(h-pc),abs(l-pc)));o=np.full(len(c),np.nan);cs=np.cumsum(tr);o[n:]=(cs[n:]-cs[:-n])/n;return o
def sim(d,i,L,entry,stop,tgt,maxb,s):
    """Einstieg zum Open der Kerze i; Stopp zuerst bei Konflikt; Zeitausstieg Close; Kosten 1 Pip + 0.2 Pip Slippage"""
    risk=abs(entry-stop)
    if risk<=0 or i>=len(d['c']):return None
    tp=entry+L*tgt*risk;cost=(1.2*pip(s))/risk
    for j in range(i,min(i+maxb,len(d['c']))):
        hs=d['l'][j]<=stop if L>0 else d['h'][j]>=stop
        ht=d['h'][j]>=tp if L>0 else d['l'][j]<=tp
        if hs:return -1-cost,j-i
        if ht:return tgt-cost,j-i
    j=min(i+maxb,len(d['c']))-1
    return L*(d['c'][j]-entry)/risk-cost,j-i
def hr(t):return int(dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).hour)
def day(t):return dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).date()
# ---------------- 4H-Sessionen
def run4h(level,tgt,maxb=6,minr=0.3,maxr=3.0,trend=False):
    out=[]
    for s in SYMS:
        d=load(s,'4H');A=atr(d);n=len(d['c']);days={}
        D=[day(t) for t in d['t']];B=[hr(t)//4 for t in d['t']]
        for i in range(n):days.setdefault(D[i],[]).append(i)
        keys=sorted(days)
        dl={}  # Tagesdaten
        for k in keys:
            ix=days[k];dl[k]=dict(asia=[i for i in ix if B[i] in(0,1)],lon=[i for i in ix if B[i] in(2,3)],ny=[i for i in ix if B[i] in(3,4)],all=ix)
        dd=load(s,'D')
        for ki,k in enumerate(keys):
            if ki<3:continue
            cur=dl[k];prev=dl[keys[ki-1]]
            # Niveaus
            if level=='asia' and len(cur['asia'])==2:
                H=max(d['h'][i] for i in cur['asia']);Lo=min(d['l'][i] for i in cur['asia']);win=[i for i in cur['all'] if B[i] in(2,3,4)]
            elif level=='pdhl' and prev['all']:
                H=max(d['h'][i] for i in prev['all']);Lo=min(d['l'][i] for i in prev['all']);win=[i for i in cur['all'] if B[i] in(1,2,3,4)]
            elif level=='prevny' and prev['ny']:
                H=max(d['h'][i] for i in prev['ny']);Lo=min(d['l'][i] for i in prev['ny']);win=[i for i in cur['all'] if B[i] in(0,1,2)]
            elif level=='london' and len(cur['lon'])==2:
                H=max(d['h'][i] for i in cur['lon']);Lo=min(d['l'][i] for i in cur['lon']);win=[i for i in cur['all'] if B[i]==4]
            elif level=='fri' and k.weekday()==0:
                # Freitag davor
                fk=[x for x in keys[:ki] if x.weekday()==4][-1:] 
                if not fk or (k-fk[0]).days>4:continue
                f=dl[fk[0]]['all'];H=max(d['h'][i] for i in f);Lo=min(d['l'][i] for i in f);win=[i for i in cur['all'] if B[i] in(1,2,3,4)]
            elif level=='pwhl' and k.weekday() in(1,2,3,4):
                wk=[x for x in keys[:ki] if x.isocalendar()[1]!=k.isocalendar()[1] and x.isocalendar()[0]<=k.isocalendar()[0]]
                if not wk:continue
                lw=[x for x in wk if x.isocalendar()[1]==wk[-1].isocalendar()[1] and x.isocalendar()[0]==wk[-1].isocalendar()[0]]
                f=[i for x in lw for i in dl[x]['all']];H=max(d['h'][i] for i in f);Lo=min(d['l'][i] for i in f);win=[i for i in cur['all'] if B[i] in(1,2,3,4)]
            else:continue
            done=False
            for i in win:
                if done or i+1>=n or np.isnan(A[i]):continue
                for L,lvl,sw in((-1,H,d['h'][i]>H and d['c'][i]<H),(1,Lo,d['l'][i]<Lo and d['c'][i]>Lo)):
                    if not sw:continue
                    stop=d['h'][i] if L<0 else d['l'][i];entry=d['o'][i+1];risk=abs(entry-stop)
                    if risk<minr*A[i] or risk>maxr*A[i] or (stop-entry)*L>0:continue
                    r=sim(d,i+1,L,entry,stop,tgt,maxb,s)
                    if r:out.append(dict(s=s,d=str(D[i]),L=L,r=r[0],b=r[1]));done=True;break
    return out
def rep(tr,name,split=None):
    if len(tr)<20:print(f'{name:55s} n={len(tr)}');return None
    r=np.array([x['r'] for x in tr]);ds=sorted(x['d'] for x in tr);cut=split or ds[int(len(ds)*.6)]
    a=[x['r'] for x in tr if x['d']<cut];b=[x['r'] for x in tr if x['d']>=cut]
    yrs=max((dt.date.fromisoformat(ds[-1])-dt.date.fromisoformat(ds[0])).days/365.25,0.5);se=r.std(ddof=1)/np.sqrt(len(r))
    print(f'{name:55s} n={len(r):5d} E={r.mean():+.3f} t={r.mean()/se:+.1f} wr={100*(r>0).mean():.0f}% R/J={r.sum()/yrs:+.0f} dev={np.mean(a):+.2f}({len(a)}) test={np.mean(b):+.2f}({len(b)})',flush=True)
    return dict(name=name,n=len(r),E=float(r.mean()),t=float(r.mean()/se),dev=float(np.mean(a)),test=float(np.mean(b)),rj=float(r.sum()/yrs))
if __name__=='__main__':
    R=[]
    for lv in['asia','pdhl','prevny','london','fri','pwhl']:
        for tg in[1,1.5,2,3]:
            x=rep(run4h(lv,tg),f'4H {lv} Sweep+Rücklauf, Ziel {tg}R');R.append(x) if x else None
    json.dump(R,open('/tmp/fx/sw4h.json','w'))
