import warnings;warnings.filterwarnings('ignore')
exec(open('wf.py').read().split("RES={}")[0])
import json,math,datetime as dt,numpy as np
from model import CUR,PX as PXD
SETS2=dict(SETS);SETS2['I_Real+Mom']=[2,8,9,10]
HS=list(range(46,94));ALPHAS=[20.0,200.0]
last=months[-1];li=[i for i,d in enumerate(S) if d['m']==last]
W={'EUR':.576,'JPY':.136,'GBP':.119,'CAD':.091,'CHF':.036}  # DXY-Gewichte ohne SEK
def cur_scores(pr):
    """Wie im Vorbild: jede Waehrung GEGEN den US-Dollar (Long = steigt gegen USD); USD-Eintrag = DXY-Nachbau (Long = DXY steigt)."""
    v={}
    for c in CUR:
        if c=='USD': continue
        v[c]=pr[c+'USD'] if c+'USD' in pr else -pr['USD'+c]
    out=[0.0]*len(CUR)
    for c,x in v.items(): out[CUR.index(c)]=x
    out[CUR.index('USD')]=-sum(W[c]*v[c] for c in W)
    return out
CL={c:[] for c in CUR};NM=0
for h in HS:
    y=np.array([ (math.log(PXD[d['sym']][1][d['k']+h]/PXD[d['sym']][1][d['k']])/(d['sd']*math.sqrt(h))) if d['k']+h<len(PXD[d['sym']][1]) else np.nan for d in S])
    tr=np.where(~np.isnan(y))[0]; cnt={c:0 for c in CUR};n=0
    for nm,cols in SETS2.items():
        for al in ALPHAS:
            A=XA[tr][:,cols];mu=A.mean(0);sg=A.std(0)+1e-9;A=(A-mu)/sg
            w=np.linalg.solve(A.T@A+al*np.eye(len(cols)),A.T@(y[tr]-y[tr].mean()))
            p=((XA[li][:,cols]-mu)/sg)@w+y[tr].mean()
            sc=cur_scores({S[i]['sym']:float(pp) for i,pp in zip(li,p)})
            for k,c in enumerate(CUR): cnt[c]+= 1 if sc[k]>0 else 0
            n+=1
    NM=n
    for c in CUR: CL[c].append(cnt[c])
live={'stand':dt.datetime.now(dt.UTC).strftime('%d.%m.%Y'),'datenmonat':last,'horizonte':HS,'n_modelle':NM,'long':CL}
m=json.load(open('/home/claude/journal-daten/makro/modell.json'));m['live']=live
json.dump(m,open('/home/claude/journal-daten/makro/modell.json','w'),ensure_ascii=False,separators=(',',':'))
for c in CUR: print(c,round(100*sum(CL[c])/(NM*len(HS))),'% Long')
