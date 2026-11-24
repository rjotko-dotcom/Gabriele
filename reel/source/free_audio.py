# Sound for the freestyle "JUODA. BALTA. TAVO." ad (12.7 s). Same palette as the other ads.
import numpy as np, wave, sys
sr=48000; T=12.7; n=int(sr*T); t=np.arange(n)/sr
rng=np.random.default_rng(31)
L_=np.zeros(n); R_=np.zeros(n)
def add(sig,at,g=1.0,pan=0.0):
    i=int(round(at*sr)); s=sig*g
    if i<0: s=s[-i:]; i=0
    j=min(n,i+len(s)); s=s[:j-i]; L_[i:j]+=s*(1-pan); R_[i:j]+=s*(1+pan)
def lpv(x,k):
    k=np.broadcast_to(k,x.shape); y=np.empty_like(x); c=0.0
    for i in range(len(x)): c+=k[i]*(x[i]-c); y[i]=c
    return y
def saw(f,Ls,ph=0): x=np.arange(Ls)/sr; return 2*((f*x+ph)%1)-1
def nrm(x): return x/np.abs(x).max()
def kf(f): return 1-np.exp(-2*np.pi*np.asarray(f,float)/sr)
def swish(d=.3,f0=900,f1=6500,seed=0):
    r=np.random.default_rng(100+seed); Ls=int(d*sr); x=np.arange(Ls)/sr; nz=r.standard_normal(Ls)
    hi=lpv(nz,kf(np.interp(x,[0,d*.6,d],[f0,f1,f1*.6]))); band=hi-lpv(hi,kf(np.interp(x,[0,d],[f0,f1])/3))
    return nrm(band*np.sin(np.pi*x/d)**2)
def pluck(f,dec=5):
    Ls=int(1.0*sr); x=np.arange(Ls)/sr; return (np.sin(2*np.pi*f*x)+.25*np.sin(4*np.pi*f*x))*np.exp(-x*dec)*np.minimum(1,x/.003)
def tick(f=3600):
    Ls=int(.02*sr); x=np.arange(Ls)/sr; return np.sin(2*np.pi*f*x)*np.exp(-x*250)
def sparkle(d=.8,seed=0):
    r=np.random.default_rng(200+seed); Ls=int(d*sr); x=np.arange(Ls)/sr; y=np.zeros(Ls)
    for k in range(12):
        a0=r.uniform(0,d*.7); f=r.uniform(3800,8000); xi=np.clip(x-a0,0,None); y+=np.sin(2*np.pi*f*xi)*np.exp(-xi*28)*(x>=a0)*r.uniform(.4,1)
    return nrm(y*np.sin(np.pi*x/d))
def stab(notes,dur=.9):   # clean filtered chord stab + soft click (no boom)
    Ls=int(dur*sr); x=np.arange(Ls)/sr; y=np.zeros(Ls)
    for f in notes:
        for d in (-.2,.2): y+=saw(f*(1+d/100),Ls)
    y=lpv(y,np.interp(x,[0,.05,dur],[.18,.06,.02]))*np.exp(-x*3.2)*np.minimum(1,x/.004)
    click=rng.standard_normal(int(.006*sr)); click=click-lpv(click,.5)
    y[:len(click)]+=click*0.6
    thump=np.sin(2*np.pi*np.cumsum(70+40*np.exp(-x*30))/sr)*np.exp(-x*14)*np.minimum(1,x/.004)
    return nrm(y)+0.35*thump
# ---------- 0-3 s: three word hits + quiet clock ticks + riser
add(stab([146.83,220.0,293.66]),0.02,.42)
add(stab([116.54,174.61,233.08]),1.0,.42,-.15)
add(stab([174.61,261.63,349.23]),2.0,.46,.15)
for at in np.arange(0.25,3.0,0.25):
    if abs(at-round(at))<1e-6: continue
    add(tick(2600),at,.09,-.3 if (at*4)%2 else .3)
Ls=int(1.0*sr); x=np.arange(Ls)/sr
add(lpv(rng.standard_normal(Ls),np.linspace(.01,.3,Ls))*(x/1.0)**2.5*0.45,2.05)
add(swish(.55,300,6000,1),2.75,.07)
# ---------- 3.0-9.6: groove bed (same engine as the story ad)
beat=0.5; tb=t-3.0
duck=np.where((t>=3.0)&(t<9.6),1-0.55*np.exp(-((tb%beat))*9),1)
groove=np.clip((9.6-t)/0.5,0,1)*(t>=3.0)
chords=[(3.0,73.42,[146.83,174.61,220.0,261.63]),(5.0,58.27,[146.83,174.61,233.08,261.63]),
        (7.0,87.31,[174.61,220.0,261.63,329.63]),(9.0,65.41,[164.81,196.0,246.94,293.66])]
pad=np.zeros(n); sub=np.zeros(n)
for i,(st,b,notes) in enumerate(chords):
    en=chords[i+1][0] if i+1<len(chords) else 10.0
    a=int(st*sr); e=int(min(T,en+0.3)*sr); Ls=e-a; x=np.arange(Ls)/sr; y=np.zeros(Ls)
    for f in notes:
        for d,ph in ((-0.25,.1),(0,.5),(0.25,.8)): y+=saw(f*(1+d/100),Ls,ph)
    w=np.minimum(1,x/0.2)*np.minimum(1,np.maximum(0,(Ls/sr-x)/0.3))
    pad[a:e]+=y*w; sub[a:e]+=np.sin(2*np.pi*b*x)*w
