import pickle
_t=open('ideen6.py').read(); exec(_t[:_t.index('\nres=[]\ndef add(')])
import pyr as PY
sets={'COTtop70':S_cot('comm',156,1,'folgen',70),'COTtop50':S_cot('comm',156,1,'folgen',50),'COTk2_70':S_cot('comm',156,2,'folgen',70),'COTd8':S_cot('comm',156,1,'folgen',50,delta=8),'COTtrend70':S_cot('comm',156,1,'folgen',70,trend=True),'Gold104U':S_gold(104,'Umkehr',20),'Gold156U':S_gold(156,'Umkehr',20),'Gold260F':S_gold(260,'folgen',20)}
res=[]
for nm,sg in sets.items():
    # A) Pyramiding/Trail
    for sa,tk,adds,red,N in itertools.product((3,4),(3,4,6),((),((1,.5),(2,.5))),(None,(5,0)),(20,40)):
        tr=PY.run(sg,sa=sa,tk=tk,adds=adds,red=red,N=N); a,b,c=summ(tr)
        res.append(dict(typ='pyr',name=nm,p=(sa,tk,adds,red,N),all=a,dev=b,test=c,_tr=tr))
    # B) hohe Winrate: weiter Stopp, kleines Ziel
    for sa,tg,N in ((4,0.25,20),(4,0.4,20),(5,0.3,30),(5,0.5,30),(6,0.35,30),(6,0.5,40),(8,0.3,40),(3,0.4,15)):
        tr=runsig(sg,sa,tg,N); a,b,c=summ(tr)
        res.append(dict(typ='hw',name=nm,p=(sa,tg,N),all=a,dev=b,test=c,_tr=tr))
pickle.dump(res,open('/tmp/hw.pkl','wb'))
