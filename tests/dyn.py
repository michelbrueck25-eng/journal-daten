s=open("challenge.py").read(); exec(s[:s.rindex("if __name__==")])
import numpy as np
days,p=daily(PORT['Mischung 7 (Greedy)'])
def run(f,mode,dd=10.0,dl=3.0,L=365,step=30,cap=6.0):
    res=[]
    for s in range(0,len(p)-L,step):
        eq=0.0;peak=0.0;mdd=0;bad=False;
        for k in range(L):
            if mode=='fix': m=f
            else: m=min(cap,f*(eq+dd)/dd)       # Risiko wächst mit Puffer zum statischen Limit
            v=p[s+k]*m
            if v<=-dl: bad=True;break
            eq+=v
            if eq<=-dd: bad=True;break
            peak=max(peak,eq);mdd=max(mdd,peak-eq)
        res.append((bad,eq,mdd))
    n=len(res);ok=[r for r in res if not r[0]]
    return 100*(1-len(ok)/n),np.median([r[1] for r in res]),np.percentile([r[1] for r in res],20),np.median([r[2] for r in ok]) if ok else 0
print('Jahres-Fenster (Start alle 30 Tage seit 2019), Limit 10 % statisch, Tageslimit 3 %')
for mode,fs in (('fix',(1,1.5,2,2.5,3)),('dyn',(1,1.5,2,2.5,3))):
    for f in fs:
        b,med,p20,md=run(f,mode);print(f'{mode} Faktor {f}: Limit gerissen {b:3.0f} % | Jahresertrag Median {med:5.1f} % (schwächste 20 %: {p20:5.1f}) | Median-Drawdown {md:4.1f} % -> {med/12:4.2f} %/Monat')
