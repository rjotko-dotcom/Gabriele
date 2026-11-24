import numpy as np, wave, sys
sr=44100; T=15.0; n=int(sr*T); t=np.arange(n)/sr
out=np.zeros((n,2))
rng=np.random.default_rng(3)
def add(sig,at,gain=1.0,pan=0.0):
    i=int(at*sr); j=min(n,i+len(sig)); s=sig[:j-i]*gain
    out[i:j,0]+=s*(1-pan)/1; out[i:j,1]+=s*(1+pan)/1
def env(L,a,d): x=np.arange(L)/sr; return np.minimum(1,x/max(a,1e-4))*np.exp(-x/d)
def lp(x,k):  # one-pole lowpass
    y=np.zeros_like(x); c=0.0
    for i in range(len(x)): c+=k*(x[i]-c); y[i]=c
    return y
def kick(g=1.0):
    L=int(.5*sr); x=np.arange(L)/sr; f=45+120*np.exp(-x*30)
    return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-x*7)*g
def hat():
    L=int(.08*sr); w=rng.standard_normal(L); w=w-lp(w,.6); return w*env(L,.001,.018)*.25
def impact():
    L=int(2.5*sr); x=np.arange(L)/sr; f=30+80*np.exp(-x*8)
    sub=np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-x*1.6)
    nz=lp(rng.standard_normal(L),.15)*np.exp(-x*5)*.8
    return (sub*1.1+nz)
def whoosh(dur,rev=False):
    L=int(dur*sr); w=rng.standard_normal(L); k=np.linspace(.01,.35,L)
    y=np.zeros(L); c=0
    for i in range(L): c+=k[i]*(w[i]-c); y[i]=c
    e=np.sin(np.linspace(0,np.pi,L))**2 if not rev else np.linspace(0,1,L)**3
    return y*e*.9
def pad(f0s,dur,g):
    L=int(dur*sr); x=np.arange(L)/sr; y=np.zeros(L)
    for f in f0s:
        for d in (-0.15,0,0.15):
            ph=rng.uniform(0,6.28); y+=np.sign(np.sin(2*np.pi*(f+d)*x+ph))*0.3+np.sin(2*np.pi*(f+d)*x+ph)
    y=lp(y,.02); e=np.minimum(1,x/1.0)*np.minimum(1,(dur-x)/1.0)
    return y*e*g
# drone pad: D minor-ish
add(pad([73.42,110.0,146.83],15,.06),0)
add(pad([174.61,220.0],8.6,.035),6.4)
# intro: soft pulses + ticks
for b in np.arange(0,4,0.5): add(kick(.35),b)
for b in np.arange(0.25,4,0.5): add(hat(),b,.6,.3)
add(whoosh(1.0,True),1.0,.5); add(whoosh(.5),1.75,.6,-.2)
add(whoosh(1.2,True),2.8,.8)                      # riser into slam
add(impact(),4.0,1.0); add(impact(),4.5,.8)        # BLACK / FRIDAY
add(whoosh(.6),5.05,.5,.3)
add(whoosh(.9,True),5.6,.7)
add(impact(),6.5,.9)                               # reveal
# groove from 6.5
for b in np.arange(6.5,14.5,0.5): add(kick(.9),b)
for b in np.arange(6.75,14.5,0.5): add(hat(),b,1.0,-.3)
for b in np.arange(6.5,14.5,0.25): add(hat(),b,.35,.4)
# claps/snare on 2&4
def snare():
    L=int(.25*sr); w=rng.standard_normal(L); w=w-lp(w,.2); return w*env(L,.001,.06)*.45
for b in np.arange(7.0,14.5,1.0): add(snare(),b)
add(impact(),8.0,.7)                               # -20%
add(whoosh(.5),9.55,.5)
# price count ticks
for k,tt in enumerate(np.linspace(10.6,11.8,14)):
    L=int(.03*sr); x=np.arange(L)/sr; add(np.sin(2*np.pi*2400*x)*np.exp(-x*150)*.25,tt)
add(impact(),11.9,.6)
add(whoosh(.6),12.45,.5)
add(whoosh(.8),13.2,.4,.2)
# master
m=np.tanh(out*1.4); fade=np.minimum(1,(T-t)/0.6)[:,None]; m*=fade*0.85
m=(m/np.max(np.abs(m))*0.89*32767).astype('<i2')
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(m.tobytes())
