# Modern, fluid automotive bed (13.5 s): pulsing filtered pad, sub, arp, soft hats,
# reverse swell into a clean shimmering logo sting. No impacts.
import numpy as np, wave, sys
sr=48000; T=10.5; n=int(sr*T); t=np.arange(n)/sr
rng=np.random.default_rng(11)
L_=np.zeros(n); R_=np.zeros(n)
def add(sig,at,g=1.0,pan=0.0):
    i=int(at*sr); j=min(n,i+len(sig)); s=sig[:j-i]*g
    L_[i:j]+=s*(1-pan); R_[i:j]+=s*(1+pan)
def lpv(x,k):
    k=np.broadcast_to(k,x.shape); y=np.empty_like(x); c=0.0
    for i in range(len(x)): c+=k[i]*(x[i]-c); y[i]=c
    return y
def saw(f,L,ph=0): x=np.arange(L)/sr; return 2*((f*x+ph)%1)-1
beat=0.5
duck=1-0.55*np.exp(-((t%beat))*9)          # sidechain-style pump
duck=np.where(t<7.4,duck,1)
groove=np.clip((7.4-t)/0.5,0,1)            # groove ends into outro
chords=[(0,73.42,[146.83,174.61,220.0,261.63]),(2,58.27,[146.83,174.61,233.08,261.63]),
        (4,87.31,[174.61,220.0,261.63,329.63]),(6,65.41,[164.81,196.0,246.94,293.66])]
pad=np.zeros(n); sub=np.zeros(n)
for i,(st,b,notes) in enumerate(chords):
    en=chords[i+1][0] if i+1<len(chords) else 7.8
    a=int(st*sr); e=int(min(T,en+0.3)*sr); Ls=e-a; x=np.arange(Ls)/sr
    y=np.zeros(Ls)
    for f in notes:
        for d,ph in ((-0.25,.1),(0,.5),(0.25,.8)): y+=saw(f*(1+d/100),Ls,ph)
    w=np.minimum(1,x/0.25)*np.minimum(1,np.maximum(0,(Ls/sr-x)/0.3))
    pad[a:e]+=y*w
    sub[a:e]+=np.sin(2*np.pi*b*x)*w
cut=np.interp(t,[0,1.7,6.2,7.4,7.8],[0.012,0.04,0.07,0.09,0.02])
pad=lpv(pad,cut)*duck
L_+=pad*0.05; R_+=pad*0.05
sub*=duck*groove; L_+=sub*0.16; R_+=sub*0.16
# arp (16ths) with opening filter
for i,(st,b,notes) in enumerate(chords):
    seq=[notes[0]*2,notes[1]*2,notes[2]*2,notes[-1]*2]
    for k in range(8 if st<8 else 4):
        at=st+k*0.25
        if at<0.5 or at>=7.4: continue
        f=seq[[0,1,2,3,2,1,3,2][k%8]]; Ls=int(.35*sr); x=np.arange(Ls)/sr
        y=saw(f,Ls)*0.6+np.sin(2*np.pi*f*x)
        y=lpv(y,np.interp(at,[0,8],[0.05,0.18]))*np.exp(-x*11)*np.minimum(1,x/0.002)
        add(y,at,0.042*min(1,at/2+0.4),0.4 if k%2 else -0.4)
# soft hats 16ths from 2s, gentle
for at in np.arange(2.0,7.4,0.25):
    Ls=int(.05*sr); w=rng.standard_normal(Ls); w=w-lpv(w,.6)
    g=0.035 if (at*4)%2 else 0.02
    add(w*np.exp(-np.arange(Ls)/sr*90),at,g,0.25 if (at*4)%2 else -0.25)
for at in np.arange(4.25,7.4,0.5):   # offbeat open hat
    Ls=int(.22*sr); w=rng.standard_normal(Ls); w=w-lpv(w,.5)
    add(w*np.exp(-np.arange(Ls)/sr*14),at,0.016)
# riser/swell into logo (smooth air + rising tone)
Ls=int(1.5*sr); x=np.arange(Ls)/sr; w=rng.standard_normal(Ls)
air=lpv(w,np.linspace(.01,.25,Ls))*(x/1.5)**2.5
tone=np.sin(2*np.pi*np.cumsum(np.linspace(220,880,Ls))/sr)*(x/1.5)**3*0.25
add(air*0.32+tone*0.12,6.15)
# end-card sting at 8.05: Dm9 shimmer, slow-bloom sub, bell
Ls=int(3.3*sr); x=np.arange(Ls)/sr
y=np.zeros(Ls)
for f in (146.83,220.0,261.63,329.63,440.0,587.33):
    for d in (-0.3,0.3): y+=np.sin(2*np.pi*f*(1+d/100)*x)+0.25*saw(f*(1+d/100),Ls)
