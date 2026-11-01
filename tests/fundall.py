import warnings,os,sys,json,bisect,datetime as dt,io,contextlib
warnings.filterwarnings('ignore')
os.environ['FW_START']='2000-01-01'
sys.path.insert(0,'/home/claude/journal-daten/tests')
import numpy as np
import fwd
import importlib
with contextlib.redirect_stdout(io.StringIO()):
    f2=importlib.import_module('fund2')
S5=f2.comb_scores(4,1)          # Fundament-Score je COT-Stichtag
CD=sorted(S5)
allabs=[abs(sc[a]-sc[b]) for sc in S5.values() for a in sc for b in sc if a<b]
MED=float(np.median(allabs))
def fscore(sym,date):
    if len(sym)!=6 or sym[:3] not in f2.CCY or sym[3:] not in f2.CCY:return None
    k=bisect.bisect_right(CD,(date-dt.timedelta(days=4)).isoformat())-1
    if k<0:return None
    sc=S5[CD[k]]
    return sc[sym[:3]]-sc[sym[3:]] if sym[:3] in sc and sym[3:] in sc else None
def rows(tr):
    out=[]
    for t in tr:
        if not t.get('closed',True):continue
        d=dt.date.fromisoformat(str(t.get('open_date') or t['date'])[:10]);L=1 if t['dir']=='long' else -1
        out.append((d,t['sym'],L,float(t['r'])))
    return out
def ev(rs):
    if not rs:return (0,None)
    a=np.array(rs);return (len(a),float(a.mean()))
F=json.load(open('/home/claude/journal-privat/forwardtest.json'));S={x['id']:x for x in F['strategien']}
res=[];ROWS={}
def one(sid):
    x=S[sid];c=x.get('cfg') or {}
    if c.get('typ')=='h4':tr,_=fwd.run4(x)
    elif sid in fwd.OBF or sid.startswith('fw2-w-'):tr,_=fwd.ob_fwd(sid) if sid in fwd.OBF else fwd.wob_fwd(sid)
    elif sid in fwd.FW:
        fn,kind,p=fwd.FW[sid];tr=[];busy={};P=fwd.P
        for (s,i,L) in sorted(fn(),key=lambda z:(P[z[0]]['ts'][z[1]],z[0])):
            if i<=busy.get(s,-1) or i+1>=len(P[s]['d']['c']):continue
            t=fwd.fsim(s,i,L,**p)
            if not t:continue
            t.update(sym=s,dir='long' if L else 'short',date=t['open_date']);busy[s]=i+t['bars']
            if t['closed']:tr.append(t)
    else:return None
    R=rows(tr);agree=[];dis=[];strong=[];weak=[];nof=[];base=[]
    for d,s,L,r in R:
        base.append(r);fs=fscore(s,d)
        if fs is None:nof.append(r);continue
        if fs*L>0:
            agree.append(r)
            if abs(fs)>=MED:strong.append(r)
        elif fs*L<0:dis.append(r)
        if abs(fs)<MED:weak.append(r)
    spl=lambda lst_rows,sel:[r for (d,s,L,r) in lst_rows if sel(d)]
    ROWS[sid]=[(str(d),sy,L,r,fscore(sy,d)) for d,sy,L,r in R]
    return dict(id=sid,name=x['name'],gruppe=x['gruppe'],alle=ev(base),mit=ev(agree),stark=ev(strong),gegen=ev(dis),ohneCOT=ev(nof))
ids=[i for i,x in S.items() if not x['gruppe'].startswith('Alter Test')]
for sid in ids:
    try:
        r=one(sid)
    except Exception as e:
        print('FEHLER',sid,repr(e)[:100],flush=True);continue
    if r:
        res.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
json.dump(res,open('/tmp/fx/fundall.json','w'),ensure_ascii=False)

json.dump(ROWS,open('/tmp/fx/rows.json','w'))
