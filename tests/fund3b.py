import warnings;warnings.filterwarnings('ignore')
import sys;sys.argv=['x']
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from fund3 import *
print('--- B/C korrigiert: Ausstieg am Ende des Ereignistags (hold = n+1)')
for n in[0,1,3,5]:
    run(f'B vorher {n}T in erwartete Richtung (inkl. Ereignistag)',exp_,-n if n else 0,n+1,1)
    run(f'B vorher {n}T gegen erwartete Richtung',exp_,-n if n else 0,n+1,-1)
    run(f'C Hindsight {n}T (nicht handelbar)',sur,-n if n else 0,n+1,1)
print('--- D korrigiert: vorher n Tage bis +5 Tage nach Ereignis')
for n in[1,3,5]:
    run(f'D erwartete Richtung vorher {n}T, halten bis +5T',exp_,-n,n+6,1)
    run(f'D Hindsight vorher {n}T, bis +5T',sur,-n,n+6,1)
# nur high impact
sur_h={};exp_h={}
for e in E:
    if e['imp']=='high':
        sur_h.setdefault((e['d'],e['c']),[]).append(e['s']);exp_h.setdefault((e['d'],e['c']),[]).append(e['ex'])
sur_h={k:int(np.sign(sum(v))) for k,v in sur_h.items() if sum(v)!=0};exp_h={k:int(np.sign(sum(v))) for k,v in exp_h.items() if sum(v)!=0}
print('--- nur high impact')
for n in[1,3]:
    run(f'H erwartete Richtung vorher {n}T',exp_h,-n,n+1,1)
    run(f'H Hindsight vorher {n}T',sur_h,-n,n+1,1)
run('H folgen Überraschung Folgetag hold=3',sur_h,1,3,1)
run('H folgen Überraschung Folgetag hold=5',sur_h,1,5,1)
# Zinsentscheide
rs={}
for e in E:
    if 'Zinsentscheid' in e['t'] and e['s']!=0:rs[(e['d'],e['c'])]=int(e['s'])
print('Zinsentscheid-Überraschungen:',len(rs))
run('Z Zins-Überraschung folgen, hold=5',rs,1,5,1)
# kumulierte Überraschungen 20 Tage je Währung, wöchentlich Top gegen Flop
print('--- F) Überraschungs-Momentum: Summe der Überraschungen der letzten 28 Tage je Währung, Montag, Top vs Flop')
days=[dt.date(2026,1,5)+dt.timedelta(days=7*i) for i in range(45)]
for hold in[5,10,20]:
  for lb in[28,56]:
    tr=[]
    for d in days:
        if d>dt.date(2026,10,20):continue
        sc={c:sum(e['s'] for e in E if e['c']==c and d-dt.timedelta(days=lb)<=e['d']<d) for c in CCY}
        r=sorted(sc.items(),key=lambda z:z[1])
        if r[-1][1]==r[0][1]:continue
        p=pair(r[-1][0],r[0][0])
        if p:
            t=trade(p[0],p[1],d,hold)
            if t:tr.append(t)
    summ(tr,f'F Überraschungs-Momentum lb={lb} hold={hold} top1')
