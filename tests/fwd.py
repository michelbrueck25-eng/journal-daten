"""Forward-Engine: spielt die aktivierten Strategien deterministisch ueber die Marktdaten NACH dem Teststart.
Aufruf: python3 fwd.py   (schreibt journal-privat/forwardtest.json und die oeffentliche Kopie)"""
import json,sys,os,datetime as dt,numpy as np
os.chdir("/home/claude/journal-daten/tests"); sys.path.insert(0,"/home/claude/journal-daten/tests")
_t=open('/home/claude/journal-daten/tests/ideen6.py').read(); exec(_t[:_t.index('\nres=[]\ndef add(')])
from ideen2 import sig_cot
PRIV='/home/claude/journal-privat'; PUB='/home/claude/journal-daten'
START=dt.date(2026,10,30); ENDE=dt.date(2026,12,30)
A2=((1,.5),(2,.5))
FW={ # id: (Signalfunktion, Art, Parameter)
 'fw5-c1':(lambda:sig_cot(156,1,'folgen',70),'pyr',dict(sa=3,tk=99,adds=(),red=None,N=20,tg=None)),
 'fw5-c2':(lambda:sig_cot(156,2,'folgen',70),'pyr',dict(sa=4,tk=99,adds=(),red=None,N=40,tg=None)),
 'fw6-d1':(lambda:S_cot('comm',156,1,'folgen',50,delta=8),'pyr',dict(sa=4,tk=99,adds=(),red=None,N=40,tg=None)),
 'fw6-p1':(lambda:S_cot('comm',156,1,'folgen',70),'pyr',dict(sa=3,tk=99,adds=(),red=None,N=15,tg=None)),
 'fw6-p2':(lambda:S_cot('comm',156,1,'folgen',70),'pyr',dict(sa=6,tk=99,adds=(),red=None,N=40,tg=4)),
 'fw6-g1':(lambda:S_gold(104,'Umkehr',20),'pyr',dict(sa=3,tk=99,adds=(),red=None,N=20,tg=None)),
 'fw7-a1':(lambda:S_cot('comm',156,1,'folgen',70),'pyr',dict(sa=3,tk=6,adds=A2,red=None,N=40,tg=None)),
 'fw7-a2':(lambda:S_cot('comm',156,2,'folgen',70),'pyr',dict(sa=3,tk=6,adds=A2,red=(5,0),N=40,tg=None)),
 'fw7-g1':(lambda:S_gold(104,'Umkehr',20),'pyr',dict(sa=3,tk=4,adds=(),red=None,N=20,tg=None)),
 'fw7-h1':(lambda:S_gold(156,'Umkehr',20),'pyr',dict(sa=3,tk=99,adds=(),red=None,N=15,tg=0.4)),
}
def fsim(s,i,L,sa,tk,adds,red,N,tg):
    """Wie pyr()/sim(), aber mit offenem Ende (letzte vorhandene Kerze). Rueckgabe dict."""
    d=P[s]['d']; n=len(d['c']); a=P[s]['a'][i]; ts=P[s]['ts']
    if i+1>=n or np.isnan(a): return None
    e=d['o'][i+1]; sd=sa*a; sg=1 if L else -1; stp=e-sg*sd; tp=None if not tg else e+sg*tg*sd
    units=[[e,1.0,i+1]]; ext=e; todo=list(adds); real=0.0; cost=0.0; reduced=False; closed=False; mfe=0.0; mae=0.0; bd=bp=0; end=min(i+N,n-1); j=i+1
    def cal(u,jj): return (ts[jj]-ts[u[2]]).days
    for j in range(i+1,end+1):
        hi,lo,cl=d['h'][j],d['l'][j],d['c'][j]
        if (lo<=stp) if L else (hi>=stp):
            real+=sum(u[1]*sg*(stp-u[0])/sd for u in units); cost+=sum(u[1]*cost_r(s,sd,a,cal(u,j)) for u in units); units=[]; closed=True; why='Stopp'; mae=min(mae,sg*(stp-e)/sd); break
        if tp is not None and ((hi>=tp) if L else (lo<=tp)):
            real+=sum(u[1]*sg*(tp-u[0])/sd for u in units); cost+=sum(u[1]*cost_r(s,sd,a,cal(u,j)) for u in units); units=[]; closed=True; why='Ziel'; mfe=max(mfe,tg); break
        for (lv,sz) in list(todo):
            lvp=e+sg*lv*sd
            if ((hi>=lvp) if L else (lo<=lvp)) and j>i+1: units.append([lvp,sz,j]); todo.remove((lv,sz))
        mfe=max(mfe,sg*((hi if L else lo)-e)/sd); mae=min(mae,sg*((lo if L else hi)-e)/sd)
        ext=max(ext,hi) if L else min(ext,lo); stp=max(stp,ext-tk*a) if L else min(stp,ext+tk*a)
        pl=sg*(cl-e)/sd
        if pl<0: bd+=1
        elif pl>0: bp+=1
        if red and not reduced and j-(i+1)==red[0] and pl<red[1]:
            real+=sum(0.5*u[1]*sg*(cl-u[0])/sd for u in units); cost+=sum(0.5*u[1]*cost_r(s,sd,a,cal(u,j)) for u in units)
            for u in units: u[1]*=0.5
            reduced=True
    if not closed:
        px=d['c'][j]
        if j>=i+N: # Zeitausstieg
            real+=sum(u[1]*sg*(px-u[0])/sd for u in units); cost+=sum(u[1]*cost_r(s,sd,a,cal(u,j)) for u in units); units=[]; closed=True; why='Zeit'
        else:
            mtm=sum(u[1]*sg*(px-u[0])/sd for u in units)-sum(u[1]*cost_r(s,sd,a,cal(u,j)) for u in units)
            return dict(closed=False,r=round(float(real-cost+mtm),3),mfe=round(float(mfe),2),mae=round(float(mae),2),bars=j-i,bd=bd,bp=bp,entry=float(e),stop=float(stp),open_date=str(ts[i+1]),last=str(ts[j]),size=sum(u[1] for u in units))
    return dict(closed=True,why=why,r=round(float(real-cost),3),mfe=round(float(mfe),2),mae=round(float(mae),2),bars=j-i,bd=bd,bp=bp,entry=float(e),open_date=str(ts[i+1]),close_date=str(ts[j]))
