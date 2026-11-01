import re
src=open('challenge.py').read(); cut=src.rindex("if __name__=='__main__':"); exec(src[:cut])
for nm in ('Mischung 7 (Greedy)','5er + o12','o10 + fw6-p1'):
    w=PORT[nm]
    for lim,tgt in ((6,8),(10,10)):
        print(f'--- {nm}: Ziel +{tgt} %, Max-Verlust {lim} %, Tageslimit 3 %, bis 365 Tage')
        for f in (2,3,4,5):
            days,p=daily({k:v*f for k,v in w.items()}); r,md=sim(days,p,tgt,lim,maxd=365,step=7)
            mx=max(v*f for v in w.values())
            print(f'  Faktor {f}: bestanden {r["pass"]:3.0f} % | gerissen {r["dd"]+r["daily"]:3.0f} % | offen {r["zeit"]:2.0f} % | Median {md} Tage | max Risiko je Trade {mx:.1f} %')
