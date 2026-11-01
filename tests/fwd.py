"""Forward-Engine: spielt die aktivierten Strategien deterministisch ueber die Marktdaten NACH dem Teststart.
Aufruf: python3 fwd.py   (schreibt journal-privat/forwardtest.json und die oeffentliche Kopie)"""
import json,sys,os,datetime as dt,numpy as np
os.chdir("/home/claude/journal-daten/tests"); sys.path.insert(0,"/home/claude/journal-daten/tests")
_t=open('/home/claude/journal-daten/tests/ideen6.py').read(); exec(_t[:_t.index('\nres=[]\ndef add(')])
from ideen2 import sig_cot
PRIV='/home/claude/journal-privat'; PUB='/home/claude/journal-daten'
START=dt.date.fromisoformat(os.environ.get('FW_START','2026-10-30')); ENDE=dt.date(2026,12,30)
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

# ---- 4h-Strategien (RSI(3)-Rücksetzer), Daten wie in h4.py ----
import h4 as H4
def sg4(th,minatr):
    out=[]
    for s,d in H4.D.items():
        n=len(d['c']);pp=H4.pip(s)
        for i in range(210,n-1):
            a=d['a'][i]
            if np.isnan(a) or np.isnan(d['sma200'][i]) or a/pp<minatr: continue
            c=d['c'][i];up=c>d['sma200'][i]
            if d['r3'][i]<th and up: out.append((s,i,True))
            elif d['r3'][i]>100-th and (not up): out.append((s,i,False))
    return out
def fsim4(s,i,L,sa,tg,N):
    d=H4.D[s];n=len(d['c']);a=d['a'][i]
    if i+1>=n or np.isnan(a): return None
    e=d['o'][i+1];sd=sa*a;sg=1 if L else -1;stp=e-sg*sd;tp=e+sg*tg*sd;mfe=mae=0.0;end=min(i+N,n-1);closed=False;bd=bp=0
    for j in range(i+1,end+1):
        hi,lo=d['h'][j],d['l'][j]
        if (lo<=stp) if L else (hi>=stp): px=stp;closed=True;why='Stopp';mae=min(mae,-1.0);break
        if (hi>=tp) if L else (lo<=tp): px=tp;closed=True;why='Ziel';mfe=max(mfe,tg);break
        mfe=max(mfe,sg*((hi if L else lo)-e)/sd);mae=min(mae,sg*((lo if L else hi)-e)/sd)
        pl=sg*(d['c'][j]-e)
        if pl<0: bd+=1
        elif pl>0: bp+=1
    else: j=end;px=d['c'][j]
    if not closed and j>=i+N: closed=True;why='Zeit'
    days=(d['t'][j]-d['t'][i+1])/864e5+0.17;r=sg*(px-e)/sd-H4.cost_r(s,sd,a,days)
    bars=round((j-i)/6,2);od=str(dt.datetime.fromtimestamp(d['t'][i+1]/1000,dt.timezone.utc))[:16]
    o=dict(closed=closed,r=round(float(r),3),mfe=round(float(mfe),2),mae=round(float(mae),2),bars=bars,bd=round(bd/6,2),bp=round(bp/6,2),entry=float(e),open_date=od)
    if closed: o.update(why=why,close_date=str(dt.datetime.fromtimestamp(d['t'][j]/1000,dt.timezone.utc))[:16])
    else: o.update(stop=float(stp),last=str(dt.datetime.fromtimestamp(d['t'][j]/1000,dt.timezone.utc))[:16])
    return o
def run4(x):
    c=x['cfg'];tr=[];op=[];busy={}
    for (s,i,L) in sorted(sg4(c['th'],c['minatr']),key=lambda z:(H4.D[z[0]]['t'][z[1]],z[0])):
        if i<=busy.get(s,-1): continue
        if i+1>=len(H4.D[s]['c']) or dt.datetime.fromtimestamp(H4.D[s]['t'][i+1]/1000,dt.timezone.utc).date()<START: continue
        t=fsim4(s,i,L,c['sa'],c['tg'],c['N'])
        if not t: continue
        t.update(sym=s,dir='long' if L else 'short',date=t['open_date']);busy[s]=i+int(round(t['bars']*6))
        (tr if t['closed'] else op).append(t)
    return tr,op