y=lpv(y,0.08)*np.minimum(1,x/0.08)*np.exp(-x*0.9)
add(y,7.6,0.038)
add(np.sin(2*np.pi*36.71*x)*np.minimum(1,x/0.25)*np.exp(-x*1.4),7.6,0.11)
for f,dt,p in ((1174.66,0,-.2),(1760.0,0.12,.2),(2349.3,0.24,0)):
    xb=x; add((np.sin(2*np.pi*f*xb)+.3*np.sin(2*np.pi*f*2.01*xb)*np.exp(-xb*4))*np.exp(-xb*1.8),7.6+dt,0.022,p)
# price ticks
for tt in np.linspace(4.95,5.9,12):
    Ls=int(.02*sr); x2=np.arange(Ls)/sr; add(np.sin(2*np.pi*3600*x2)*np.exp(-x2*250),tt,0.022)
# minimal detail SFX
def swish(d=.3,f0=900,f1=6500,seed=0):
    r=np.random.default_rng(100+seed); Ls=int(d*sr); x=np.arange(Ls)/sr; nz=r.standard_normal(Ls)
    hi=lpv(nz,1-np.exp(-2*np.pi*np.interp(x,[0,d*.6,d],[f0,f1,f1*.6])/sr)); band=hi-lpv(hi,1-np.exp(-2*np.pi*np.interp(x,[0,d],[f0,f1])/3/sr))
    y=band*np.sin(np.pi*x/d)**2; return y/np.abs(y).max()
def sparkle(d=.8,seed=0):
    r=np.random.default_rng(200+seed); Ls=int(d*sr); x=np.arange(Ls)/sr; y=np.zeros(Ls)
    for k in range(12):
        a0=r.uniform(0,d*.7); f=r.uniform(3800,8000); xi=np.clip(x-a0,0,None); y+=np.sin(2*np.pi*f*xi)*np.exp(-xi*28)*(x>=a0)*r.uniform(.4,1)
    y*=np.sin(np.pi*x/d); return y/np.abs(y).max()
def pluck(f):
    Ls=int(1.0*sr); x=np.arange(Ls)/sr; return (np.sin(2*np.pi*f*x)+.25*np.sin(4*np.pi*f*x))*np.exp(-x*5)*np.minimum(1,x/.003)
add(swish(.35,600,5000,1),0.0,.05,-.5); add(swish(.35,700,6000,2),0.08,.05,.5)     # BLACK / FRIDAY slide in
add(sparkle(.8,1),0.65,.022)                                                     # glint on title
add(swish(.5,300,4000,3),1.3,.06)                                                # zoom-through into car
add(swish(.3,1200,7000,4),1.65,.05,.3); add(pluck(1174.66),1.75,.035)          # -20 %
add(swish(.4,500,5000,5),1.8,.04,-.6)                                            # red band slides in
add(sparkle(.7,2),2.15,.02,.2)                                                   # headlight glint
add(swish(.3,900,6000,6),4.3,.045,-.3)                                           # price block
add(swish(.2,3000,9000,7),4.85,.03,.3)                                           # strike-through
add(pluck(1318.51),5.95,.03); add(pluck(1760.0),6.05,.03,.3)                    # price settles + pill
add(sparkle(.8,3),6.35,.02,-.2)                                                  # second light pass
# reverb
def rev(x,seed,dec=2.2):
    Li=int(3.0*sr); ir=np.random.default_rng(seed).standard_normal(Li)*np.exp(-np.arange(Li)/sr*dec); ir[:int(.02*sr)]=0
    ir/=np.sqrt((ir**2).sum())
    N=1<<int(np.ceil(np.log2(len(x)+Li)))
    return np.fft.irfft(np.fft.rfft(x,N)*np.fft.rfft(ir,N),N)[:len(x)]
m=np.stack([L_+rev(L_,1)*0.35,R_+rev(R_,2)*0.35],1)
m*=np.minimum(1,t/0.3)[:,None]*np.minimum(1,(T-t)/0.6)[:,None]
m/=np.max(np.abs(m)); m=np.tanh(m*1.2); m=(m/np.max(np.abs(m))*0.85*32767).astype('<i2')
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(m.tobytes())
