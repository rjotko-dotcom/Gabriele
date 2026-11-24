# Music bed (CC0, FreePD) + subtle, detail-synced sound design. Master later to -14 LUFS.
# usage: sfx_mix.py music.wav out.wav
import numpy as np, wave, sys
sr=48000; T=11.5; n=int(T*sr); t=np.arange(n)/sr
rng=np.random.default_rng(21)
w=wave.open(sys.argv[1]); assert w.getframerate()==sr
mus=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2).astype(float)/32768
mus=np.pad(mus,((0,max(0,n-len(mus))),(0,0)))[:n]
def lp(x,k):
    k=np.broadcast_to(np.asarray(k,float),(len(x),)); y=np.empty_like(x); c=np.zeros(x.shape[1:])
    for i in range(len(x)): c=c+k[i]*(x[i]-c); y[i]=c
    return y
kf=lambda fc:1-np.exp(-2*np.pi*np.asarray(fc,float)/sr)
# music: gentle open, softer filter-out into end card, tail fade
fc=np.where(t<7.8,20000,np.maximum(1400,20000*np.exp(-(t-7.8)*5)))
m=lp(lp(mus,kf(fc)),kf(fc))
m*=np.interp(t,[0,.08,7.8,8.3,11.5],[0,1,1,.55,0])[:,None]
sfx=np.zeros((n,2))
def put(sig,at,g,pan=0.0):
    i=int(at*sr); j=min(n,i+len(sig)); s=sig[:j-i]*g
    sfx[i:j,0]+=s*(1-pan)*.9; sfx[i:j,1]+=s*(1+pan)*.9
def norm(x): return x/np.abs(x).max()
def swish(d=.35,f0=800,f1=6000):
    L=int(d*sr); x=np.arange(L)/sr; nz=rng.standard_normal(L)[:,None]
    f=np.interp(x,[0,d*.6,d],[f0,f1,f1*.6]); hi=lp(nz,kf(f)); band=hi-lp(hi,kf(f/3))
    return norm(band[:,0]*np.sin(np.pi*x/d)**2)
def tick(f=3800):
    L=int(.03*sr); x=np.arange(L)/sr; nz=rng.standard_normal(L)
    return norm(np.sin(2*np.pi*f*x)*np.exp(-x*260)+.3*nz*np.exp(-x*600))
def sparkle(d=.9):
    L=int(d*sr); x=np.arange(L)/sr; y=np.zeros(L)
    for k in range(14):
        at=rng.uniform(0,d*.7); f=rng.uniform(3500,8000); xi=np.clip(x-at,0,None)
        y+=np.sin(2*np.pi*f*xi)*np.exp(-xi*25)*(x>=at)*rng.uniform(.4,1)
    return norm(y*np.sin(np.pi*x/d))
def bell(fs,d=1.8,dec=2.2):
    L=int(d*sr); x=np.arange(L)/sr; y=sum(np.sin(2*np.pi*f*x)+.2*np.sin(2*np.pi*f*2.01*x)*np.exp(-x*5) for f in fs)
    return norm(y*np.exp(-x*dec)*np.minimum(1,x/.004))
def riser(d=1.1):
    L=int(d*sr); x=np.arange(L)/sr; nz=rng.standard_normal(L)[:,None]
    y=lp(nz,kf(np.interp(x,[0,d],[300,7000])))[:,0]; tone=np.sin(2*np.pi*np.cumsum(np.interp(x,[0,d],[300,1200]))/sr)
    return norm((norm(y)+.25*tone)*(x/d)**2.2)
def softhit():   # tonal, cushioned (not a boom): short low thump + airy tail
    L=int(1.6*sr); x=np.arange(L)/sr
    body=np.sin(2*np.pi*np.cumsum(90+60*np.exp(-x*25))/sr)*np.exp(-x*7)*np.minimum(1,x/.006)
    air=lp(rng.standard_normal(L)[:,None],kf(2500))[:,0]; air=norm(air-lp(air[:,None],kf(400))[:,0])*np.exp(-x*4)*.35
    return norm(body*.8+air)
# ---- cue sheet (seconds in the edit)
put(swish(.6,200,2500),0.0,.10)                 # reveal from black
put(swish(.32),0.55,.16,-.3); put(swish(.30,1200,7000),0.78,.12,.3)   # BLACK / FRIDAY
put(sparkle(1.2),0.9,.06,.2)                    # light over paint
put(swish(.22,2000,9000),1.3,.07)               # red line
put(swish(.26,1500,8000),1.58,.11,.4); put(tick(2600),1.78,.10,.3)    # slash, -20 %
put(sparkle(.7),1.85,.07,-.2)                   # headlight glint
put(swish(.3),2.28,.10,-.3)                     # model name
put(swish(.3,900,6000),3.28,.10,-.4)            # price block
put(swish(.28,3000,9000),3.98,.08,.2)           # strike-through
for k,tt in enumerate(np.linspace(4.32,5.55,12)): put(tick(3600+k*40),tt,.07*(0.6+0.4*k/11),(-1)**k*.2)
put(bell([1318.5,1975.5]),5.6,.08)              # price settles
put(swish(.3),6.28,.09,.3)                      # CTA
put(sparkle(1.1),6.7,.06,-.2)                   # second light pass
put(riser(1.0),7.0,.13)                         # into end card
put(softhit(),8.0,.22)                          # Fakto Auto lands
put(swish(.3,1000,7000),8.28,.08,.5)            # Nissan logo slides in
put(sparkle(.9),8.85,.06)                       # shine across Fakto Auto
put(bell([1174.66,1760.0,2349.3],2.6,1.4),8.05,.07)
# light reverb on the sfx bus
Li=int(1.6*sr); ir=rng.standard_normal(Li)*np.exp(-np.arange(Li)/sr*3.5); ir[:int(.012*sr)]=0; ir/=np.sqrt((ir**2).sum())
N=1<<int(np.ceil(np.log2(n+Li)))
wet=np.stack([np.fft.irfft(np.fft.rfft(sfx[:,c],N)*np.fft.rfft(np.roll(ir,c*53),N),N)[:n] for c in (0,1)],1)
out=m*0.8+sfx+wet*0.12
out*=np.minimum(1,(T-t)/.5)[:,None]
out/=np.abs(out).max()*1.05
with wave.open(sys.argv[2],'wb') as o: o.setnchannels(2);o.setsampwidth(2);o.setframerate(sr);o.writeframes((out*32767).astype('<i2').tobytes())
