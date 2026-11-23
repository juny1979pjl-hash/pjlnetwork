import numpy as np, wave
def smooth(x,k):
    c=np.cumsum(np.concatenate([[0],x]).astype(np.float64)); y=(c[k:]-c[:-k])/k
    pad=len(x)-len(y); return np.concatenate([np.full(pad//2,y[0]),y,np.full(pad-pad//2,y[-1])]).astype(np.float32)
SR=48000; T=928.2; N=int(SR*T)
t=np.arange(N)/SR
rng=np.random.default_rng(7)
def note(f): return 440*2**((f-69)/12)
chords=[[38,45,50,53,57],[34,41,46,50,53],[41,48,53,57,60],[36,43,48,52,55]]  # Dm Bb F C
seg=12.0
out=np.zeros((N,2),np.float32)
idx=(t//seg).astype(int)%4
for ci,ch in enumerate(chords):
    m=(idx==ci).astype(np.float32)
    # smooth crossfade between chords
    m=smooth(m,int(SR*1.5))
    for j,n in enumerate(ch):
        f=note(n)
        for det,pan in ((-0.12,0.3),(0.12,0.7)):
            ph=rng.uniform(0,6.28)
            s=np.sin(2*np.pi*(f*(1+det/100))*t+ph)+0.25*np.sin(2*np.pi*2*f*t+ph)
            lfo=0.6+0.4*np.sin(2*np.pi*(0.05+0.01*j)*t+ph)
            amp=(0.16 if n<45 else 0.09)*lfo*m
            out[:,0]+=s*amp*(1-pan); out[:,1]+=s*amp*pan
# pulse (heartbeat-like low thump) every 0.75s
pulse=np.zeros(N,np.float32)
L=int(0.35*SR); tt=np.arange(L)/SR
thump=(np.sin(2*np.pi*55*tt*(1-tt*0.8))*np.exp(-tt*14)).astype(np.float32)
for s0 in np.arange(0,T,0.75):
    i=int(s0*SR); pulse[i:i+L]+=thump[:max(0,min(L,N-i))]
# envelope: loud in intro/pauses/outro, low under voice
vo=[(12.0,243.39),(249.39,440.63),(446.63,663.39),(669.39,903.19)]
g=np.full(N,1.0,np.float32); pg=np.full(N,1.0,np.float32)
for a,b in vo:
    g[int(a*SR):int(b*SR)]=0.16; pg[int(a*SR):int(b*SR)]=0.0
g=smooth(g,int(SR*0.8)); pg=smooth(pg,int(SR*0.8))
out*=g[:,None]
out+=(pulse*pg*0.55)[:,None]
# fades
fi=int(SR*1.5); out[:fi]*=np.linspace(0,1,fi)[:,None]
fo=int(SR*3); out[-fo:]*=np.linspace(1,0,fo)[:,None]
out/=np.abs(out).max(); out*=0.5
w=wave.open('music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
print('ok')
