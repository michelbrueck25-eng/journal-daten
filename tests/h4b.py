from h4 import *
tmax=max(d['t'][-1] for d in D.values());tmin=min(d['t'][210] for d in D.values());cut=tmin+0.6*(tmax-tmin)
def sg2(th,trend2,minatr,hours,ob=100):
    out=[]
    for s,d in D.items():
        n=len(d['c']);pp=pip(s)
        for i in range(210,n-2):
            a=d['a'][i]
            if np.isnan(a) or np.isnan(d['sma200'][i]): continue
            if a/pp<minatr: continue
            if hours and d['hour'][i] not in hours: continue
            c=d['c'][i];up=c>d['sma200'][i];st=d['sma50'][i]>d['sma200'][i]
            if d['r3'][i]<th and up and (st or not trend2): out.append((s,i,True))
            elif d['r3'][i]>100-th and (not up) and ((not st) or not trend2): out.append((s,i,False))
    return out
res=[]
for th,t2,ma,hrs in itertools.product((2,5),(False,True),(0,12,20),(None,(4,8,12,16),(0,20))):
    sg=sg2(th,t2,ma,hrs)
    for sa,tg,N in ((3,0.5,24),(3,0.8,12),(3,0.3,24),(2,0.8,12),(4,0.6,24)):
        tr=run(sg,sa,tg,N);a=summ(tr)
        if a.get('n',0)<150: continue
        dev=summ([x for x in tr if x['t']<cut]);te=summ([x for x in tr if x['t']>=cut])
        res.append(dict(th=th,t2=t2,ma=ma,hrs=hrs,sa=sa,tg=tg,N=N,all=a,dev=dev,test=te,tr=tr))
pickle.dump(res,open('/tmp/h4b.pkl','wb'))
print(len(res))
for x in sorted([x for x in res if x['all']['wr']>=58],key=lambda x:-x['all']['avg'])[:12]:
    print(x['th'],x['t2'],x['ma'],x['hrs'],x['sa'],x['tg'],x['N'],x['all'],'dev',x['dev'].get('avg'),x['dev'].get('n'),'test',x['test'].get('avg'),x['test'].get('n'))
