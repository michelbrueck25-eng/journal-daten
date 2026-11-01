exec(open('portfolio2.py').read().split("if __name__=='__main__':")[0])
import numpy as np,json
print(len(IDS),IDS)
dev={i:mvec(i,None,SP) for i in IDS}; full={i:mvec(i) for i in IDS}
info={}
for i in IDS:
    r=np.array([x[2] for x in tr[i]]);rd=np.array([x[2] for x in tr[i] if x[1]<SP])
    info[i]=dict(n=len(r),E=float(r.mean()),Ed=float(rd.mean()) if len(rd) else 0,nd=len(rd),var=float(r.var()))
# Mittelwert-Varianz auf Entwicklung, Kovarianz Richtung Diagonale geschrumpft
X=np.array([dev[i] for i in IDS]);mu=X.mean(1);C=np.cov(X);Cs=0.5*C+0.5*np.diag(np.diag(C))
def solve(cap=0.3):
    w=np.maximum(np.linalg.solve(Cs,mu),0)
    for _ in range(50):
        w=w/w.sum();w=np.minimum(w,cap)
    return dict(zip(IDS,w/w.max()))
ok=[i for i in IDS if info[i]['E']>=0.15 and info[i]['n']>=30]
print('ok',len(ok))
w0=solve()
w0={i:(v if i in ok else 0) for i,v in w0.items()}
m=max(w0.values());w0={i:(v if v>=0.04*m else 0) for i,v in w0.items()}
res={}
for lim in (6,10):
    # Skalierung auf Limit: Drawdown (gesamt) = 85 % des Limits
    s=stats(w0);f=0.85*lim/s['dd'];w={i:v*f for i,v in w0.items() if v*f>0.005}
    a=stats(w);b=stats(w,None,SP);c=stats(w,SP)
    print(f'--- Limit {lim} %: Faktor {f:.2f}, {len(w)} Strategien, Ertrag/Monat gesamt {a["mon"]:.2f} % DD {a["dd"]:.1f} worst {a["worst"]:.1f} | Entw {b["mon"]:.2f}/{b["dd"]:.1f} | Prüfung {c["mon"]:.2f}/{c["dd"]:.1f}')
    for i,v in sorted(w.items(),key=lambda a:-a[1]):print(f'   {i:10} Risiko je Trade {v:5.2f} % | E {info[i]["E"]:+.2f} n{info[i]["n"]} Kelly voll {info[i]["E"]/info[i]["var"]*100:5.1f} %')
    res[lim]=dict(w=w,all=a,dev=b,test=c)
import pickle;pickle.dump((res,info),open('/tmp/ix/opt.pkl','wb'))
