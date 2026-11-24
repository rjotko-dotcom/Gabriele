# Minimal end-card sound design (4.0 s): air swell -> soft cushioned landing -> shimmer chord tail.
# usage: outro_audio.py single|all out.wav
import numpy as np, wave, sys
mode,dst=sys.argv[1],sys.argv[2]
sr=48000; T=4.0; n=int(T*sr); t=np.arange(n)/sr
rng=np.random.default_rng(3)
out=np.zeros((n,2))
def lp(x,k):
    k=np.broadcast_to(np.asarray(k,float),(len(x),)); y=np.empty_like(x); c=0.0
    for i in range(len(x)): c+=k[i]*(x[i]-c); y[i]=c
    return y
kf=lambda fc:1-np.exp(-2*np.pi*np.asarray(fc,float)/sr)
norm=lambda x:x/np.abs(x).max()
def put(sig,at,g,pan=0.0):
    i=int(at*sr); j=min(n,i+len(sig)); s=sig[:j-i]*g
    out[i:j,0]+=s*(1-pan); out[i:j,1]+=s*(1+pan)
def swell(d):            # filtered air rising into the landing
    L=int(d*sr); x=np.arange(L)/sr; y=lp(rng.standard_normal(L),kf(np.interp(x,[0,d],[250,4500])))
    return norm(y)*(x/d)**2.5
def swish(d=.3,f0=900,f1=6500):
    L=int(d*sr); x=np.arange(L)/sr; nz=rng.standard_normal(L)
    hi=lp(nz,kf(np.interp(x,[0,d*.6,d],[f0,f1,f1*.6]))); band=hi-lp(hi,kf(np.interp(x,[0,d],[f0,f1])/3))
    return norm(band*np.sin(np.pi*x/d)**2)
def land():              # cushioned tonal thump, no boom
    L=int(1.2*sr); x=np.arange(L)/sr
    body=np.sin(2*np.pi*np.cumsum(85+55*np.exp(-x*28))/sr)*np.exp(-x*8)*np.minimum(1,x/.008)
    return norm(body)
def chord(fs,d=3.4):     # soft shimmer pad / bell bloom
    L=int(d*sr); x=np.arange(L)/sr; y=np.zeros(L)
    for f in fs:
        for dt in (-.25,.25): y+=np.sin(2*np.pi*f*(1+dt/100)*x)
    return norm(y*np.minimum(1,x/.03)*np.exp(-x*1.15))
def pluck(f):
    L=int(1.2*sr); x=np.arange(L)/sr
    return norm((np.sin(2*np.pi*f*x)+.25*np.sin(4*np.pi*f*x))*np.exp(-x*4.5)*np.minimum(1,x/.003))
def sparkle(d=.8):
    L=int(d*sr); x=np.arange(L)/sr; y=np.zeros(L)
    for k in range(12):
        at=rng.uniform(0,d*.7); f=rng.uniform(3800,8000); xi=np.clip(x-at,0,None)
        y+=np.sin(2*np.pi*f*xi)*np.exp(-xi*28)*(x>=at)*rng.uniform(.4,1)
    return norm(y*np.sin(np.pi*x/d))
put(swell(.55),0.0,.14)
put(land(),0.5,.30)
put(chord([293.66,440.0,587.33,739.99,880.0]),0.5,.10)        # D major add9-ish, airy
put(swish(.3),0.42,.07,.4)
if mode=='single':
    put(pluck(1174.66),0.55,.05,.3)
    put(sparkle(.9),1.0,.05)
else:
    for i,f in enumerate((880.0,1108.73,1318.51)):            # one soft note per brand
        put(pluck(f),0.6+i*0.15,.055,(i-1)*.45)
    put(sparkle(.9),1.25,.05)
# small room reverb
Li=int(1.8*sr); ir=rng.standard_normal(Li)*np.exp(-np.arange(Li)/sr*3.0); ir[:int(.012*sr)]=0; ir/=np.sqrt((ir**2).sum())
N=1<<int(np.ceil(np.log2(n+Li)))
wet=np.stack([np.fft.irfft(np.fft.rfft(out[:,c],N)*np.fft.rfft(np.roll(ir,c*41),N),N)[:n] for c in (0,1)],1)
m=out+wet*0.22
m*=np.minimum(1,(T-t)/0.6)[:,None]
m/=np.abs(m).max()*1.05
with wave.open(dst,'wb') as o: o.setnchannels(2);o.setsampwidth(2);o.setframerate(sr);o.writeframes((m*32767).astype('<i2').tobytes())
