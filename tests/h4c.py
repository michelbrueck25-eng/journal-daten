from h4b import sg2,D,run,summ,pip,cut,itertools,np,pickle
sg=sg2(5,False,20,None)
out=[]
for sa,tg,N in itertools.product((3,4,5),(0.4,0.5,0.6,0.7),(18,24,36)):
    tr=run(sg,sa,tg,N);a=summ(tr)
    if a.get('n',0)<150: continue
    t=[x['t'] for x in tr];yrs=(max(t)-min(t))/864e5/365.25;rr=np.array([x['r'] for x in tr])
    dev=summ([x for x in tr if x['t']<cut]);te=summ([x for x in tr if x['t']>=cut])
    out.append((a['wr'],a['avg'],sa,tg,N,a['n'],round(rr.sum()/yrs,1),a['dd'],dev.get('avg'),te.get('avg')))
for o in sorted([o for o in out if o[0]>=68],key=lambda o:-o[1])[:8]: print(o)
