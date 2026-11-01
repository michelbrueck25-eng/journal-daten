exec(open('portfolio2.py').read().split("if __name__=='__main__':")[0])
import pickle,json,numpy as np,datetime as dt
res,info=pickle.load(open('/tmp/ix/opt.pkl','rb'));w=res[10]['w'];avg=float(np.mean(list(w.values())))
ev=series(w);d0=dt.date.fromisoformat(min(ev));d1=dt.date.fromisoformat(max(ev))
days=[];x=d0
while x<=d1:days.append(x);x+=dt.timedelta(days=1)
daily=np.array([ev.get(x.isoformat(),0.0) for x in days])  # in % des Kontos bei Plan (1 R = Gewicht %)
# nur Handelstage Mo-Fr
daily=np.array([v for x,v in zip(days,daily) if x.weekday()<5])
rng=np.random.default_rng(11);B=21;N=252;P=4000;nb=N//B
starts=rng.integers(0,len(daily)-B,(P,nb));path=np.concatenate([daily[s:s+B] for s in starts.T],axis=0) if False else np.stack([np.concatenate([daily[s:s+B] for s in row]) for row in starts])
rows=[]
for fac in (0.5,0.75,1.0,1.25,1.5,2.0,3.0,4.0):
    eq=np.cumprod(1+path*fac/100,axis=1);pk=np.maximum.accumulate(np.concatenate([np.ones((P,1)),eq],1),axis=1)[:,1:];dd=(pk-eq)/pk
    m=dd.max(1)*100;fin=(eq[:,-1]-1)*100
    rows.append(dict(faktor=fac,risiko=round(avg*fac,2),dd_median=-round(float(np.median(m)),1),dd95=-round(float(np.percentile(m,95)),1),p6=round(float((m>=6).mean()*100),1),p10=round(float((m>=10).mean()*100),1),p15=round(float((m>=15).mean()*100),1),rendite_median=round(float(np.median(fin)),1)))
    print(rows[-1])
for path_ in ('/home/claude/journal-daten/forwardtest.json','/home/claude/journal-privat/forwardtest.json'):
    d=json.load(open(path_));d['portfolio']['optimal']['bootstrap']={'trades':N,'pfade':P,'einheit':'Handelstage','text':'Zufällige Jahre aus den Rückrechnungen des Plans (Bootstrap aus 21-Tage-Blöcken, 252 Handelstage, 4.000 Pfade je Zeile). Die Blöcke erhalten Verlustserien und parallele Trades. Faktor 1 ist dein Plan, Risiko ist der Durchschnitt je Strategie und Trade.','zeilen':rows};json.dump(d,open(path_,'w'),ensure_ascii=False,separators=(',',':'))
