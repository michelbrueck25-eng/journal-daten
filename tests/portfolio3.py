import sys,io,contextlib,pickle
exec(open('portfolio2.py').read().split("if __name__=='__main__':")[0])
import numpy as np
dev={i:mvec(i,None,SP) for i in IDS}
sd={i:float(dev[i][dev[i]!=0].std()) if (dev[i]!=0).sum()>3 else 9 for i in IDS}
def rp(sel): return {i:1/sd[i] for i in sel}
def sc(w,tgt,cap=1.0):
    w=scale_to(w,tgt,None,SP); m=max(w.values())
    if m>cap: w={k:v*cap/m for k,v in w.items()}     # kein Trade ueber cap %
    return w
def cal(sel,lo=None,hi=SP):
    w=rp(sel); s=stats(w,lo,hi); return s['jahr']/s['dd'] if s and s['dd']>0 else 0
# Greedy-Vorwaertsauswahl auf Entwicklung (Ertrag je Drawdown), max 8
sel=[]; best=0
for _ in range(8):
    c=max(((cal(sel+[i]),i) for i in IDS if i not in sel),default=None)
    if not c or c[0]<=best*1.03: break
    best,i=c; sel.append(i)
print('Greedy-Auswahl (Entwicklung):',sel,'Calmar Entw',round(best,2))
P5=['fw7-g1','fw7-h1','fw5-c1','fw7-a2','fw3-k3']
OBN=['fw10-o1','fw10-o9','fw10-o10','fw10-o11','fw10-o12','fw10-o13']
sets={'Empfehlung alt (5)':P5,'nur blaue Familie (o1,o9-o13)':OBN,'Greedy auf Entwicklung':sel,'alt + o9 + o12':P5+['fw10-o9','fw10-o12'],'alt + o12':P5+['fw10-o12']}
print()
for nm,ss in sets.items():
    w=rp(ss)
    for lab,lo,hi in (('Entw',None,SP),('Pruef',SP,None)):
        s=stats(w,lo,hi); print(f"{nm:30} {lab:5} Ertrag/Drawdown {s['jahr']/s['dd']:.2f}   R-Jahr {s['jahr']:.1f} DD {s['dd']:.1f}",end=' | ' if lab=='Entw' else '\n')
pickle.dump(dict(sel=sel,sets=sets),open('/tmp/pf/p3.pkl','wb'))
# Risiko-Skalierung fuer zwei Portfolios: Faktor auf Basis dev-DD=5 %
print('\nRisiko-Skalierung (Gewichte risk-parity, Basis: Entwicklung 5 % Max-Drawdown = Faktor 1, kein Trade ueber 2 %):')
for nm in ('Empfehlung alt (5)','Greedy auf Entwicklung','alt + o12'):
    base=scale_to(rp(sets[nm]),5.0,None,SP)
    for f in (0.5,1,1.5,2,3):
        w={k:min(v*f,2.0) for k,v in base.items()}
        a=stats(w,None,SP); b=stats(w,SP,None); full=stats(w)
        # laengste Phase unter dem Hoechststand (Monate), Gesamt
        ev=series(w); ds=sorted(ev); eq=np.cumsum([ev[d] for d in ds]); pk=np.maximum.accumulate(eq); under=0;mx=0;lastd=None
        for k,d in enumerate(ds):
            if eq[k]<pk[k]-1e-9: under+=1
            else: under=0
            mx=max(mx,under)
        print(f"{nm:24} Faktor {f:3} | Gesamt {full['mon']:.2f} %/Mon DD {full['dd']:.1f} schlechtester Mon {full['worst']:.1f} Verlustmon {full['neg']}/{full['nm']} | Pruefung {b['mon']:.2f} %/Mon DD {b['dd']:.1f} | max Tage unter Hoechststand ~{mx} Schlusstage")
