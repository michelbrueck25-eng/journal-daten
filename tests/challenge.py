import pickle,json,datetime as dt,numpy as np,collections
exec(open('portfolio2.py').read().split("if __name__=='__main__':")[0])
res=pickle.load(open('/tmp/pf/p2.pkl','rb')); sel5,w0=res[('Top 5','riskparity')]
base5={i:min(v,1.0) for i,v in w0.items()}
sd={i:float(mvec(i)[mvec(i)!=0].std()) for i in IDS}
def rpw(ids,sc): 
    w={i:1/sd[i] for i in ids}; m=max(w.values()); return {i:v/m*sc for i,v in w.items()}
PORT={'5er Empfehlung':base5,
 '5er + o12':{**base5,'fw10-o12':0.12},
 'o10 + fw6-p1':{'fw10-o10':0.2,'fw6-p1':1.0},
 'Mischung 7 (Greedy)':rpw(['fw7-h1','fw10-o10','fw5-c1','fw10-o12','fw7-g1','fw6-p1','fw7-a2'],1.0)}
def daily(w):
    ev=series(w); d0=dt.date.fromisoformat(min(ev)); d1=dt.date.fromisoformat(max(ev)); days=[]; x=d0
    while x<=d1: days.append(x); x+=dt.timedelta(days=1)
    return days,np.array([ev.get(x.isoformat(),0.0) for x in days])
def sim(days,p,target,ddlim,dailylim=3.0,maxd=120,step=5):
    out=collections.Counter(); dur=[]
    for s in range(0,len(p)-maxd,step):
        eq=0.0; res='zeit'
        for k in range(maxd):
            v=p[s+k]
            if v<=-dailylim: res='daily'; break
            eq+=v
            if eq<=-ddlim: res='dd'; break
            if eq>=target: res='pass'; dur.append(k+1); break
        out[res]+=1
    n=sum(out.values()); return {r:out[r]/n*100 for r in ('pass','dd','daily','zeit')},(float(np.median(dur)) if dur else None)
if __name__=='__main__':
    for nm,w in PORT.items():
        for lim,tgt in ((6,8),(10,10)):
            print(f'--- {nm}: Phase 1 Ziel +{tgt} %, Max-Verlust {lim} %, Tageslimit 3 % (Start alle 5 Tage seit 2019, max 120 Tage)')
            for f in (0.5,1,1.5,2,3):
                days,p=daily({k:v*f for k,v in w.items()}); r,md=sim(days,p,tgt,lim)
                print(f'  Faktor {f:3}: bestanden {r["pass"]:4.0f} % | Limit gerissen {r["dd"]+r["daily"]:3.0f} % (Tageslimit {r["daily"]:2.0f}) | noch offen {r["zeit"]:3.0f} % | Median Tage bis Ziel {md}')
