import warnings;warnings.filterwarnings('ignore')
exec(open('wf.py').read().split("RES={}")[0])
import json,math,datetime as dt,numpy as np
from model import CUR,PX as PXD
SETS2=dict(SETS);SETS2['I_Real+Mom']=[2,8,9,10]
HS=list(range(46,94));ALPHAS=[20.0,200.0]
last=months[-1];li=[i for i,d in enumerate(S) if d['m']==last]
def cur_scores(pr):
    syms=sorted(pr);A=np.zeros((len(syms)+1,8));b=np.zeros(len(syms)+1)
    for r,s in enumerate(syms): A[r,CUR.index(s[:3])]=1;A[r,CUR.index(s[3:])]=-1;b[r]=pr[s]
    A[-1,:]=1;return np.linalg.lstsq(A,b,rcond=None)[0]
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
