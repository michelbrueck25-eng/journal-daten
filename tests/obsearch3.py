import sys,os,io,contextlib,json,itertools,datetime as dt,pickle,numpy as np
os.chdir('/home/claude/journal-daten/tests'); sys.path.insert(0,'.')
t=open('obsearch.py').read(); t=t[:t.index('rows=[]')]
g={'__name__':'o3','__file__':'/home/claude/journal-daten/tests/dob.py'}
with contextlib.redirect_stdout(io.StringIO()): exec(t,g)
run=g['run']; st=g['st']; SP='2023-01-01'
def mon(tr):
    m={}
    for x in tr: m[x['date'][:7]]=m.get(x['date'][:7],0)+x['r']
    return m
blue=run('mid',0.1,5,20,'A',0,'alle'); BM=mon(blue)
rows=[]
for flt,sb,tg,md,age,grp in itertools.product(('','weekly_trend'),(0.05,0.1,0.15),(5,6,8,10),(20,30,40,60),(0,20,40),('alle','FX','Metall')):
    if flt and grp=='Metall': continue
    c=('mid',sb,tg,md,'A',age,grp,flt); tr=run(*c); a=st(tr)
    if not a or a[0]<300: continue
    dv=st([x for x in tr if x['date']<SP]); te=st([x for x in tr if x['date']>=SP])
    if not dv or not te: continue
    rows.append((min(dv[1],te[1]),c,a,dv,te,tr))
rows.sort(key=lambda x:-x[0]); print(len(rows),'Varianten n>=300')
for r in rows[:12]: print(f'{r[0]:+.3f}',r[1],'n%d E%+.3f wr%.0f'%r[2],'Entw %+.3f Pruef %+.3f'%(r[3][1],r[4][1]))
ex=[]
for l in ('fw3-k1','fw3-k2','fw3-k3','fw10-o1','fw10-o2','fw10-o3','fw10-o4','fw10-o5','fw10-o6','fw10-o7','fw10-o8'): pass
top=[r for r in rows if r[0]>=0.25 and r[1]!=('mid',0.1,5,20,'A',0,'alle','')]
ks=sorted(set().union(BM,*[mon(r[5]) for r in top])); V=lambda m:np.array([m.get(k,0) for k in ks]); vb=V(BM); sel=[]
for r in top:
    v=V(mon(r[5]))
    if np.corrcoef(v,vb)[0,1]>0.97: continue
    if all(abs(np.corrcoef(v,V(mon(s[5])))[0,1])<0.93 for s in sel): sel.append(r)
    if len(sel)==5: break
print('Auswahl:')
for r in sel: print(f'{r[0]:+.3f}',r[1],'n%d E%+.3f wr%.0f'%r[2],'Entw n%d %+.3f Pruef n%d %+.3f'%(r[3][0],r[3][1],r[4][0],r[4][1]),'Korr zu blau %.2f'%np.corrcoef(V(mon(r[5])),vb)[0,1],'R/Jahr',round(sum(x['r'] for x in r[5])/11.5,1))
pickle.dump([(r[0],r[1],r[2],r[3],r[4]) for r in sel],open('/tmp/pf/obsel3.pkl','wb'))
