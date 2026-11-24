# Same end-card sound as the reel/story outro (riser -> Dm9 shimmer + soft sub bloom + bells),
# standalone: landing at 0.9 s, total 3.8 s.  usage: outro_sting.py out.wav
import numpy as np, wave, sys
sr=48000; T=3.8; n=int(sr*T); t=np.arange(n)/sr; LAND=0.9
rng=np.random.default_rng(11)
L_=np.zeros(n); R_=np.zeros(n)
def add(sig,at,g=1.0,pan=0.0):
    i=int(round(at*sr)); s=sig*g
    if i<0: s=s[-i:]; i=0
    j=min(n,i+len(s)); s=s[:j-i]; L_[i:j]+=s*(1-pan); R_[i:j]+=s*(1+pan)
def lpv(x,k):
    k=np.broadcast_to(k,x.shape); y=np.empty_like(x); c=0.0
    for i in range(len(x)): c+=k[i]*(x[i]-c); y[i]=c
    return y
def saw(f,L,ph=0): x=np.arange(L)/sr; return 2*((f*x+ph)%1)-1
# riser (identical to the story: 1.5 s, ends just after the landing)
Ls=int(1.5*sr); x=np.arange(Ls)/sr; w=rng.standard_normal(Ls)
air=lpv(w,np.linspace(.01,.25,Ls))*(x/1.5)**2.5
tone=np.sin(2*np.pi*np.cumsum(np.linspace(220,880,Ls))/sr)*(x/1.5)**3*0.25
add(air*0.32+tone*0.12,LAND-1.45)
# sting
Ls=int(3.3*sr); x=np.arange(Ls)/sr; y=np.zeros(Ls)
for f in (146.83,220.0,261.63,329.63,440.0,587.33):
    for d in (-0.3,0.3): y+=np.sin(2*np.pi*f*(1+d/100)*x)+0.25*saw(f*(1+d/100),Ls)
y=lpv(y,0.08)*np.minimum(1,x/0.08)*np.exp(-x*0.9)
add(y,LAND,0.038)
add(np.sin(2*np.pi*36.71*x)*np.minimum(1,x/0.25)*np.exp(-x*1.4),LAND,0.11)
for f,dt,p in ((1174.66,0,-.2),(1760.0,0.12,.2),(2349.3,0.24,0)):
    add((np.sin(2*np.pi*f*x)+.3*np.sin(2*np.pi*f*2.01*x)*np.exp(-x*4))*np.exp(-x*1.8),LAND+dt,0.022,p)
def rev(x,seed,dec=2.2):
    Li=int(3.0*sr); ir=np.random.default_rng(seed).standard_normal(Li)*np.exp(-np.arange(Li)/sr*dec); ir[:int(.02*sr)]=0
    ir/=np.sqrt((ir**2).sum()); N=1<<int(np.ceil(np.log2(len(x)+Li)))
    return np.fft.irfft(np.fft.rfft(x,N)*np.fft.rfft(ir,N),N)[:len(x)]
m=np.stack([L_+rev(L_,1)*0.35,R_+rev(R_,2)*0.35],1)
m*=np.minimum(1,(T-t)/0.6)[:,None]
m=np.tanh(m/np.max(np.abs(m))*1.2); m=m/np.max(np.abs(m))*0.85
with wave.open(sys.argv[1],'wb') as o: o.setnchannels(2);o.setsampwidth(2);o.setframerate(sr);o.writeframes((m*32767).astype('<i2').tobytes())
