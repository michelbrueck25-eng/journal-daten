import json,glob,os,csv,math,datetime as dt
import numpy as np
H='/home/claude/journal-privat/marktdaten'
CUR=['USD','EUR','GBP','JPY','CHF','AUD','CAD','NZD']
# ---- Makrodaten monatlich, 1 Monat Verzoegerung (Wert von Monat m ist erst Ende m+1 bekannt) ----
M={}
for r in csv.DictReader(open('/home/claude/journal-daten/makro/monatlich.csv')):
    f=lambda x: float(x) if x not in ('',None) else np.nan
    M[(r['waehrung'],r['monat'])]=(f(r['leitzins']),f(r['cpi_yoy']),f(r['arbeitslosenquote']))
months=sorted({k[1] for k in M})
def ffill(c,i):  # letzter bekannter Wert (CPI quartalsweise / JPY-Ende)
    v=np.array([M.get((c,m),(np.nan,)*3)[i] for m in months],float)
    for k in range(1,len(v)):
        if np.isnan(v[k]): v[k]=v[k-1]
    return v
MAC={c:{n:ffill(c,i) for i,n in enumerate(['rate','cpi','un'])} for c in CUR}
mi={m:i for i,m in enumerate(months)}
def feats(c,mon):
    """Makro-Merkmale einer Waehrung, bekannt am Ende des Monats mon: nutzt nur Monate <= mon-1"""
    i=mi[mon]-1
    if i<13: return None
    g=MAC[c]; r=g['rate'];p=g['cpi'];u=g['un']
    x=[r[i],p[i],r[i]-p[i],u[i],r[i]-r[i-6],p[i]-p[i-6],u[i]-u[i-12],r[i]-r[i-12]]
    return None if any(np.isnan(x)) else x
FN=['rate','cpi','real','un','d_rate6','d_cpi6','d_un12','d_rate12']
# ---- Kurse ----
PX={}
for f in sorted(glob.glob(H+'/*_D.json')):
    s=os.path.basename(f)[:-7]
    if len(s)!=6 or s[:3] not in CUR or s[3:] not in CUR: continue
    rows=json.load(open(f))['rows']; PX[s]=(np.array([r[0] for r in rows]),np.array([r[4] for r in rows]),0.01 if s.endswith('JPY') else 1e-4)
HZ=[10,20,30,45,60,90]
def ym(ts): d=dt.datetime.utcfromtimestamp(ts/1000); return f'{d.year}-{d.month:02d}'
# Stichproben: je Monatsende, je Paar
S=[]  # dict
for s,(t,c,pv) in PX.items():
    b,q=s[:3],s[3:]
    mons=np.array([ym(x) for x in t]); lr=np.diff(np.log(c),prepend=np.nan)
    for k in range(1,len(t)):
        if k==len(t)-1 or mons[k]!=mons[k+1]:
            m=mons[k]
            if m not in mi or k<260: continue
            fb,fq=feats(b,m),feats(q,m)
            if fb is None or fq is None: continue
            sd=np.nanstd(lr[k-59:k+1])
            mom=[np.log(c[k]/c[k-21]),np.log(c[k]/c[k-63]),np.log(c[k]/c[k-252])]
            S.append(dict(sym=s,k=k,t=int(t[k]),m=m,base=b,quote=q,x=np.array(fb)-np.array(fq),mom=np.array(mom)/ (sd*math.sqrt(21)),
              sd=sd,fut={h:(math.log(c[k+h]/c[k]) if k+h<len(c) else None) for h in HZ},pv=pv,px=c[k]))
S.sort(key=lambda d:(d['t'],d['sym']))
json.dump({'n':len(S)},open('n.json','w'))
if __name__=='__main__': print(len(S),S[0]['m'],S[-1]['m'])