def _smc(nm,win):
    import io,contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        import smc2
    return smc2.filt(smc2.CAND[nm](),win)
FW.update({
 'fw9-s1':(lambda:_smc('Sweep 20',20),'pyr',dict(sa=3,tk=99,adds=(),red=None,N=15,tg=None)),
 'fw9-s2':(lambda:_smc('FVG Retest',20),'pyr',dict(sa=2,tk=99,adds=(),red=None,N=15,tg=None)),
 'fw9-s3':(lambda:_smc('OB nach BOS',20),'pyr',dict(sa=2,tk=99,adds=(),red=None,N=25,tg=None)),
})
OBF={'fw10-o1':('mid',0.1,5,20,'A',0,'alle'),'fw10-o2':('mid',0.25,3,10,'A',20,'FX'),'fw10-o3':('mid',0.25,2,20,'A',0,'FX'),'fw3-k1':('mid',0.25,3,10,'A',0,'alle'),'fw3-k2':('mid',0.5,3,7,'A',0,'alle','weekly_trend'),'fw3-k3':('edge',0.1,3,10,'A',0,'alle','cot_stark30')}
_OB={}
def ob_fwd(sid):
    """Daily-Orderblock-Forward: Zonen und Einstieg wie in obsearch.run, nur Trades mit Einstieg ab START."""
    if 'run' not in _OB:
        import io,contextlib
        t=open('/home/claude/journal-daten/tests/obsearch.py').read(); t=t[:t.index('rows=[]')]
        g={'__name__':'obsearch_fwd','__file__':'/home/claude/journal-daten/tests/dob.py'}
        with contextlib.redirect_stdout(io.StringIO()): exec(t,g)
        _OB['run']=g['run']
    tr=[];op=[]
    for x in sorted(_OB['run'](*OBF[sid]),key=lambda x:x['date']):
        if x['date']<str(START): continue
        t=dict(closed=not x['offen'],r=round(float(x['r']),3),bars=x['bars'],entry=x['entry'],open_date=x['date']+' 00:00',sym=x['sym'],dir='long' if x['L'] else 'short',date=x['date']+' 00:00',why={'SL':'Stopp','TP':'Ziel','Zeit':'Zeit'}[x['why']])
        if x['offen']: t['last']=x['last']+' 00:00'; op.append(t)
        else: t['close_date']=x['last']+' 00:00'; tr.append(t)
    return tr,op
def sig_saison(N=30,stopm=2.0,thr=0.75,minyrs=6,mean_min=0.05,step=3):
    """Saisonalitaets-Signale (wie seas2.run, Walk-forward) fuer die aktuellen Bars; Index in der P-Struktur dieser Datei."""
    import io,contextlib
    with contextlib.redirect_stdout(io.StringIO()): import seas2 as S2
    out=[]
    for s in S2.SYMS:
        RL,_=S2.sim_all(s,N,stopm,0,True); RS,_=S2.sim_all(s,N,stopm,0,False)
        md=S2.P[s]['md']; yr=S2.P[s]['yr']; n=len(yr); cell={}
        for i in range(n):
            m,dd=md[i]
            if dd>28 or (dd-1)%step: continue
            key=(m,(dd-1)//step*step+1); cell.setdefault(key,{})
            if yr[i] not in cell[key]: cell[key][yr[i]]=i
        y=max(set(yr)); ds={str(x):k for k,x in enumerate(P[s]['ts'])}
        sig=[]
        for key,byy in cell.items():
            past=[byy[yy] for yy in byy if yy<y]
            if len(past)<minyrs or y not in byy: continue
            for L,R in ((True,RL),(False,RS)):
                rs=np.array([R[i] for i in past]); rs=rs[~np.isnan(rs)]
                if len(rs)<minyrs: continue
                wr=(rs>0).mean()
                if wr>=thr and rs.mean()>=mean_min: sig.append((wr,rs.mean(),key,L))
        sig.sort(key=lambda x:(-x[0],-x[1]))
        for wr,mn,key,L in sig:
            j=ds.get(str(S2.P[s]['ts'][cell[key][y]]))
            if j is not None: out.append((s,j,L))
    return out
FW['fw4-s5']=(lambda:sig_saison(),'pyr',dict(sa=2,tk=99,adds=(),red=None,N=30,tg=None))
def wob_fwd(sid):
    """Weekly-Orderblock-Forward (fw2-w-<cot>-<ziel*10>-<tage>)"""
    import importlib.util
    if 'wob' not in _OB:
        sp=importlib.util.spec_from_file_location('wob','/home/claude/journal-daten/tests/wob.py'); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); _OB['wob']=m
    _,_,cot,tg,md=sid.split('-'); tr=[];op=[]
    for x in sorted(_OB['wob'].run(int(tg)/10,int(md),cot),key=lambda x:x['date']):
        if x['date']<str(START): continue
        t=dict(closed=not x['offen'],r=round(float(x['r']),3),bars=x['bars'],entry=x['entry'],open_date=x['date']+' 00:00',sym=x['sym'],dir='long' if x['L'] else 'short',date=x['date']+' 00:00',why={'SL':'Stopp','TP':'Ziel','Zeit':'Zeit'}[x['why']])
        if x['offen']: t['last']=x['last']+' 00:00'; op.append(t)
        else: t['close_date']=x['last']+' 00:00'; tr.append(t)
    return tr,op