def stats(tr):
    if not tr: return dict(n=0)
    r=np.array([x['r'] for x in tr]); w=r[r>0]; l=r[r<=0]; eq=np.cumsum(r); h=np.array([x['bars'] for x in tr],float)
    streak=m=0
    for v in r:
        streak=streak+1 if v<=0 else 0; m=max(m,streak)
    tb=sum(x['bars'] for x in tr)
    return dict(n=len(r),wr=round(float((r>0).mean()*100),1),avg=round(float(r.mean()),3),pf=round(float(w.sum()/max(1e-9,abs(l.sum()))),2) if len(l) else None,
      avg_gewinn=round(float(w.mean()),2) if len(w) else None,avg_verlust=round(float(l.mean()),2) if len(l) else None,summe_r=round(float(r.sum()),2),
      dd=round(float((np.maximum.accumulate(np.r_[0,eq])[1:]-eq).max()),2),haltedauer=round(float(h.mean()),1),
      halt_gewinner=round(float(np.mean([x['bars'] for x in tr if x['r']>0])),1) if len(w) else None,halt_verlierer=round(float(np.mean([x['bars'] for x in tr if x['r']<=0])),1) if len(l) else None,
      zeit_drawdown_pct=round(100*sum(x['bd'] for x in tr)/max(1,tb),1),zeit_gewinn_pct=round(100*sum(x['bp'] for x in tr)/max(1,tb),1),
      mfe=round(float(np.mean([x['mfe'] for x in tr])),2),mae=round(float(np.mean([x['mae'] for x in tr])),2),max_verlustserie=m)
def main():
    F=json.load(open(f'{PRIV}/forwardtest.json')); ex=json.load(open(f'{PRIV}/journal-export.json'))
    aktiv=[i for i in ex['forwardAktiv'] if i not in ex.get('forwardEntfernt',[])]
    last=max(P[s]['ts'][-1] for s in P); S={x['id']:x for x in F['strategien']}; done=[];skip=[]
    for sid in aktiv:
        if sid not in FW: skip.append(sid); continue
        fn,kind,p=FW[sid]; x=S[sid]; tr=[];open_=[];busy={}
        for (s,i,L) in sorted(fn(),key=lambda z:(P[z[0]]['ts'][z[1]],z[0])):
            if i<=busy.get(s,-1): continue
            if i+1>=len(P[s]['d']['c']): continue
            if P[s]['ts'][i+1]<START: continue
            t=fsim(s,i,L,**p)
            if not t: continue
            t.update(sym=s,dir='long' if L else 'short',date=t['open_date']); busy[s]=i+t['bars']
            (tr if t['closed'] else open_).append(t)
        K=stats(tr); eq=[round(float(v),2) for v in np.cumsum([t['r'] for t in tr])] if tr else []
        x['forward']=dict(n=len(tr),offen=len(open_),equity=eq,kennzahlen=K,testStart=str(START),testEnde=str(ENDE),datenstand=str(last),
                          offen_r=round(float(sum(t['r'] for t in open_)),2))
        x['offene']=open_; x['trades']=tr; x['status']='Forward-Test läuft' if str(last)<=str(ENDE) else 'Testphase beendet'; done.append(sid)
    F['stand']=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M'); F['forwardDatenstand']=str(last)
    json.dump(F,open(f'{PRIV}/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
    G=dict(F);G['strategien']=[x for x in F['strategien'] if not x['gruppe'].startswith('Alter Test')]
    json.dump(G,open(f'{PUB}/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
    print('Datenstand',last,'gelaufen',done,'ohne Engine',skip)
if __name__=='__main__': main()
