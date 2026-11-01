import sys,json,random,numpy as np,io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from smc import *
    _t=open('ideen6.py').read(); exec(_t[:_t.index('\nres=[]\ndef add(')])
bias={}
for (s,i,L) in S_cot('comm',156,1,'folgen',70)+S_gold(104,'Umkehr',20):
    bias.setdefault(s,[]).append((i,L))
def filt(sg,win):
    out=[]
    for (s,i,L) in sg:
        for (j,Lb) in bias.get(s,[]):
            if j<=i<=j+win and Lb==L: out.append((s,i,L));break
    return out
if __name__=='__main__':
    res=[]
    for nm,fn in CAND.items():
        sg0=fn()
        for win in (20,40):
            sg=filt(sg0,win)
            if len(sg)<60: continue
            rows=[]
            for sa in (2,3):
                for tg in (None,1.5,2):
                    for N in (15,25,40):
                        tr=runsig(sg,sa,tg,N);a,dv,te=summ(tr)
                        if a.get('avg') is None or a['n']<60: continue
                        rows.append((a['avg'],sa,tg,N,a,dv,te))
            rows.sort(key=lambda x:-x[0])
            print(nm,'COT-Fenster',win,len(sg),flush=True)
            for r in rows[:2]: print('   ',r[1:4],r[4],'dev',r[5].get('avg'),r[5].get('n'),'test',r[6].get('avg'),r[6].get('n'),flush=True)
