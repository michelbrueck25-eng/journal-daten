"""R:R-/Haltedauer-Sweep ueber die Daily-OB-Familie (Einstieg Kante/Mitte, Stop-Puffer, Ziel in R, Max-Tage, Qualitaet, Universum)."""
import io,contextlib,json,itertools,datetime as dt,numpy as np
t=open('/home/claude/journal-daten/tests/obsearch.py').read(); t=t[:t.index('rows=[]')]
g={'__name__':'obsearch_fwd','__file__':'/home/claude/journal-daten/tests/dob.py'}
with contextlib.redirect_stdout(io.StringIO()): exec(t,g)
run=g['run']
SPL='2023-01-01'
res=[]
for entry,stopb,qs,grp in itertools.product(('edge','mid'),(0.1,0.25),('A','alle'),('FX','alle')):
    for md in (10,20,40,60):
        for tg in (1,1.5,2,3,4,5,6,8,10):
            tr=run(entry,stopb,tg,md,qs,0,grp)
            if len(tr)<150: continue
            r=np.array([x['r'] for x in tr]); ds=np.array([x['date'] for x in tr])
            a=r[ds<SPL]; b=r[ds>=SPL]
            yrs=max((dt.date.fromisoformat(max(ds.tolist()))-dt.date.fromisoformat(min(ds.tolist()))).days/365.25,1)
            res.append(dict(entry=entry,stopb=stopb,qs=qs,grp=grp,md=md,tg=tg,n=len(r),E=float(r.mean()),rj=float(r.sum()/yrs),wr=float((r>0).mean()),dev=float(a.mean()),test=float(b.mean()),nd=len(a),nt=len(b)))
    print(entry,stopb,qs,grp,len(res),flush=True)
json.dump(res,open('/tmp/fx/rsweep.json','w'))
