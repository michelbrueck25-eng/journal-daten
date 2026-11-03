import warnings;warnings.filterwarnings('ignore')
exec(open('wf.py').read().split("rows=report(None)")[0])
import numpy as np,json,math,datetime as dt
# Verbund je Horizont: Mittel der z-standardisierten Vorhersagen aller 8 Modelle, nur Modelle mit dev netR>0 (Auswahl NUR aus Dev-Daten)
rows=report(None);dev={(r['modell'],r['h']):r['netR'] for r in rows if r['teil']=='dev'}
res=[]
for h in HZ:
    sel=[nm for nm in SETS if dev.get((nm,h),-1)>0]
    allm=list(SETS)
    for lab,ms in (('alle8',allm),('dev>0',sel)):
        if not ms: continue
        d={}
        for nm in ms:
            for i,p,y in RES[(nm,h)]:
                d.setdefault(i,[]).append(p)
        ids=sorted(d);P=np.array([np.mean(d[i]) for i in ids]);yy=dict((i,y) for i,p,y in RES[(allm[0],h)])
        for part,cond in (('dev',lambda m:m<'2023-01'),('test',lambda m:m>='2023-01')):
            sel_i=[(i,p) for i,p in zip(ids,P) if cond(S[i]['m']) and not np.isnan(yy.get(i,np.nan))]
            if not sel_i: continue
            pp=np.array([x[1] for x in sel_i]);Y=np.array([yy[x[0]] for x in sel_i]);cost=np.array([PV[x[0]]/(SD[x[0]]*PX[x[0]]*math.sqrt(h)) for x in sel_i])
            R=np.sign(pp)*Y-cost
            res.append(dict(verbund=lab,h=h,teil=part,n=len(pp),netR=round(float(R.mean()),3),treffer=round(float((np.sign(pp)==np.sign(Y)).mean()),3),ic=round(float(np.corrcoef(pp,Y)[0,1]),3),modelle=ms if lab=='dev>0' else 8))
for r in res:
    if r['teil']=='test': print(r)
json.dump(res,open('ens_res.json','w'),ensure_ascii=False)
