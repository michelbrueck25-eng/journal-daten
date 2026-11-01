import warnings;warnings.filterwarnings('ignore')
from fund import *
import json,random
ev=list(csv.DictReader(open('/home/claude/journal-daten/wirtschaft.csv',encoding='utf-8')))
CM={'Australien':'AUD','Kanada':'CAD','Schweiz':'CHF','Eurozone':'EUR','Großbritannien':'GBP','Japan':'JPY','Neuseeland':'NZD','USA':'USD'}
def num(s):
    m=re.search(r'-?\d+(?:\.\d+)?',s.replace(',','')) if s else None
    return float(m.group()) if m else None
E=[]
for x in ev:
    c=CM.get(x['country']);a,f,p=num(x['actual']),num(x['forecast']),num(x['previous'])
    if not c or a is None or f is None:continue
    inv=-1 if 'Arbeitslosen' in x['title'] else 1
    s=np.sign(a-f)*inv
    ex=np.sign(f-p)*inv if p is not None else 0   # erwartete Richtung (Prognose gegen Vorwert)
    E.append(dict(d=dt.date.fromisoformat(x['date']),c=c,s=s,ex=ex,imp=x['impact'],t=x['title'],time=x['time']))
print('Ereignisse mit Ist+Prognose:',len(E),'Überraschung ≠0:',sum(1 for e in E if e['s']!=0),'Datenspanne',min(e['d'] for e in E),max(e['d'] for e in E))
# Tagesebene: je (Datum, Währung) ein Signal
def agg(key):
    D={}
    for e in E:D.setdefault((e['d'],e['c']),[]).append(e[key])
    return {k:int(np.sign(sum(v))) for k,v in D.items() if sum(v)!=0}
def leg(c):
    # Handelspaar gegen USD (USD gegen EUR)
    return ('USD','EUR') if c=='USD' else (c,'USD')
def mk(c,dirc,d0,hold,stop=2.0):
    a,b=leg(c); lng,sht=(a,b) if dirc>0 else (b,a)
    p=pair(lng,sht)
    return trade(p[0],p[1],d0,hold,stop) if p else None
def wd(d,n):  # n Handelstage zurueck/vor
    step=1 if n>0 else -1;k=abs(n)
    while k:
        d+=dt.timedelta(days=step)
        if d.weekday()<5:k-=1
    return d
sur=agg('s');exp_=agg('ex')
res=[]
def run(name,sigs,start_off,hold,sign=1,imp=None):
    tr=[]
    for (d,c),s in sigs.items():
        d0=wd(d,start_off) if start_off<0 else (d if start_off==0 else wd(d,start_off))
        t=mk(c,s*sign,d0,hold)
        if t:tr.append(t)
    x=summ(tr,name)
    if x:res.append(x)
    return tr
print('\n--- A) NACH der Nachricht: Überraschung folgen / kontern (Einstieg Open des Folgetags)')
for h in[1,3,5,10]:
    run(f'A folgen Überraschung, Folgetag, hold={h}',sur,1,h,1)
    run(f'A kontern Überraschung, Folgetag, hold={h}',sur,1,h,-1)
print('\n--- B) VORHER rein, Richtung = erwartete Veränderung (Prognose vs Vorwert), Ausstieg Ereignistag Close')
for n in[1,3,5]:
    run(f'B vorher {n}T in erwartete Richtung',exp_,-n,n,1)
    run(f'B vorher {n}T gegen erwartete Richtung',exp_,-n,n,-1)
print('\n--- C) Hindsight-Obergrenze: vorher rein in Richtung der späteren Überraschung (nicht handelbar)')
for n in[1,3,5]:
    run(f'C Hindsight {n}T vor Ereignis',sur,-n,n,1)
print('\n--- D) Vorher rein in erwartete Richtung, dann nach Ereignis halten (n Tage vorher bis 5 Tage danach)')
for n in[3,5]:
    run(f'D vorher {n}T, halten bis +5T',exp_,-n,n+5,1)
print('\n--- E) Nur starke Überraschung (|Ist-Prognose| relativ gross) folgen')
big={}
for e0,x in zip(E,[None]*len(E)):pass
json.dump(res,open('/tmp/fx/ev.json','w'))
