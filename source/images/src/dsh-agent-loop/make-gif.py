from PIL import Image, ImageDraw, ImageFont
import os

W, H, S = 1000, 430, 2
F = "/System/Library/Fonts/Hiragino Sans GB.ttc"
def f(sz, w=0):
    try: return ImageFont.truetype(F, sz*S, index=w)
    except Exception: return ImageFont.truetype(F, sz*S, index=0)

BG=(13,20,34); NODE=(24,34,54); NODE_HI=(37,99,235); EDGE=(70,85,110); TXT=(226,232,240); SUB=(148,163,184); ORANGE=(249,115,22); GREEN=(34,197,94)

nodes=[
 ("inbox","消息排队", 35),
 ("认领一步","claim + 开 step", 230),
 ("模型推理","stream 回包", 425),
 ("工具执行","并行池 / 屏障", 620),
 ("判定","还有活吗", 815),
]
NW, NH, NY = 150, 96, 150

def base():
    img=Image.new("RGB",(W*S,H*S),BG); d=ImageDraw.Draw(img)
    d.text((40*S,36*S),"一个轮次里，循环是怎么转的",font=f(26,1),fill=TXT)
    d.text((40*S,78*S),"工具跑完就回到模型；模型不再调工具，这个轮次就收尾",font=f(15,0),fill=SUB)
    return img,d

def draw_nodes(d, active):
    for i,(t,s,x) in enumerate(nodes):
        on = i==active
        fill = NODE_HI if on else NODE
        d.rounded_rectangle([x*S,NY*S,(x+NW)*S,(NY+NH)*S],radius=12*S,fill=fill,
                            outline=ORANGE if on else (45,60,86), width=(4 if on else 2)*S)
        d.text((x*S+14*S,(NY+22)*S),t,font=f(17,1),fill=TXT if on else (203,213,225))
        d.text((x*S+14*S,(NY+52)*S),s,font=f(12,0),fill=(219,234,254) if on else SUB)
    for i in range(len(nodes)-1):
        x1=(nodes[i][2]+NW)*S; x2=nodes[i+1][2]*S; y=(NY+NH//2)*S
        d.line([(x1+6*S,y),(x2-8*S,y)],fill=EDGE,width=3*S)
        d.polygon([(x2-4*S,y),(x2-16*S,y-7*S),(x2-16*S,y+7*S)],fill=EDGE)

def back_edge(d, on, label):
    x_from=(nodes[4][2]+NW//2)*S; x_to=(nodes[2][2]+NW//2)*S; yb=(NY+NH)*S
    c = ORANGE if on else (45,60,86)
    d.line([(x_from,yb+6*S),(x_from,yb+34*S),(x_to,yb+34*S),(x_to,yb+8*S)],fill=c,width=3*S,joint="curve")
    d.polygon([(x_to,yb+4*S),(x_to-7*S,yb+18*S),(x_to+7*S,yb+18*S)],fill=c)
    d.text(((x_to+x_from)//2-34*S, yb+40*S), label, font=f(13,0), fill=ORANGE if on else SUB)

def footer(d, text, color=SUB):
    d.text((40*S,368*S),text,font=f(15,0),fill=color)

frames=[]
seq=[
 (0,"turn 1 · step 0 · inbox 里有 1 条消息"),
 (1,"turn 1 · step 1 · 认领：next-step 输入 + 一条排队消息"),
 (2,"turn 1 · step 1 · 模型流式回包，产出 3 个 tool-call"),
 (3,"turn 1 · step 1 · 3 个调用进滚动池并行跑"),
 (4,"turn 1 · step 1 · 模型仍要工具 → 继续"),
]
for act,cap in seq:
    img,d=base(); draw_nodes(d,act); back_edge(d,False,"下一个 step"); footer(d,cap)
    frames.append(img)
for act,cap in [(2,"turn 1 · step 2 · 带着工具结果再问一次模型"),
                (3,"turn 1 · step 2 · 这次 1 个调用"),
                (4,"turn 1 · step 2 · 没有 tool-call → 这一步完成")]:
    img,d=base(); draw_nodes(d,act); back_edge(d,act==2,"下一个 step"); footer(d,cap)
    frames.append(img)
img,d=base(); draw_nodes(d,-1); back_edge(d,False,"下一个 step")
d.rounded_rectangle([40*S,352*S,470*S,392*S],radius=10*S,fill=(22,101,52),outline=GREEN,width=2*S)
d.text((58*S,362*S),"turn/end: completed",font=f(16,1),fill=(187,247,208))
footer(d,"两个 step，一次轮次收尾——这就是全部魔法")
frames.append(img)

out=[fr.resize((W,H),Image.LANCZOS).convert("P",palette=Image.ADAPTIVE,colors=96) for fr in frames]
durs=[900,900,900,900,1100,900,900,900,2200]
os.makedirs("source/images/DSH-Agent主循环",exist_ok=True)
out[0].save("source/images/DSH-Agent主循环/step-loop.gif",save_all=True,append_images=out[1:],
            duration=durs,loop=0,optimize=True,disposal=1)
print("bytes:",os.path.getsize("source/images/DSH-Agent主循环/step-loop.gif"))
