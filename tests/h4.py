import json,glob,os,itertools,random,pickle,numpy as np,pandas as pd,datetime as dt
HOME='/home/claude/journal-privat/marktdaten'
D={}
for f in sorted(glob.glob(HOME+'/*_4H.json')):
    s=os.path.basename(f).split('_')[0]; r=np.array(json.load(open(f))['rows'],float)
    D[s]=dict(t=r[:,0],o=r[:,1],h=r[:,2],l=r[:,3],c=r[:,4])
def pip(s): return 0.01 if s.endswith('JPY') else 0.0001
def cost_r(s,sd,a,days):
    if s=='GOLD': return (0.05*a+0.012*a*days)/sd
    return (1.0+0.3*days)*pip(s)/sd
def atr(d,n=14):
    h,l,c=d['h'],d['l'],d['c'];pc=np.r_[c[0],c[:-1]];tr=np.maximum(h-l,np.maximum(abs(h-pc),abs(l-pc)));return pd.Series(tr).rolling(n).mean().values
def rsi(c,n):
    d=np.diff(c,prepend=c[0]);up=pd.Series(np.where(d>0,d,0)).ewm(alpha=1/n,adjust=False).mean();dn=pd.Series(np.where(d<0,-d,0)).ewm(alpha=1/n,adjust=False).mean();return (100-100/(1+up/dn.replace(0,np.nan))).values
for s,d in D.items():
    c=pd.Series(d['c']);d['a']=atr(d);d['sma200']=c.rolling(200).mean().values;d['sma50']=c.rolling(50).mean().values;d['ema20']=c.ewm(span=20,adjust=False).mean().values
    d['m20']=c.rolling(20).mean().values;d['sd20']=c.rolling(20).std().values;d['r3']=rsi(d['c'],3);d['r14']=rsi(d['c'],14)
    d['hh']=pd.Series(d['h']).rolling(12).max().shift(1).values;d['ll']=pd.Series(d['l']).rolling(12).min().shift(1).values
    d['hour']=np.array([dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).hour for t in d['t']])
def sim(s,i,L,sa,tg,N):
    d=D[s];n=len(d['c']);a=d['a'][i]
    if i+1+N>=n or np.isnan(a): return None
    e=d['o'][i+1];sd=sa*a;sg=1 if L else -1;stp=e-sg*sd;tp=e+sg*tg*sd
    for j in range(i+1,i+1+N):
        if (d['l'][j]<=stp) if L else (d['h'][j]>=stp): r=-1.0;break
        if (d['h'][j]>=tp) if L else (d['l'][j]<=tp): r=tg;break
    else: j=i+N;r=sg*(d['c'][j]-e)/sd
    days=(d['t'][j]-d['t'][i+1])/864e5+0.17
    return r-cost_r(s,sd,a,days),j
def sigs(kind,p):
    out=[]
    for s,d in D.items():
        n=len(d['c'])
        for i in range(210,n-2):
            if np.isnan(d['a'][i]) or np.isnan(d['sma200'][i]): continue
            c=d['c'][i];up=c>d['sma200'][i]
            if kind=='rsi3':
                if d['r3'][i]<p[0] and up: out.append((s,i,True))
                elif d['r3'][i]>100-p[0] and not up: out.append((s,i,False))
            elif kind=='boll':
                z=(c-d['m20'][i])/d['sd20'][i]
                if z<-p[0] and up: out.append((s,i,True))
                elif z>p[0] and not up: out.append((s,i,False))
            elif kind=='pull':  # Rücksetzer zum EMA20 im Trend + Umkehrkerze
                if up and d['l'][i]<=d['ema20'][i] and c>d['o'][i] and c>d['ema20'][i] and d['r14'][i]<p[0]: out.append((s,i,True))
                if (not up) and d['h'][i]>=d['ema20'][i] and c<d['o'][i] and c<d['ema20'][i] and d['r14'][i]>100-p[0]: out.append((s,i,False))
            elif kind=='ses':   # Ausbruchsfalle: 12-Bar-Hoch/Tief gebrochen, Schluss wieder zurück (Fakeout) gegen den Bruch
                if d['h'][i]>d['hh'][i] and c<d['hh'][i]: out.append((s,i,False))
                if d['l'][i]<d['ll'][i] and c>d['ll'][i]: out.append((s,i,True))
    return out
def run(sg,sa,tg,N):
    busy={};out=[]
    for (s,i,L) in sorted(sg,key=lambda x:(D[x[0]]['t'][x[1]],x[0])):
        if i<=busy.get(s,-1): continue
        t=sim(s,i,L,sa,tg,N)
        if not t: continue
        busy[s]=t[1];out.append(dict(sym=s,t=float(D[s]['t'][i+1]),L=L,r=float(t[0]),bars=t[1]-i))
    return out
def summ(tr):
    if len(tr)<30: return dict(n=len(tr))
    r=np.array([x['r'] for x in tr]);eq=np.cumsum(r)
    return dict(n=len(r),wr=round(float((r>0).mean()*100),1),avg=round(float(r.mean()),3),pf=round(float(r[r>0].sum()/max(1e-9,-r[r<=0].sum())),2),dd=round(float((np.maximum.accumulate(eq)-eq).max()),1),hold=round(float(np.mean([x['bars'] for x in tr])),1))
if __name__=='__main__':
    tmax=max(d['t'][-1] for d in D.values());tmin=min(d['t'][210] for d in D.values());cut=tmin+0.6*(tmax-tmin)
    res=[]
    fam=[('rsi3',(5,)),('rsi3',(10,)),('boll',(2.0,)),('boll',(2.5,)),('pull',(40,)),('pull',(30,)),('ses',(0,))]
    for kind,p in fam:
        sg=sigs(kind,p)
        for sa,tg,N in itertools.product((1.5,2,3),(0.3,0.5,0.8,1.0),(12,24)):
            tr=run(sg,sa,tg,N);a=summ(tr)
            if a.get('n',0)<30: continue
            dev=summ([x for x in tr if x['t']<cut]);te=summ([x for x in tr if x['t']>=cut])
            res.append(dict(kind=kind,p=p,sa=sa,tg=tg,N=N,all=a,dev=dev,test=te,tr=tr))
    pickle.dump(res,open('/tmp/h4.pkl','wb'))
    ok=sorted([x for x in res if x['all'].get('wr',0)>=55],key=lambda x:-x['all']['avg'])
    print(len(res),'Varianten, Median avg',np.median([x['all']['avg'] for x in res if 'avg' in x['all']]))
    for x in ok[:15]: print(x['kind'],x['p'],x['sa'],x['tg'],x['N'],x['all'],'dev',x['dev'].get('avg'),'test',x['test'].get('avg'),x['test'].get('n'))