def main():
    F=json.load(open(f'{PRIV}/forwardtest.json')); ex=json.load(open(f'{PRIV}/journal-export.json'))
    aktiv=[i for i in ex['forwardAktiv'] if i not in ex.get('forwardEntfernt',[])]+[i for i in os.environ.get('FW_FORCE','').split(',') if i]  # nur was in der App aktiv ist
    last=max(P[s]['ts'][-1] for s in P); S={x['id']:x for x in F['strategien']}; done=[];skip=[]
    for sid in aktiv:
        if sid in S and (S[sid].get('cfg') or {}).get('typ')=='h4':
            x=S[sid];tr,open_=run4(x);last=max(last,max(dt.date.fromtimestamp(d['t'][-1]/1000) for d in H4.D.values())) if False else last
            K=stats(tr);eq=[round(float(v),2) for v in np.cumsum([t['r'] for t in tr])] if tr else []
            x['forward']=dict(n=len(tr),offen=len(open_),equity=eq,kennzahlen=K,testStart=str(START),testEnde=str(ENDE),datenstand=str(max(dt.datetime.fromtimestamp(d['t'][-1]/1000,dt.timezone.utc).date() for d in H4.D.values())),offen_r=round(float(sum(t['r'] for t in open_)),2))
            x['offene']=open_;x['trades']=tr;x['status']='Forward-Test läuft';done.append(sid);continue
        if (sid in OBF or sid.startswith('fw2-w-')) and sid in S:
            tr,open_=ob_fwd(sid) if sid in OBF else wob_fwd(sid); x=S[sid]; K=stats(tr); eq=[round(float(v),2) for v in np.cumsum([t['r'] for t in tr])] if tr else []
            x['forward']=dict(n=len(tr),offen=len(open_),equity=eq,kennzahlen=K,testStart=str(START),testEnde=str(ENDE),datenstand=str(last),offen_r=round(float(sum(t['r'] for t in open_)),2))
            x['offene']=open_;x['trades']=tr;x['status']='Forward-Test läuft';done.append(sid);continue
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
    if os.environ.get('FW_DRY'):
        for i in aktiv:
            if i.startswith('fw8'): print(i,json.dumps(S[i]['forward']['kennzahlen']),len(S[i]['trades']),len(S[i]['offene']),(S[i]['trades'] or S[i]['offene'])[:1])
        print('DRY');return
    json.dump(F,open(f'{PRIV}/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
    G=dict(F);G['strategien']=[x for x in F['strategien'] if not x['gruppe'].startswith('Alter Test')]
    json.dump(G,open(f'{PUB}/forwardtest.json','w'),ensure_ascii=False,separators=(',',':'))
    print('Datenstand',last,'gelaufen',done,'ohne Engine',skip)
if __name__=='__main__': main()
