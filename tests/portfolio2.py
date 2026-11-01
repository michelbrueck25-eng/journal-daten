"""Portfolio-Empfehlung: Auswahl der oberen Strategien + Risikoaufteilung. Auswahl/Gewichte nur aus Entwicklung (<2023), Auswertung auf Pruefung (>=2023). Trade-Ebene, Gewinn/Verlust am Schlusstag."""
import sys,os,io,contextlib,json,datetime as dt,collections,itertools,pickle,numpy as np
os.chdir('/home/claude/journal-daten/tests'); sys.path.insert(0,'.')
D='/home/claude/journal-daten'; B=json.load(open(f'{D}/backtest-trades.json')); F=json.load(open(f'{D}/forwardtest.json')); S={x['id']:x for x in F['strategien']}
t=open('obsearch.py').read(); t=t[:t.index('rows=[]')]; g={'__name__':'p2','__file__':f'{D}/tests/dob.py'}
with contextlib.redirect_stdout(io.StringIO()): exec(t,g)
OBK={'fw3-k1':('mid',0.25,3,10,'A',0,'alle'),'fw3-k2':('mid',0.5,3,7,'A',0,'alle','weekly_trend'),'fw3-k3':('edge',0.1,3,10,'A',0,'alle','cot_stark30')}
T={}
for k,v in B.items():
    if S.get(k,{}).get('tf')=='Daily' and np.mean([x[3] for x in v])>=0.15: T[k]=[(x[0],x[1],x[3],x[4] or 1) for x in v]
for k,c in OBK.items():
    T[k]=[(x['date'],x['sym'],x['r'],max(x['bars'],1)) for x in g['run'](*c)]
def cl(o,bars):
    return (dt.date.fromisoformat(o)+dt.timedelta(days=int(round(bars*7/5)))).isoformat()
SP='2023-01-01'; IDS=sorted(T)
tr={i:[(o,cl(o,b),r,s) for (o,s,r,b) in T[i]] for i in IDS}
months=sorted({c[:7] for i in IDS for (_,c,_,_) in tr[i]}); MI={m:k for k,m in enumerate(months)}
def mvec(i,lo=None,hi=None):
    v=np.zeros(len(months))
    for (o,c,r,s) in tr[i]:
        if (lo and c<lo) or (hi and c>=hi): continue
        v[MI[c[:7]]]+=r
    return v
def series(w,lo=None,hi=None):
    ev=collections.defaultdict(float)
    for i,wi in w.items():
        for (o,c,r,s) in tr[i]:
            if (lo and c<lo) or (hi and c>=hi): continue
            ev[c]+=wi*r
    return ev
def stats(w,lo=None,hi=None):
    ev=series(w,lo,hi)
    if not ev: return None
    ds=sorted(ev); eq=np.cumsum([ev[d] for d in ds]); pk=np.maximum.accumulate(np.r_[0,eq])[1:]; dd=float((pk-eq).max())
    m=collections.defaultdict(float)
    for d in ds: m[d[:7]]+=ev[d]
    ms=np.array(list(m.values())); yrs=max((dt.date.fromisoformat(ds[-1])-dt.date.fromisoformat(ds[0])).days/365.25,0.5)
    return dict(jahr=float(eq[-1]/yrs),mon=float(eq[-1]/yrs/12),dd=dd,worst=float(ms.min()),neg=int((ms<0).sum()),nm=len(ms))
def scale_to(w,target_dd,lo=None,hi=None):
    s=stats(w,lo,hi); return {k:v*target_dd/s['dd'] for k,v in w.items()}
if __name__=='__main__':
    print(len(IDS),'Kandidaten:',IDS)
    dev={i:mvec(i,None,SP) for i in IDS}
    info={}
    for i in IDS:
        v=dev[i]; r=[x[2] for x in tr[i] if x[1]<SP]
        info[i]=dict(E=float(np.mean(r)) if r else 0,n=len(r),sd=float(v[v!=0].std()) if (v!=0).sum()>3 else 9)
    print('Entw E/n/sd:',{i:(round(x['E'],2),x['n'],round(x['sd'],1)) for i,x in info.items()})
    # Korrelation (Monate, gesamt)
    full={i:mvec(i) for i in IDS}
    def pick(K,minE=0.15,cmax=0.75):
        order=sorted(IDS,key=lambda i:-(info[i]['E']/info[i]['sd'] if info[i]['n']>=20 else -1))
        out=[]
        for i in order:
            if info[i]['E']<minE or info[i]['n']<20: continue
            if all(np.corrcoef(dev[i],dev[j])[0,1]<cmax for j in out): out.append(i)
            if len(out)==K: break
        return out
    res={}
    for nm,sel in (('alle Kandidaten',IDS),('Top 3',pick(3)),('Top 5',pick(5)),('Top 7',pick(7)),('Top 10',pick(10))):
        for wm in ('gleich','riskparity'):
            w={i:(1.0 if wm=='gleich' else 1/info[i]['sd']) for i in sel}
            w=scale_to(w,5.0,None,SP)          # Risiko so, dass Entwicklung 5 % Max-Drawdown hat
            a=stats(w,None,SP); b=stats(w,SP,None)
            print(f"{nm:16} {wm:10} N={len(sel):2} | Entw: {a['mon']:.2f} %/Mon DD {a['dd']:.1f} schlecht {a['worst']:.1f} | Pruef: {b['mon']:.2f} %/Mon DD {b['dd']:.1f} schlechtester Mon {b['worst']:.1f} Verlustmon {b['neg']}/{b['nm']}")
            res[(nm,wm)]=(sel,w)
    pickle.dump(res,open('/tmp/pf/p2.pkl','wb'))
    print('Top5:',pick(5)); print('Top7:',pick(7))
