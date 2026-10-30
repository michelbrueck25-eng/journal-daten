import json,pickle,random,numpy as np,datetime as dt
_t=open('ideen6.py').read(); exec(_t[:_t.index('\nres=[]\ndef add(')])
import pyr as PY
rnd=random.Random(11); rng=np.random.default_rng(5)
A2=((1,.5),(2,.5))
CF={
'fw7-a1':dict(g='COT Commercials Top gegen Flop 70',sig=lambda:S_cot('comm',156,1,'folgen',70),kind='pyr',p=dict(sa=3,tk=6,adds=A2,red=None,N=40),name='COT Top/Flop · Aufstocken +1 R/+2 R · Trail 6 ATR · 40 Tage'),
'fw7-a2':dict(g='COT Commercials zwei Paare, Abstand 70',sig=lambda:S_cot('comm',156,2,'folgen',70),kind='pyr',p=dict(sa=3,tk=6,adds=A2,red=(5,0),N=40),name='COT 2 Paare · Aufstocken, Verlierer nach 5 Tagen halbieren · Trail 6 ATR'),
'fw7-a3':dict(g='COT Veränderung 8 Wochen',sig=lambda:S_cot('comm',156,1,'folgen',50,delta=8),kind='pyr',p=dict(sa=3,tk=6,adds=A2,red=None,N=40),name='COT Veränderung 8 Wochen · Aufstocken · Trail 6 ATR · 40 Tage'),
'fw7-g1':dict(g='Gold COT Commercials Umkehr 104W',sig=lambda:S_gold(104,'Umkehr',20),kind='pyr',p=dict(sa=3,tk=4,adds=(),red=None,N=20),name='Gold COT Umkehr · Trail 4 ATR · 20 Tage (Winrate 66 %)'),
'fw7-h1':dict(g='Gold COT Commercials Umkehr 156W',sig=lambda:S_gold(156,'Umkehr',20),kind='hw',p=dict(sa=3,tg=0.4,N=15),name='Gold COT Umkehr 156W · Stopp 3 ATR, Ziel 0,4 R · 15 Tage (Winrate 86 %, verdächtig hoch)'),
}
out={}
for sid,c in CF.items():
    sg=c['sig']()
    f=(lambda s: PY.run(s,**c['p'])) if c['kind']=='pyr' else (lambda s: runsig(s,c['p']['sa'],c['p']['tg'],c['p']['N']))
    tr=f(sg); a,b,t=summ(tr); r=np.array([x['r'] for x in tr]); nulls=[]
    for _ in range(100):
        sh=[(s,i+rnd.randint(30,250),L) for (s,i,L) in sg if i+250<len(P[s]['d']['c'])-45]
        q=f(sh)
        if q: nulls.append(np.mean([x['r'] for x in q]))
    nulls=np.array(nulls); ci=np.percentile([np.mean(rng.choice(r,len(r))) for _ in range(2000)],[5,95])
    # Risiko
    py=max(5,len(r)/len(set(x['date'][:4] for x in tr)));d=[]
    for _ in range(2000):
        x=rng.choice(r,int(round(py)));eq=np.cumsum(x);d.append(float((np.maximum.accumulate(np.r_[0,eq])[1:]-eq).max()))
    d50,d95=np.percentile(d,[50,95]);risk=min(1.5,5/max(d95,1e-9));risk=round(risk*20)/20
    mo={}
    for x in tr:
        y,m=int(x['date'][:4]),int(x['date'][5:7]);k=(dt.date(y,m,1)-dt.date(1970,1,1)).days
        n0,s0=mo.get(k,(0,0));mo[k]=(n0+1,s0+x['r'])
    hold=np.mean([x.get('hold',0) for x in tr]) if c['kind']=='pyr' else None
    out[sid]=dict(c=c,a=a,b=b,t=t,nullm=float(nulls.mean()),null95=float(np.percentile(nulls,95)),nullge=float((nulls>=r.mean()).mean()),ci=[float(ci[0]),float(ci[1])],risk=risk,d50=float(d50*risk),d95=float(d95*risk),py=py,mo=sorted((k,v[0],round(v[1],2)) for k,v in mo.items()),r=r,hold=hold,tr=tr)
    print(sid,a,'dev',b.get('avg'),b.get('n'),'test',t.get('avg'),t.get('n'),'null',round(nulls.mean(),3),round(np.percentile(nulls,95),3),'ge',(nulls>=r.mean()).mean(),'CI',ci.round(2),'risk',risk,flush=True)
pickle.dump(out,open('/tmp/build7.pkl','wb'))
# Korrelation
ids=list(out);allm=sorted(set(x['date'][:7] for o in out.values() for x in o['tr']))
M={k:np.array([sum(x['r'] for x in o['tr'] if x['date'][:7]==m) for m in allm]) for k,o in out.items()}
print(ids);print(np.round(np.corrcoef([M[k] for k in ids]),2))
