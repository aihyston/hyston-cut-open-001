"""Step 4: procedural background (rain, bokeh, blooming flowers, petals).

Writes raw RGB24 frames (960x540 @ 24 fps) to `out` (a binary stream).
The final encode upscales to 1920x1080 and burns 1080p subtitles on top.
Scene colours / rain / bloom are driven by keyframes (see examples/scenes.example.json).
"""
import math, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 960, 540, 24


def default_keyframes(dur):
    """Generic arc: night rain -> warm bloom -> brighter finale -> fade."""
    p = lambda x: round(dur * x, 2)
    return [
        dict(t=0, top="#05080f", bottom="#121a28", rain=0.5, bloom=0.0, petals=0.0),
        dict(t=p(0.06), top="#08101c", bottom="#1b2738", rain=1.0, bloom=0.0, petals=0.0),
        dict(t=p(0.24), top="#152437", bottom="#8a6458", rain=0.45, bloom=0.45, petals=0.5),
        dict(t=p(0.36), top="#0a1320", bottom="#253447", rain=0.9, bloom=0.25, petals=0.1),
        dict(t=p(0.52), top="#1b2b42", bottom="#b07a63", rain=0.4, bloom=0.75, petals=0.7),
        dict(t=p(0.64), top="#0d0a18", bottom="#2e2340", rain=0.7, bloom=0.5, petals=0.15),
        dict(t=p(0.75), top="#24365a", bottom="#d79a74", rain=0.25, bloom=1.0, petals=1.0),
        dict(t=p(0.88), top="#1c2840", bottom="#a78272", rain=0.12, bloom=1.0, petals=0.5),
        dict(t=round(dur + 0.1, 2), top="#0a0e18", bottom="#2a2a36", rain=0.0, bloom=1.0, petals=0.2),
    ]


