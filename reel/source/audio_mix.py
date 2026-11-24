# Mix: CC0 track "Chronos" (FreePD, public domain) cut to the edit at 120 BPM,
# filter-out into the logo end card, transition swoosh + soft shimmer. Mastered later with loudnorm.
import numpy as np, wave, sys
src,dst=sys.argv[1],sys.argv[2]
w=wave.open(src); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2).astype(float)/32768
T=11.5; n=int(T*sr); a=a[:n]; t=np.arange(n)/sr
def lp1(x,k):
    y=np.empty_like(x); c=np.zeros(x.shape[1]) if x.ndim>1 else 0.0
    for i in range(len(x)): c=c+k[i]*(x[i]-c); y[i]=c
    return y
# time-varying 2-pole low-pass: open until 8.0, sweeps to ~350 Hz by 8.6
fc=np.where(t<8.0,18000,np.maximum(350,18000*np.exp(-(t-8.0)*6.6)))
k=1-np.exp(-2*np.pi*fc/sr)
m=lp1(lp1(a,k),k)
gain=np.interp(t,[0,0.15,8.0,8.6,9.5,11.5],[0,1,1,0.55,0.4,0.0])
m*=gain[:,None]
# fade-in already; small ramp at very start
rng=np.random.default_rng(5)
def add(sig,at,g,pan=0):
    i=int(at*sr); j=min(n,i+len(sig)); m[i:j,0]+=sig[:j-i]*g*(1-pan); m[i:j,1]+=sig[:j-i]*g*(1+pan)
# swoosh: band-passed noise sweeping up then down, 0.7 s centred on logo move
L=int(.75*sr); x=np.arange(L)/sr; nz=rng.standard_normal(L)
fc2=np.interp(x,[0,.45,.75],[400,5000,1500]); k2=1-np.exp(-2*np.pi*fc2/sr)
lo=lp1(nz[:,None],k2)[:,0]; lo2=lp1(lo[:,None],k2)[:,0]; bp=lo-lp1(lo2[:,None],k2/4)[:,0]
env=np.sin(np.pi*np.clip(x/.75,0,1))**2
sw=bp*env; sw/=np.abs(sw).max()
pan=np.interp(x,[0,.75],[-.6,.6])
i=int(7.85*sr); m[i:i+L,0]+=sw*0.22*(1-pan); m[i:i+L,1]+=sw*0.22*(1+pan)
# soft shimmer as the logo settles (high bell partials, no low end)
L=int(2.8*sr); x=np.arange(L)/sr; sh=np.zeros(L)
for f,d in ((1174.66,0),(1760.0,.05),(2349.32,.1),(2637.0,.16)):
    xi=np.clip(x-d,0,None); sh+=(np.sin(2*np.pi*f*xi)+.25*np.sin(2*np.pi*2*f*xi))*np.exp(-xi*1.6)*(x>=d)
sh*=np.minimum(1,x/0.01)
add(sh/np.abs(sh).max(),8.5,0.07)
# short reverb on everything after 8 s for a polished tail
Li=int(2.5*sr); ir=rng.standard_normal(Li)*np.exp(-np.arange(Li)/sr*2.4); ir[:int(.015*sr)]=0; ir/=np.sqrt((ir**2).sum())
N=1<<int(np.ceil(np.log2(n+Li)))
tail=np.stack([np.fft.irfft(np.fft.rfft(m[:,c]*(t>7.9),N)*np.fft.rfft(np.roll(ir,c*37),N),N)[:n] for c in (0,1)],1)
m=m+tail*0.18
m*=np.minimum(1,(T-t)/0.5)[:,None]
m/=np.abs(m).max()*1.05
out=(m*32767).astype('<i2')
with wave.open(dst,'wb') as o: o.setnchannels(2);o.setsampwidth(2);o.setframerate(sr);o.writeframes(out.tobytes())
