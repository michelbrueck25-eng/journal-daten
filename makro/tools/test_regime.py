import random,math,unittest
from regime import *
def series(kind,n=300,seed=1):
    r=random.Random(seed);p=100;o=[];h=[];l=[];c=[]
    for i in range(n):
        d={'up':0.25,'down':-0.25,'range':0}[kind]
        if kind=='range': d=-(p-100)*0.15
        q=p+d+r.gauss(0,.4);o.append(p);h.append(max(p,q)+abs(r.gauss(0,.2)));l.append(min(p,q)-abs(r.gauss(0,.2)));c.append(q);p=q
    return o,h,l,c
class T(unittest.TestCase):
    def test_up(self):
        R=regime(*series('up'));self.assertGreater(sum(1 for x in R[100:] if x==1)/len(R[100:]),.8)
    def test_down(self):
        R=regime(*series('down'));self.assertGreater(sum(1 for x in R[100:] if x==-1)/len(R[100:]),.8)
    def test_range(self):
        R=regime(*series('range'));self.assertLess(sum(1 for x in R[100:] if x!=0)/len(R[100:]),.35)
    def test_warmup(self):
        R=regime(*series('up'));self.assertTrue(all(x is None for x in R[:60]))
    def test_no_lookahead(self):
        o,h,l,c=series('up',300,3);a=regime(o,h,l,c)
        b=regime(o[:200],h[:200],l[:200],c[:200]);self.assertEqual(a[:200],b)
    def test_profile(self):
        o,h,l,c=series('range',300,4);v=[1]*300
        poc,vah,val=profile(h,l,v,299)
        self.assertTrue(val<=poc<=vah)
        hi=max(h[180:300]);lo=min(l[180:300]);self.assertTrue(lo<=val and vah<=hi)
    def test_va_share(self):
        o,h,l,c=series('range',300,5);v=[random.Random(i).random()+.5 for i in range(300)]
        poc,vah,val=profile(h,l,v,299,bins=30)
        self.assertTrue(vah-val>0)
    def test_poc_concentrated(self):
        h=[101]*50+[100.5]*100;l=[99]*50+[100.2]*100;v=[1]*150
        poc,vah,val=profile(h,l,v,149,n=150)
        self.assertTrue(100.2<=poc<=100.5)
    def test_profile_no_lookahead(self):
        o,h,l,c=series('up',300,6);v=[1]*300
        a=profile(h,l,v,150);h2=h[:151]+[999]*149;l2=l[:151]+[0]*149
        self.assertEqual(a,profile(h2,l2,v,150))
unittest.main(verbosity=0)
