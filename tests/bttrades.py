"""Backtest-Trades je Strategie (Datum, Paar, Richtung, R, Tage) fuer die Monatsansicht der App. Nutzt die Forward-Engine mit Start 2010."""
import os,sys,json,io,contextlib
os.environ['FW_START']='2010-01-01'
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'.')
with contextlib.redirect_stdout(io.StringIO()):
    import fwd
import numpy as np
from fwd import *
F=json.load(open(f'{PRIV}/forwardtest.json')); out={}
for x in F['strategien']:
    sid=x['id']; tr=[]
    if (x.get('cfg') or {}).get('typ')=='h4':
        t4,_=run4(x); tr=t4
    elif sid in FW:
        fn,kind,p=FW[sid]; busy={}
        for (s,i,L) in sorted(fn(),key=lambda z:(P[z[0]]['ts'][z[1]],z[0])):
            if i<=busy.get(s,-1) or i+1>=len(P[s]['d']['c']): continue
            t=fsim(s,i,L,**p)
            if not t: continue
            t.update(sym=s,dir='long' if L else 'short',date=t['open_date']); busy[s]=i+t['bars']
            if t['closed']: tr.append(t)
    else: continue
    out[sid]=[[str(t['open_date'])[:10],t['sym'],'L' if t['dir']=='long' else 'S',round(float(t['r']),2),round(float(t['bars'])) if t.get('bars') is not None else None] for t in tr]
    print(sid,len(tr),round(sum(t['r'] for t in tr),1),flush=True)
json.dump(out,open('../backtest-trades.json','w'),separators=(',',':'),ensure_ascii=False)
print('fertig',len(out),os.path.getsize('../backtest-trades.json'))
