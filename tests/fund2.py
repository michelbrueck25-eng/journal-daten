import warnings;warnings.filterwarnings('ignore')
from fund import *
import json
def comb_scores(k,wl):
    a=cot_scores('cn',k);b=cot_scores('nn',k);out={}
    for d in a:
        if d not in b:continue
        i=dates.index(d);sc={}
        for c in CCY:
            if c not in a[d] or c not in b[d]:continue
            v=[cot[c][x]['cn'] for x in dates[max(0,i-155):i+1]];rg=max(v)-min(v)
            lvl=(cot[c][d]['cn']-min(v))/rg*100-50 if rg else 0
            sc[c]=a[d][c]-b[d][c]+wl*lvl/2
        out[d]=sc
    return out
def run_sc(S,hold,topn,stop=2.0,thr=0):
    tr=[]
    for d,sc in S.items():
        d0=dt.date.fromisoformat(d)+dt.timedelta(days=6)
        ranked=[]
        for a,b in itertools.combinations(CCY,2):
            if a in sc and b in sc:ranked.append((abs(sc[a]-sc[b]),a,b,sc[a]-sc[b]))
        ranked.sort(reverse=True)
        for g,a,b,diff in ranked[:topn]:
            if g<thr:continue
            lng,sht=(a,b) if diff>0 else (b,a);p=pair(lng,sht)
            if p:
                t=trade(p[0],p[1],d0,hold,stop)
                if t:tr.append(t)
    return tr
if __name__=='__main__':
    R=[]
    for k in[2,4,8]:
      for wl in[0,1]:
        S=comb_scores(k,wl)
        for hold in[10,20]:
          for topn in[1,3,6]:
            x=summ(run_sc(S,hold,topn),f'COMB k={k} Niveau={wl} hold={hold} top{topn}')
            if x:R.append(x)
    json.dump(R,open('/tmp/fx/comb.json','w'))
