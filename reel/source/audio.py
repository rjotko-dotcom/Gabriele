# Calm, premium automotive bed: pads + soft bass arp + light plucks, no impacts.
import numpy as np, wave, sys
sr=44100; T=15.0; n=int(sr*T); t=np.arange(n)/sr
rng=np.random.default_rng(7)
L_=np.zeros(n); R_=np.zeros(n)
def add(sig,at,g=1.0,pan=0.0):
    i=int(at*sr); j=min(n,i+len(sig)); s=sig[:j-i]*g
    L_[i:j]+=s*(1-pan); R_[i:j]+=s*(1+pan)
def lp(x,k):
    y=np.empty_like(x); c=0.0
    for i in range(len(x)): c+=k*(x[i]-c); y[i]=c
    return y
def saw(f,L): x=np.arange(L)/sr; return 2*((f*x)%1)-1
chords=[ # (start, bass, notes)
 (0,73.42,[146.83,174.61,220.00]),(2,58.27,[146.83,174.61,233.08]),
 (4,87.31,[174.61,220.00,261.63]),(6,65.41,[164.81,196.00,261.63]),
 (8,73.42,[146.83,174.61,220.00,293.66]),(10,58.27,[146.83,174.61,233.08,293.66]),
 (12,87.31,[174.61,220.00,261.63,349.23]),(14,73.42,[146.83,220.00,293.66])]
# pads (overlapping, slow attack)
for i,(st,b,notes) in enumerate(chords):
    dur=(chords[i+1][0]-st if i+1<len(chords) else T-st)+0.8
    Ls=int(dur*sr); x=np.arange(Ls)/sr; y=np.zeros(Ls)
    for f in notes:
        for d in (-0.6,0,0.6): y+=saw(f+d*f/440,Ls)*0.5+np.sin(2*np.pi*(f+d)*x)
    y=lp(y,0.035)
    e=np.minimum(1,x/0.7)*np.minimum(1,np.maximum(0,(dur-x)/0.8))
    add(y*e,st,0.035 if st<6 else 0.04)
# soft bass arp eighths from 2s
for i,(st,b,notes) in enumerate(chords):
    for k in range(4 if st<14 else 2):
        at=st+k*0.5
        if at<2.0: continue
        Ls=int(.48*sr); x=np.arange(Ls)/sr
        y=lp(saw(b,Ls)+0.5*np.sin(2*np.pi*b*x),0.06)*np.exp(-x*5)*np.minimum(1,x/0.005)
        add(y,at,0.22 if at<6.5 else 0.3)
# light plucks from 6.5 (arpeggio up an octave)
for i,(st,b,notes) in enumerate(chords):
    if st<6: continue
    seq=[notes[0]*2,notes[1]*2,notes[2]*2,notes[1]*2]
    for k in range(8 if st<14 else 2):
        at=st+k*0.25+(0.5 if st==6 else 0)
        if at>=14.6 or (st==6 and k>=6): continue
        f=seq[k%4]; Ls=int(.6*sr); x=np.arange(Ls)/sr
        y=(np.sin(2*np.pi*f*x)+0.3*np.sin(4*np.pi*f*x))*np.exp(-x*7)*np.minimum(1,x/0.003)
        add(y,at,0.045,0.35 if k%2 else -0.35)
# very soft shaker on offbeats from 6.5
for at in np.arange(6.75,14.5,0.5):
    Ls=int(.06*sr); w=rng.standard_normal(Ls); w=w-lp(w,.5)
    add(w*np.exp(-np.arange(Ls)/sr*60),at,0.05,0.2)
# gentle swells into transitions (quiet filtered air)
def swell(d):
    Ls=int(d*sr); w=rng.standard_normal(Ls); k=np.linspace(.005,.06,Ls); y=np.empty(Ls); c=0
    for i in range(Ls): c+=k[i]*(w[i]-c); y[i]=c
    return y*np.linspace(0,1,Ls)**2*np.linspace(1,0.2,Ls)**0.3
add(swell(1.6),2.6,0.35); add(swell(1.6),5.0,0.35)
# chimes on -20% and final price
def bell(f):
    Ls=int(2.5*sr); x=np.arange(Ls)/sr
    return (np.sin(2*np.pi*f*x)+.4*np.sin(2*np.pi*f*2.76*x)*np.exp(-x*3))*np.exp(-x*1.5)
add(bell(880),8.1,0.06,-0.2); add(bell(1174.66),8.35,0.045,0.2)
add(bell(1046.5),11.9,0.06); add(bell(1318.5),12.1,0.04,0.25)
# price ticks (soft)
for tt in np.linspace(10.6,11.8,13):
    Ls=int(.025*sr); x=np.arange(Ls)/sr; add(np.sin(2*np.pi*3200*x)*np.exp(-x*220),tt,0.05)
# simple stereo reverb (FFT convolution)
def rev(x,seed):
    Li=int(2.2*sr); ir=np.random.default_rng(seed).standard_normal(Li)*np.exp(-np.arange(Li)/sr*2.6); ir[0]=0
    N=1<<int(np.ceil(np.log2(len(x)+Li)))
    return np.fft.irfft(np.fft.rfft(x,N)*np.fft.rfft(ir,N),N)[:len(x)]
wl=rev(L_,1); wr=rev(R_,2)
m=np.stack([L_+wl*0.012,R_+wr*0.012],1)
m*=np.minimum(1,t/0.4)[:,None]*np.minimum(1,(T-t)/0.9)[:,None]
m=np.tanh(m/np.max(np.abs(m))*1.1); m=(m/np.max(np.abs(m))*0.85*32767).astype('<i2')
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(m.tobytes())