def render(wav_path, out, duration, keyframes=None, seed=7, log=sys.stderr):
    DUR = duration
    keyframes = keyframes or default_keyframes(DUR)
    rng = np.random.default_rng(seed)
    N=int(DUR*FPS)
    # audio envelope
    a,sr=sf.read(wav_path,dtype="float32")
    hop=sr//FPS
    env=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)+1e-9) for i in range(N)])
    env=np.convolve(env,np.ones(6)/6,'same'); env=env/np.percentile(env,97)
    def hx(s): return np.array([int(s[i:i+2],16) for i in (1,3,5)],np.float32)/255
    # keyframes: time, top, bottom, rain, bloom, petals
    K=[(k['t'],k['top'],k['bottom'],k['rain'],k['bloom'],k['petals']) for k in keyframes]
    kt=np.array([k[0] for k in K])
    def key(t):
        i=np.searchsorted(kt,t)-1; i=min(max(i,0),len(K)-2)
        u=(t-kt[i])/(kt[i+1]-kt[i]); u=u*u*(3-2*u)
        A,B=K[i],K[i+1]
        return [hx(A[1])*(1-u)+hx(B[1])*u, hx(A[2])*(1-u)+hx(B[2])*u]+[A[j]*(1-u)+B[j]*u for j in (3,4,5)]
    yy=np.linspace(0,1,H,dtype=np.float32)[:,None,None]
    xx=np.linspace(-1,1,W,dtype=np.float32)[None,:,None]
    vig=(1-0.55*(xx**2*0.6+(yy*2-1)**2*0.5)).clip(0.25,1)
    # bokeh sprite
    def disk(r,soft):
        g=np.linspace(-1,1,2*r+1); X,Y=np.meshgrid(g,g); d=np.sqrt(X*X+Y*Y)
        return np.clip((1-d)/soft,0,1)**1.5
    NB=26
    bk=[dict(x=rng.uniform(0,W),y=rng.uniform(0,H),r=int(rng.uniform(10,38)),vx=rng.uniform(-6,6),vy=rng.uniform(-5,-1),
            c=np.array(rng.choice([[1,.85,.65],[.7,.85,1],[1,.7,.7],[.9,.9,1]]),np.float32),a=rng.uniform(.05,.16),ph=rng.uniform(0,6.28)) for _ in range(NB)]
    for b in bk: b["s"]=disk(b["r"],0.25)
    # rain
    NR=420
    rx=rng.uniform(0,W,NR); ry=rng.uniform(0,H,NR); rs=rng.uniform(500,900,NR); rl=rng.uniform(8,22,NR); ra=rng.uniform(.15,.5,NR)
    # flower sprites
    def flower(stage,col,size=220,petals=6,seed=0):
        r=np.random.default_rng(seed)
        im=Image.new("RGBA",(size,size),(0,0,0,0)); d=ImageDraw.Draw(im)
        c=size/2; L=size*0.42*(0.15+0.85*stage); wdt=L*0.42
        for layer in range(2):
            n=petals+layer*2
            for k in range(n):
                ang=k/n*2*math.pi+layer*0.3+r.uniform(-.08,.08)
                ll=L*(1-0.3*layer)
                pts=[]
                for s in np.linspace(0,1,24):
                    # petal outline (teardrop)
                    rad=ll*s; half=wdt*(1-0.3*layer)*math.sin(math.pi*s)**0.8*0.5
                    pts.append((rad,half))
                poly=[(c+p*math.cos(ang)-q*math.sin(ang),c+p*math.sin(ang)+q*math.cos(ang)) for p,q in pts]+\
                     [(c+p*math.cos(ang)+q*math.sin(ang),c+p*math.sin(ang)-q*math.cos(ang)) for p,q in reversed(pts)]
                shade=1-0.18*layer
                fc=tuple(int(255*min(1,x*shade)) for x in col)+(int(200*min(1,stage*1.6)),)
                d.polygon(poly,fill=fc)
        cr=size*0.05*(0.3+stage)
        d.ellipse([c-cr,c-cr,c+cr,c+cr],fill=(255,214,140,int(230*min(1,stage*2))))
        im=im.filter(ImageFilter.GaussianBlur(1.2))
        return np.asarray(im).astype(np.float32)/255
    cols=[(1,.78,.80),(1,.86,.74),(.96,.92,.98),(1,.70,.72)]
    ST=24
    spr=[[flower(s/(ST-1),cols[c],seed=c) for s in range(ST)] for c in range(len(cols))]
    NF=16
    fl=[]
    for i in range(NF):
        side=i%2
        bx=rng.uniform(30,W*0.3) if i%2 else rng.uniform(W*0.7,W-30)
        fl.append(dict(x=bx if i<8 else (rng.uniform(20,200) if side else rng.uniform(W-200,W-20)),
                       y=rng.uniform(H*0.78,H*1.02) if i<8 else rng.uniform(H*0.45,H*0.95),
                       sc=rng.uniform(.35,.85),c=int(rng.integers(len(cols))),th=rng.uniform(0,.95),ph=rng.uniform(0,6.28)))
    # petals falling
    NP=40
    px=rng.uniform(0,W,NP); py=rng.uniform(-H,H,NP); pv=rng.uniform(25,60,NP); pph=rng.uniform(0,6.28,NP); pc=rng.integers(len(cols),size=NP)
    petal=disk(4,0.6)
    bloomacc=np.zeros(NF)
    def blit(img,s,x,y,alpha=1.0,add=False,col=None):
        h,w=s.shape[:2]; x0,y0=int(x-w/2),int(y-h/2)
        xa,ya=max(x0,0),max(y0,0); xb,yb=min(x0+w,W),min(y0+h,H)
        if xa>=xb or ya>=yb: return
        sub=s[ya-y0:yb-y0, xa-x0:xb-x0]
        if add:
            img[ya:yb,xa:xb]+=sub[...,None]*col*alpha
        else:
            al=sub[...,3:4]*alpha
            img[ya:yb,xa:xb]=img[ya:yb,xa:xb]*(1-al)+sub[...,:3]*al
    for f in range(N):
        t=f/FPS; top,bot,rain,bloom,pet=key(t); e=float(env[f])
        img=(top*(1-yy)+bot*yy)*np.ones((1,W,1),np.float32)
        # soft horizon glow
        img+=0.10*bloom*np.exp(-((yy-0.82)**2)/0.02)*np.exp(-(xx**2)/0.6)*np.array([1,.75,.55],np.float32)
        for b in bk:
            x=(b["x"]+b["vx"]*t)%(W+80)-40; y=(b["y"]+b["vy"]*t)%(H+80)-40
            blit(img,b["s"],x,y,b["a"]*(0.7+0.3*math.sin(t*0.7+b["ph"]))*(0.8+0.4*e),add=True,col=b["c"])
        # flowers
        for i,F in enumerate(fl):
            target=np.clip((bloom-F["th"])/0.25,0,1)
            bloomacc[i]+= (target-bloomacc[i])*0.03
            st=bloomacc[i]
            if st<0.02: continue
            s=spr[F["c"]][min(int(st*(ST-1)),ST-1)]
            sc=F["sc"]*(1+0.03*e)
            hh=int(s.shape[0]*sc)
            if hh<4: continue
            si=np.asarray(Image.fromarray((s*255).astype(np.uint8)).resize((hh,hh),Image.BILINEAR).rotate(8*math.sin(t*0.5+F["ph"]),resample=Image.BILINEAR)).astype(np.float32)/255
            blit(img,si,F["x"]+4*math.sin(t*0.6+F["ph"]),F["y"],0.9)
        # falling petals
        if pet>0.02:
            for k in range(NP):
                y=(py[k]+pv[k]*t)%(H+40)-20; x=(px[k]+25*math.sin(t*0.8+pph[k])+10*t)%W
                blit(img,petal,x,y,0.55*pet,add=True,col=np.array(cols[pc[k]],np.float32))
        # rain
        if rain>0.01:
            layer=Image.new("L",(W,H),0); d=ImageDraw.Draw(layer)
            n=int(NR*rain)
            Y=(ry+rs*t)%(H+40)-20; X=(rx-0.08*rs*t)%W
            for k in range(n):
                d.line([(X[k],Y[k]),(X[k]+rl[k]*0.08,Y[k]+rl[k])],fill=int(255*ra[k]),width=1)
            r=np.asarray(layer,np.float32)[...,None]/255
            img+=r*np.array([.75,.82,.95],np.float32)*0.55
        img*=vig*(0.94+0.08*e)
        img+=rng.normal(0,0.006,(H,W,1)).astype(np.float32)
        out.write((np.clip(img,0,1)*255).astype(np.uint8).tobytes())
        if f%480==0: print(f"frame {f}/{N}",file=log,flush=True)

