"""Weekly-OB nach Nutzerdefinition (Lag-In/Basis/Lag-Out auf Wochenkerzen), Einstieg auf Tageskerzen."""
exec(open('/home/claude/journal-daten/tests/strictbt.py').read().split("if __name__")[0])
UD,AD=U,A
def loadw(sym):
    f=f'{HOME}/marktdaten/{sym}_W.json'
    r=np.array(json.load(open(f))['rows'],float)
    return dict(t=r[:,0],o=r[:,1],h=r[:,2],l=r[:,3],c=r[:,4])
UW={s:loadw(s) for s in UD if s not in PIPS and os.path.exists(f'{HOME}/marktdaten/{s}_W.json')}
AW={s:atr(UW[s]) for s in UW}
U,A=UW,AW
ZW=[z for s in UW for z in strict(s,maxb=6)]
U,A=UD,AD
print('Weekly-Zonen',len(ZW),'Paare',len(UW))
def went(zs,mode,wait_weeks=12):
    out=[]
    for z in zs:
        s=z['sym']; d=UD[s]; L=z['L']; lo,hi=z['lo'],z['hi']; tW=UW[s]['t'][z['j']]+7*86400e3  # Lag-Out-Woche abgeschlossen
        top=z['bt'] if L else hi; bot=lo if L else z['bb']
        en={'ref_mid':(top+bot)/2,'ref_edge':top if L else bot,'ext_mid':(lo+hi)/2}[mode]
        st=lo-0.1*z['a'] if L else hi+0.1*z['a']
        q0=int(np.searchsorted(d['t'],tW))
        for q in range(max(q0,1),min(q0+wait_weeks*5,len(d['c'])-1)):
            if (d['c'][q]<lo) if L else (d['c'][q]>hi): break
            if (d['l'][q]<=en) if L else (d['h'][q]>=en):
                if (d['o'][q]<st) if L else (d['o'][q]>st): break
                out.append((s,q,L,en,st,dt.datetime.fromtimestamp(d['t'][q]/1000,dt.timezone.utc).strftime('%Y-%m-%d'))); break
    return out
VW={'alles 2R':([(1,2)],False),'alles 3R':([(1,3)],False),'alles 5R':([(1,5)],False),'alles 8R':([(1,8)],False),
 '50 % 2R, Rest 6R, BE':([(.5,2),(.5,6)],True),'50 % 1R, Rest 3R, BE':([(.5,1),(.5,3)],True)}
for mode in ('ref_mid','ref_edge','ext_mid'):
    ent=went(ZW,mode); ds=[e[5] for e in ent]; yrs=(dt.date.fromisoformat(max(ds))-dt.date.fromisoformat(min(ds))).days/365.25
    print(f'\n{mode}: n={len(ent)} ueber {yrs:.1f} J')
    for vn,(parts,be) in VW.items():
        r=np.array([psim(UD[s],q,L,en,st,parts,be,120,s) for s,q,L,en,st,dd in ent])
        a=np.array([x for x,e in zip(r,ent) if e[5]<SPL]); b=np.array([x for x,e in zip(r,ent) if e[5]>=SPL])
        print(f'  {vn:22s} E={r.mean():+.3f} R wr={100*(r>0).mean():.0f}% {r.sum()/yrs:+5.1f} R/Jahr dev={a.mean():+.2f} test={b.mean():+.2f}')
