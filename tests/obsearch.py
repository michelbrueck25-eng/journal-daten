"""Suche nach weiteren Daily-Orderblock-Varianten wie Kandidat 1-3: Gitter ueber Einstieg, Stopp, Ziel, Haltedauer, Qualitaet, Alter, Instrumentgruppe; Entwicklung <2023 / Pruefung >=2023."""
import sys,os,io,contextlib,json,itertools,datetime as dt,numpy as np
os.chdir('/home/claude/journal-daten/tests'); sys.path.insert(0,'.')
t=open('dob.py').read(); t=t[:t.index('def runB')]
with contextlib.redirect_stdout(io.StringIO()): exec(t)
SP='2023-01-01'; FXs=lambda s:s not in PIPS
def run(entry,stopb,tg,md,qs,age,grp,flt=''):
    out=[]
    if flt=='cot_stark30':
        from gen import cot_idx
    if flt=='weekly_trend':
        _wt={s:eng.wk_trend(U[s]) for s in U}
    for z in Z:
        if qs=='A' and z['q']!='A': continue
        if age and z['t0']-z['i']>age: continue
        if grp=='FX' and z['sym'] in PIPS: continue
        if grp=='Metall' and z['sym'] not in PIPS: continue
        d=U[z['sym']]; L=z['L']; k=z['t0']; a=z['a']
        if np.isnan(a): continue
        if flt=='weekly_trend' and _wt[z['sym']][k]!=(1 if L else -1): continue
        if flt=='cot_stark30':
            sy=z['sym']
            if sy in PIPS: continue
            ds_=dt.datetime.utcfromtimestamp(d['t'][k]/1000).strftime('%Y-%m-%d'); cb,cq=cot_idx(sy[:3],ds_),cot_idx(sy[3:],ds_)
            if cb is None or cq is None: continue
            if not ((cb-cq>=30) if L else (cq-cb>=30)): continue
        stop=z['lo']-stopb*a if L else z['hi']+stopb*a
        if entry=='edge':
            if (d['o'][k]<z['lo']) if L else (d['o'][k]>z['hi']): continue
            en=z['hi'] if L else z['lo']; kk=k
        else:
            mid=(z['hi']+z['lo'])/2; kk=None
            for q in range(k,min(k+6,len(d['c'])-1)):
                if (d['c'][q]<z['lo']) if L else (d['c'][q]>z['hi']): break
                if (d['l'][q]<=mid) if L else (d['h'][q]>=mid): kk=q; break
            if kk is None: continue
            en=mid
        r=simulate(d,kk,L,en,stop,tg,md,z['sym'])
        if r: out.append(dict(r=r[0],date=dt.datetime.utcfromtimestamp(d['t'][kk]/1000).strftime('%Y-%m-%d'),sym=z['sym'],bars=r[1],L=L,entry=float(en),why=r[2],offen=(r[2]=='Zeit' and kk+1+md>len(d['c'])),last=dt.datetime.utcfromtimestamp(d['t'][min(kk+r[1],len(d['c'])-1)]/1000).strftime('%Y-%m-%d')))
    return out
def st(tr):
    if len(tr)<10: return None
    r=np.array([x['r'] for x in tr]); return len(r),float(r.mean()),float((r>0).mean()*100)
rows=[]
for en,sb,tg,md,qs,age,grp in itertools.product(('edge','mid'),(0.1,0.25,0.5),(2,3,4,5),(10,20),('A','AB'),(0,20),('alle','FX')):
    tr=run(en,sb,tg,md,qs,age,grp); a=st(tr)
    if not a or a[0]<300: continue
    dv=st([x for x in tr if x['date']<SP]); te=st([x for x in tr if x['date']>=SP])
    if not dv or not te: continue
    rows.append((min(dv[1],te[1]),(en,sb,tg,md,qs,age,grp),a,dv,te))
rows.sort(key=lambda x:-x[0]); print(len(rows),'Varianten mit n>=300')
import pickle; pickle.dump(rows,open('/tmp/pf/obrows.pkl','wb'))
for m,c,a,dv,te in rows[:25]: print(f'{m:+.3f}',c,'n%d E%+.3f wr%.0f'%a,'| Entw n%d E%+.3f'%dv[:2],'| Pruef n%d E%+.3f'%te[:2])