cut=np.interp(t,[0,3.0,8.5,9.6,10.0],[0.03,0.03,0.075,0.09,0.02])
pad=lpv(pad,cut)*duck; L_+=pad*0.05; R_+=pad*0.05
sub*=duck*groove; L_+=sub*0.16; R_+=sub*0.16
for i,(st,b,notes) in enumerate(chords):
    seq=[notes[0]*2,notes[1]*2,notes[2]*2,notes[-1]*2]
    for k in range(8):
        at=st+k*0.25
        if at>=9.6: continue
        f=seq[[0,1,2,3,2,1,3,2][k%8]]; Ls=int(.35*sr); x=np.arange(Ls)/sr
        y=lpv(saw(f,Ls)*0.6+np.sin(2*np.pi*f*x),np.interp(at,[3,9.6],[0.06,0.18]))*np.exp(-x*11)*np.minimum(1,x/0.002)
        add(y,at,0.04,0.4 if k%2 else -0.4)
for at in np.arange(3.5,9.6,0.25):
    Ls=int(.05*sr); w=rng.standard_normal(Ls); w=w-lpv(w,.6)
    add(w*np.exp(-np.arange(Ls)/sr*90),at,0.035 if (at*4)%2 else 0.02,0.25 if (at*4)%2 else -0.25)
for at in np.arange(5.25,9.6,0.5):
    Ls=int(.22*sr); w=rng.standard_normal(Ls); w=w-lpv(w,.5); add(w*np.exp(-np.arange(Ls)/sr*14),at,0.016)
# ---------- detail sfx
add(swish(.5,250,5000,2),3.0,.08)                       # red splits open
add(sparkle(1.0,1),3.4,.022)                            # light pass
add(swish(.3,1200,7000,3),3.35,.04,.3)                  # title
for i,at in enumerate((3.75,4.35,4.95)):                # callouts: dot tick + line + note
    add(tick(3000),at,.07,(-.4,.4,-.4)[i]); add(swish(.25,2000,8000,10+i),at+.1,.03,(-.4,.4,-.4)[i])
    add(pluck((1174.66,1318.51,1567.98)[i],7),at+.45,.03,(-.3,.3,-.3)[i])
add(swish(.4,600,5000,4),6.45,.05,-.3)                  # into the deal
add(swish(.3,1200,7000,5),6.75,.04,.3)                  # BLACK FRIDAY
for tt in np.linspace(7.15,7.95,10): add(tick(),tt,.024)
add(pluck(1318.51),8.0,.035); add(pluck(1760.0),8.1,.03,.3)
add(swish(.2,3000,9000,6),8.35,.03,.3)
add(pluck(1174.66),8.6,.025,-.3)
add(sparkle(.8,3),8.25,.02,-.2)
# ---------- outro: riser + sting (identical to the other ads)
LAND=9.9
Ls=int(1.5*sr); x=np.arange(Ls)/sr; w=rng.standard_normal(Ls)
air=lpv(w,np.linspace(.01,.25,Ls))*(x/1.5)**2.5; tone=np.sin(2*np.pi*np.cumsum(np.linspace(220,880,Ls))/sr)*(x/1.5)**3*0.25
add(air*0.32+tone*0.12,LAND-1.45)
Ls=int(3.3*sr); x=np.arange(Ls)/sr; y=np.zeros(Ls)
for f in (146.83,220.0,261.63,329.63,440.0,587.33):
    for d in (-0.3,0.3): y+=np.sin(2*np.pi*f*(1+d/100)*x)+0.25*saw(f*(1+d/100),Ls)
add(lpv(y,0.08)*np.minimum(1,x/0.08)*np.exp(-x*0.9),LAND,0.038)
add(np.sin(2*np.pi*36.71*x)*np.minimum(1,x/0.25)*np.exp(-x*1.4),LAND,0.11)
for f,dt,p in ((1174.66,0,-.2),(1760.0,0.12,.2),(2349.3,0.24,0)):
    add((np.sin(2*np.pi*f*x)+.3*np.sin(2*np.pi*f*2.01*x)*np.exp(-x*4))*np.exp(-x*1.8),LAND+dt,0.022,p)
def rev(x,seed,dec=2.2):
    Li=int(3.0*sr); ir=np.random.default_rng(seed).standard_normal(Li)*np.exp(-np.arange(Li)/sr*dec); ir[:int(.02*sr)]=0
    ir/=np.sqrt((ir**2).sum()); N=1<<int(np.ceil(np.log2(len(x)+Li)))
    return np.fft.irfft(np.fft.rfft(x,N)*np.fft.rfft(ir,N),N)[:len(x)]
m=np.stack([L_+rev(L_,1)*0.35,R_+rev(R_,2)*0.35],1)
m*=np.minimum(1,t/0.02)[:,None]*np.minimum(1,(T-t)/0.6)[:,None]
m=np.tanh(m/np.max(np.abs(m))*1.2); m=m/np.max(np.abs(m))*0.85
with wave.open(sys.argv[1],'wb') as o: o.setnchannels(2);o.setsampwidth(2);o.setframerate(sr);o.writeframes((m*32767).astype('<i2').tobytes())
