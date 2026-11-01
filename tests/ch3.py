src=open('challenge.py').read(); cut=src.rindex("if __name__=='__main__':"); exec(src[:cut])
import numpy as np
def phase(p,s,target,ddlim,dailylim=3.0,maxd=900):
    eq=0.0
    for k in range(min(maxd,len(p)-s)):
        v=p[s+k]
        if v<=-dailylim: return 'gerissen',k+1
        eq+=v
        if eq<=-ddlim: return 'gerissen',k+1
        if eq>=target: return 'pass',k+1
    return 'offen',None
def two(days,p,target,ddlim,step=7):
    n=len(p); out={'beide':0,'p1':0,'gerissen1':0,'gerissen2':0,'offen':0}; dur=[]; tot=0
    for s in range(0,n-300,step):
        tot+=1; r,d1=phase(p,s,target,ddlim)
        if r=='gerissen': out['gerissen1']+=1; continue
        if r=='offen': out['offen']+=1; continue
        r2,d2=phase(p,s+d1,target,ddlim)
        if r2=='pass': out['beide']+=1; dur.append(d1+d2)
        elif r2=='gerissen': out['gerissen2']+=1
        else: out['offen']+=1
    return {k:v/tot*100 for k,v in out.items()},(float(np.median(dur)) if dur else None)
for nm in ('Mischung 7 (Greedy)','o10 + fw6-p1','5er + o12'):
    w=PORT[nm]
    for lim in (6,10):
        print(f'--- {nm}: Phase 1 und 2 je +6 %, statischer Max-Verlust {lim} %, Tageslimit 3 %, kein Zeitlimit')
        for f in (1,1.5,2,3,4):
            days,p=daily({k:v*f for k,v in w.items()}); r,md=two(days,p,6,lim)
            print(f'  Faktor {f:3}: beide Phasen bestanden {r["beide"]:3.0f} % | gerissen in P1 {r["gerissen1"]:3.0f} % / P2 {r["gerissen2"]:3.0f} % | offen {r["offen"]:2.0f} % | Median gesamt {md} Tage')
