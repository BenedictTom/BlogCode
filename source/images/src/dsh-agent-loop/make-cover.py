from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 900
S = 2  # supersample
img = Image.new("RGB", (W*S, H*S), "#0b1220")
d = ImageDraw.Draw(img)

# vertical gradient
top, bot = (11, 18, 32), (22, 33, 56)
for y in range(H*S):
    t = y / (H*S - 1)
    d.line([(0, y), (W*S, y)], fill=tuple(int(top[i] + (bot[i]-top[i])*t) for i in range(3)))

# subtle grid
for x in range(0, W*S, 80*S):
    d.line([(x, 0), (x, H*S)], fill=(28, 39, 62))
for y in range(0, H*S, 80*S):
    d.line([(0, y), (W*S, y)], fill=(28, 39, 62))

F = "/System/Library/Fonts/Hiragino Sans GB.ttc"
def font(sz, weight=1):
    try: return ImageFont.truetype(F, sz*S, index=weight)
    except Exception: return ImageFont.truetype(F, sz*S, index=0)

# accent bar
d.rounded_rectangle([80*S, 300*S, 92*S, 560*S], radius=6*S, fill="#f97316")

x = 130*S
d.text((x, 236*S), "DSH", font=font(40, 1), fill="#7dd3fc")
d.text((x, 300*S), "Agent 主循环", font=font(86, 1), fill="#ffffff")
d.text((x, 424*S), "一条用户消息，到底走过了什么", font=font(38, 0), fill="#c7d2e3")
d.text((x, 490*S), "轮次 / 步骤 / 工具池 / 取消", font=font(28, 0), fill="#8fa3bf")
d.text((x, 534*S), "对着 dsh-agent-loop 源码逐条核过", font=font(28, 0), fill="#8fa3bf")

# divider
d.line([(x, 620*S), (700*S, 620*S)], fill=(255,255,255,40), width=2*S)
d.text((x, 648*S), "dsh-agent-loop  ·  dsh-agent  ·  dsh-tools", font=font(24, 0), fill="#64748b")
d.text((x, 686*S), "DSH v0.1.5-alpha.1", font=font(24, 0), fill="#64748b")

# character
ch = Image.open(".tmp-fig/whale-maid.png").convert("RGBA")
target_h = 830*S
scale = target_h / ch.height
ch = ch.resize((int(ch.width*scale), target_h), Image.LANCZOS)
mask = ch.split()[3]
img.paste(ch, (W*S - ch.width - 30*S, H*S - ch.height - 10*S), mask)

img = img.resize((W, H), Image.LANCZOS)
import os
os.makedirs("source/images/DSH-Agent主循环", exist_ok=True)
img.save("source/images/DSH-Agent主循环/cover.png", optimize=True)
print("saved", img.size)
