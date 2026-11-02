import warnings;warnings.filterwarnings('ignore')
from sweeps import *
import itertools
def eng_bull(d,i):return d['c'][i]>d['o'][i] and d['c'][i-1]<d['o'][i-1] and d['c'][i]>=d['o'][i-1] and d['o'][i]<=d['c'][i-1]
def eng_bear(d,i):return d['c'][i]<d['o'][i] and d['c'][i-1]>d['o'][i-1] and d['c'][i]<=d['o'][i-1] and d['o'][i]>=d['c'][i-1]
def go(tf,mode,flip,tgt,maxb,trendf=False):
    """mode 'kerze': Kerze sweept Hoch/Tief der Vorkerze und schliesst zurueck; flip=Fortsetzung statt Umkehr"""
    out=[]
    for s in SYMS:
        d=load(s,tf);A=atr(d);n=len(d['c']);D=[str(day(t)) for t in d['t']]
        sma=np.full(n,np.nan)
        for i in range(50,n):sma[i]=d['c'][i-50:i].mean()
        for i in range(51,n-1):
            if np.isnan(A[i]):continue
            for L,sw in((-1,d['h'][i]>d['h'][i-1] and d['c'][i]<d['h'][i-1]),(1,d['l'][i]<d['l'][i-1] and d['c'][i]>d['l'][i-1])):
                if not sw:continue
                Ld=-L if flip else L
                if trendf and (Ld>0)!=(d['c'][i-1]>sma[i]):continue
                stop=(d['h'][i] if L<0 else d['l'][i]) if not flip else (d['l'][i] if L<0 else d['h'][i])
                entry=d['o'][i+1];risk=abs(entry-stop)
                if risk<0.3*A[i] or risk>3*A[i] or (stop-entry)*Ld>0:continue
                r=sim(d,i+1,Ld,entry,stop,tgt,maxb,s)
                if r:out.append(dict(s=s,d=D[i],L=Ld,r=r[0]))
                break
    return out
def combo(htf,ltf,tgt,maxb=6,flip=False):
    """Hoehere Ebene (htf: 'D' oder 'W') Vorperioden-Hoch/Tief gesweept (Kerze schliesst zurueck), danach auf ltf (4H bzw. D) Engulfing in Umkehrrichtung; Einstieg naechstes Open, Stopp Extrem der Engulfing-Kerze"""
    out=[]
    for s in SYMS if ltf=='4H' else sorted(os.path.basename(f).split('_')[0] for f in glob.glob(f'{HOME}/marktdaten/*_D.json') if len(os.path.basename(f).split('_')[0])==6 and not os.path.basename(f).startswith('XAU')):
        try:H=load(s,htf);Lw=load(s,ltf)
        except Exception:continue
        A=atr(Lw);n=len(Lw['c']);ht=H['t']
        # HTF-Sweeps: Index der HTF-Kerze, die Hoch/Tief der Vorkerze sweept und zurueckschliesst; gueltig fuer die LTF-Kerzen NACH Schluss dieser Kerze fuer die naechsten k HTF-Perioden
        per=86400e3 if htf=='D' else 7*86400e3
        sw=[]
        for i in range(1,len(H['c'])):
            if H['h'][i]>H['h'][i-1] and H['c'][i]<H['h'][i-1]:sw.append((ht[i]+per,ht[i]+3*per,-1))
            if H['l'][i]<H['l'][i-1] and H['c'][i]>H['l'][i-1]:sw.append((ht[i]+per,ht[i]+3*per,1))
        used=set()
        for (t0,t1,L) in sw:
            k=bisect.bisect_left(Lw['t'],t0)
            for i in range(max(k,2),n-1):
                if Lw['t'][i]>=t1:break
                if np.isnan(A[i]):continue
                ok=eng_bull(Lw,i) if L>0 else eng_bear(Lw,i)
                if not ok:continue
                Ld=-L if flip else L
                stop=Lw['l'][i] if Ld>0 else Lw['h'][i];entry=Lw['o'][i+1];risk=abs(entry-stop)
                if risk<0.3*A[i] or risk>3*A[i] or (stop-entry)*Ld>0:continue
                r=sim(Lw,i+1,Ld,entry,stop,tgt,maxb,s)
                if r and (s,i) not in used:used.add((s,i));out.append(dict(s=s,d=str(day(Lw['t'][i])),L=Ld,r=r[0]))
                break
    return out
if __name__=='__main__':
    R=[]
    def P(tr,nm):
        x=rep(tr,nm);R.append(x) if x else None
    for tf,mb in(('W',4),('D',5),('4H',6)):
        for flip in(False,True):
            for tg in(1,2):
                for tr_ in(False,True):
                    P(go(tf,'k',flip,tg,mb,tr_),f'{tf} Kerze sweept Vorkerze, {"Fortsetzung" if flip else "Umkehr"}, Ziel {tg}R{", mit 50-SMA-Trend" if tr_ else ""}')
    for htf,ltf,mb in(('D','4H',6),('W','D',8)):
        for flip in(False,True):
            for tg in(1,2):
                P(combo(htf,ltf,tg,mb,flip),f'{htf}-Sweep dann {ltf}-Engulfing, {"Fortsetzung" if flip else "Umkehr"}, Ziel {tg}R')
    json.dump(R,open('/tmp/fx/sw2.json','w'))
