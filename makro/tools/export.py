import warnings;warnings.filterwarnings('ignore')
exec(open('wf.py').read().split("rows=report(None)")[0])
import json,math,sys,datetime as dt,numpy as np
sys.path.insert(0,'/home/claude/tmp/ind')
from model import CUR,PX as PXD
import regime as RG
rows=report(None)
last=months[-1]; li=[i for i,d in enumerate(S) if d['m']==last]
live={}  # (nm,h)-> {sym:pred}
for nm,cols in SETS.items():
    for h in HZ:
        y=np.array([d['fut'][h]/(d['sd']*math.sqrt(h)) if d['fut'][h] is not None else np.nan for d in S])
        tr=np.where(~np.isnan(y))[0];A=XA[tr][:,cols];mu=A.mean(0);sg=A.std(0)+1e-9;A=(A-mu)/sg
        w=np.linalg.solve(A.T@A+50*np.eye(len(cols)),A.T@(y[tr]-y[tr].mean()))
        p=((XA[li][:,cols]-mu)/sg)@w+y[tr].mean()
        live[(nm,h)]={S[i]['sym']:float(pp) for i,pp in zip(li,p)}
def cur_scores(pr):
    syms=sorted(pr);A=np.zeros((len(syms)+1,8));b=np.zeros(len(syms)+1)
    for r,s in enumerate(syms): A[r,CUR.index(s[:3])]=1;A[r,CUR.index(s[3:])]=-1;b[r]=pr[s]
    A[-1,:]=1;sc=np.linalg.lstsq(A,b,rcond=None)[0];return {c:float(sc[k]) for k,c in enumerate(CUR)}
out={'stand':last,'erstellt':dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%MZ'),'horizonte':HZ,'waehrungen':{},'paare':{},'modelle':[],'verbund':json.load(open('ens_res.json'))}
for h in HZ:
    avg={s:float(np.mean([live[(nm,h)][s] for nm in SETS])) for s in live[('A_Carry',h)]}
    out['paare'][str(h)]=avg;out['waehrungen'][str(h)]=cur_scores(avg)
    # Streuung der Modelle je Waehrung: Anteil der Modelle mit gleichem Vorzeichen
for nm in SETS:
    for h in HZ:
        t=next(r for r in rows if r['modell']==nm and r['h']==h and r['teil']=='test');d=next((r for r in rows if r['modell']==nm and r['h']==h and r['teil']=='dev'),None)
        cs=cur_scores(live[(nm,h)])
        out['modelle'].append(dict(name=nm,h=h,n_test=t['n'],netR_test=round(t['netR'],3),treffer_test=round(t['treffer'],3),ic_test=round(t['ic'],3),netR_dev=round(d['netR'],3) if d else None,waehrung={c:round(v,3) for c,v in cs.items()}))
out['hinweis']='Walk-forward, Makro 1 Monat verzoegert, Split 2023-01-01, 1 Pip Kosten. Kein Modell erreicht 0,15 R netto im Test.'
json.dump(out,open('/home/claude/journal-daten/makro/modell.json','w'),ensure_ascii=False,separators=(',',':'))
# ---- Regime-Daten fuer die App: letzte 160 Tageskerzen je Paar ----
import glob,os
Hm='/home/claude/journal-privat/marktdaten';reg={'stand':last,'paare':{}}
for f in sorted(glob.glob(Hm+'/*_D.json')):
    s=os.path.basename(f)[:-7]
    if len(s)!=6 or s[:3] not in CUR or s[3:] not in CUR: continue
    r=json.load(open(f))['rows'];o=[x[1] for x in r];h=[x[2] for x in r];l=[x[3] for x in r];c=[x[4] for x in r]
    R=RG.regime(o,h,l,c);v=[1]*len(c);pf=RG.profile(h,l,v,len(c)-1)
    n=160;reg['paare'][s]={'k':[[x[0]//1000,x[1],x[2],x[3],x[4]] for x in r[-n:]],'r':[x if x is not None else 0 for x in R[-n:]],'vp':[round(z,6) for z in pf] if pf else None}
json.dump(reg,open('/home/claude/journal-daten/makro/regime.json','w'),separators=(',',':'))
print(len(out['modelle']),os.path.getsize('/home/claude/journal-daten/makro/modell.json'),os.path.getsize('/home/claude/journal-daten/makro/regime.json'))
print({c:round(v,2) for c,v in out['waehrungen']['30'].items()})
