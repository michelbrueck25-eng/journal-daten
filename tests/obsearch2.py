import sys,os,io,contextlib,json,itertools,datetime as dt,pickle,numpy as np
os.chdir('/home/claude/journal-daten/tests'); sys.path.insert(0,'.')
t=open('obsearch.py').read(); t=t[:t.index('rows=[]')]
g={'__name__':'o2','__file__':'/home/claude/journal-daten/tests/dob.py'}
with contextlib.redirect_stdout(io.StringIO()): exec(t,g)
run=g['run']; st=g['st']; SP='2023-01-01'
F=json.load(open('../forwardtest.json')); S={x['id']:x for x in F['strategien']}
def kmon(i):
    m={}
    for a in S[i]['backtest']['monate']: k=(dt.date(1970,1,1)+dt.timedelta(days=a[0])).strftime('%Y-%m'); m[k]=m.get(k,0)+a[2]
    return m
have=['fw3-k1','fw3-k2','fw3-k3','fw10-o1','fw10-o2','fw10-o3']; HM={i:kmon(i) for i in have}
rows=[]
for flt,en,sb,tg,md,age,grp in itertools.product(('weekly_trend','cot_stark30'),('edge','mid'),(0.1,0.25,0.5),(3,4,5),(7,10,20),(0,20),('alle','FX')):
    tr=run(en,sb,tg,md,'A',age,grp,flt); a=st(tr)
    if not a or a[0]<200: continue
    dv=st([x for x in tr if x['date']<SP]); te=st([x for x in tr if x['date']>=SP])
    if not dv or not te: continue
    rows.append((min(dv[1],te[1]),(en,sb,tg,md,'A',age,grp,flt),a,dv,te,tr))
rows.sort(key=lambda x:-x[0]); print(len(rows),'Varianten mit Filter, n>=200')
def mon(tr):
    m={}
    for x in tr: m[x['date'][:7]]=m.get(x['date'][:7],0)+x['r']
    return m
top=[r for r in rows if r[0]>=0.25 and r[2][0]>=240][:80]; print(len(top),'mit min>=0,25 und n>=300')
ks=sorted(set().union(*[mon(r[5]) for r in top],*HM.values())); V=lambda m:np.array([m.get(k,0) for k in ks])
ref=[V(m) for m in HM.values()]; sel=[]
for r in top:
    v=V(mon(r[5]))
    if all(abs(np.corrcoef(v,x)[0,1])<0.92 for x in ref) and all(abs(np.corrcoef(v,V(mon(s[5])))[0,1])<0.92 for s in sel): sel.append(r)
    if len(sel)==5: break
for r in sel:
    v=V(mon(r[5])); print(f'{r[0]:+.3f}',r[1],'n%d E%+.3f'%r[2][:2],'Entw n%d %+.3f'%r[3][:2],'Pruef n%d %+.3f'%r[4][:2],'Korr max zu vorhandenen %.2f'%max(np.corrcoef(v,x)[0,1] for x in ref))
pickle.dump([(r[0],r[1],r[2],r[3],r[4]) for r in sel],open('/tmp/pf/obsel2.pkl','wb'))
