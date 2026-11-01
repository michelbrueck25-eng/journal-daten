"""Portfolio-Simulation ueber alle Daily-Strategien (E>=0,15 R): Waehrungs-Deckel, Doppelsignal-Regel, Monatsbremse, Gewichtung nach Qualitaet.
Alle Zahlen in R (1 R = Basisrisiko je Trade). Gewichte werden nur auf Daten VOR 2023 geschaetzt, Auswertung getrennt Entwicklung/Pruefung."""
import json,datetime as dt,numpy as np,itertools,sys
D='/home/claude/journal-daten'
B=json.load(open(f'{D}/backtest-trades.json')); F=json.load(open(f'{D}/forwardtest.json'))
TF={x['id']:x['tf'] for x in F['strategien']}
IDS=[k for k,v in B.items() if TF.get(k)=='Daily' and np.mean([t[3] for t in v])>=0.15]
SPLIT='2023-01-01'
def legs(sym,d):
    a,b=sym[:3],sym[3:]; return {a:d,b:-d}
T=[]
for k in IDS:
    for (d,s,L,r,bars) in B[k]:
        o=dt.date.fromisoformat(d); c=o+dt.timedelta(days=int(round((bars or 1)*7/5)))
        T.append(dict(sid=k,o=o,c=c,sym=s,dir=1 if L=='L' else -1,r=r))
T.sort(key=lambda t:(t['o'],t['sid']))
def weights(mode):
    if mode=='gleich': return {k:1.0 for k in IDS}
    dev={k:[t['r'] for t in T if t['sid']==k and str(t['o'])<SPLIT] for k in IDS}
    E={k:(np.mean(v) if len(v)>=8 else 0.15) for k,v in dev.items()}; m=np.mean(list(E.values()))
    return {k:float(np.clip(1+0.5*(E[k]/m-1),0.5,1.8)) for k in IDS}   # geschrumpft: nie volle Proportionalitaet
def run(cap=None,dedupe=False,brake=None,w=None,tmin=0.25):
    w=w or {k:1.0 for k in IDS}; openp=[]; out=[]; mon={}
    for t in T:
        openp=[p for p in openp if p['c']>t['o']]
        mk=(t['o'].year,t['o'].month)
        if brake is not None and sum(x['rw'] for x in out if (x['c'].year,x['c'].month)==mk and x['c']<=t['o'])<=-brake: continue
        if dedupe and any(p['sym']==t['sym'] and p['dir']==t['dir'] for p in openp): continue
        size=w[t['sid']]
        if cap is not None:
            for cur,sg in legs(t['sym'],t['dir']).items():
                used=sum(p['size']*legs(p['sym'],p['dir'])[cur] for p in openp if cur in legs(p['sym'],p['dir']))
                room=cap-used*sg if sg*used>=0 else cap+abs(used)   # gleiche Seite: Rest bis Deckel
                if sg*used>=0: room=cap-abs(used)
                size=min(size,max(room,0))
            if size<tmin*w[t['sid']]: continue
        x=dict(t,size=size,rw=t['r']*size); openp.append(x); out.append(x)
    return out
def kenn(tr,lo=None,hi=None):
    tr=[x for x in tr if (lo is None or str(x['c'])>=lo) and (hi is None or str(x['c'])<hi)]
    if not tr: return None
    m={}
    for x in tr: m[(x['c'].year,x['c'].month)]=m.get((x['c'].year,x['c'].month),0)+x['rw']
    ys=sorted(m); a=np.array([m[k] for k in ys]); eq=np.cumsum([x['rw'] for x in sorted(tr,key=lambda x:x['c'])])
    dd=float(max(np.maximum.accumulate(eq)-eq)); yrs=max((max(x['c'] for x in tr)-min(x['o'] for x in tr)).days/365.25,0.5); tot=float(eq[-1])
    return dict(n=len(tr),R=round(tot,1),Rj=round(tot/yrs,1),dd=round(dd,1),cal=round(tot/yrs/dd,2) if dd else 0,schlecht=round(float(a.min()),1),verl=int((a<0).sum()),mon=len(a),med=round(float(np.median(a)),1),ohneTop=round(tot-float(a.max()),1))
if __name__=='__main__':
    print(len(IDS),'Strategien',len(T),'Trades')
    V=[('A Basis: alles, Gewicht 1',dict()),
       ('B + Doppelsignal-Regel',dict(dedupe=True)),
       ('C + Waehrungsdeckel 2',dict(cap=2.0)),('C2 Deckel 3',dict(cap=3.0)),('C3 Deckel 1,5',dict(cap=1.5)),
       ('D Deckel 2 + Bremse 4 R',dict(cap=2.0,brake=4)),('D2 Deckel 2 + Bremse 6 R',dict(cap=2.0,brake=6)),
       ('E Deckel 2 + Doppel',dict(cap=2.0,dedupe=True)),
       ('F Deckel 2 + Bremse 4 + Gewichte',dict(cap=2.0,brake=4,wm='qual')),('G Deckel 2 + Gewichte',dict(cap=2.0,wm='qual'))]
    for nm,kw in V:
        kw=dict(kw); wm=kw.pop('wm','gleich'); tr=run(w=weights(wm),**kw)
        print(f'\n{nm}'); 
        for lab,lo,hi in (('gesamt',None,None),('Entw <2023',None,SPLIT),('Pruef >=2023',SPLIT,None)):
            k=kenn(tr,lo,hi); print('  ',lab.ljust(13),k)
    print('\nGewichte',{k:round(v,2) for k,v in weights('qual').items()})
