import sys,datetime as dt,numpy as np,bisect
sys.path.insert(0,'/tmp/ix')
import lvl
import cotstr2 as cotstr
from lvl import M,st
orig=cotstr.cotdir
NF=['GOLD','SPX','NDX','SILBER','OEL']
FX=[s for s,m in M.items() if m['fx']]
def pr(tag,tr):
    x=st(tr)
    if x:print(f'{tag:44} n{x[0]:5} E{x[1]:+.3f} dev{x[2]:+.3f} test{x[3]:+.3f} (n{x[4]}) Win{x[5]*100:.0f}%',flush=True)
# H1/H2: COT + fib79 nach Gruppe
for grp,sy in (('FX',FX),('Gold/Indizes/Silber/Öl',NF),('nur Rohstoffe',['GOLD','SILBER','OEL']),('nur Indizes',['SPX','NDX'])):
    for thr in (15,25):
        pr(f'H1/2 COT {thr} fib79 2R {grp}',cotstr.scan('fib79',thr,2.0,syms=sy))
        pr(f'H1   COT {thr} offen  2R {grp}',cotstr.scan('open',thr,2.0,syms=sy))
# H2 Stabilität: Ziel/Haltedauer
for tgt in (1.5,2.0,2.5,3.0):
    pr(f'H2 fib79 thr20 tgt{tgt} alle',cotstr.scan('fib79',20,tgt))
# H3: COT-Veränderung 8 Wochen
def chg(s,date,thr,w=8):
    d=(date-dt.timedelta(days=4)).isoformat();d0=(date-dt.timedelta(days=4+7*w)).isoformat()
    def g(cur):
        a,b=cotstr.ci(cur,d),cotstr.ci(cur,d0);return None if a is None or b is None else a-b
    if s in cotstr.CK:
        x=g(cotstr.CK[s])
    elif len(s)==6 and s!='GOLD':
        a,b=g(s[:3]),g(s[3:]);x=None if a is None or b is None else a-b
    else:return 0
    if x is None:return 0
    return 1 if x>=thr*2 else (-1 if x<=-thr*2 else 0)
cotstr.cotdir=chg
for thr in (25,35):
    for mode in ('open','fib79','fib62'):
        pr(f'H3 COT-Veränderung 8W {thr*2} {mode} 2R alle',cotstr.scan(mode,thr,2.0))
cotstr.cotdir=orig
