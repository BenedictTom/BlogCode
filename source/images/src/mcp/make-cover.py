# 《MCP 全解》封面与正文插图
# 用法：在仓库根目录 `python3 source/images/src/mcp/make-cover.py`
# 输入：source/images/src/mcp/mcp-source.gif（用户提供的 1080x1003 动画插图，12 帧）
# 输出：source/images/MCP全解/cover.gif（1000x563，6 帧动画封面）
#       source/images/MCP全解/cover.jpg（静态首帧，给 og:image 兜底）
#       source/images/MCP全解/mcp-illustration.gif（720 宽正文插图）
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 2000, 1126                      # 2 倍画布，最后降采样到 1000x563
SRC = "source/images/src/mcp/mcp-source.gif"
OUT_DIR = "source/images/MCP全解"
CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
CX0, CY0, CW, CH = 1150, 110, 810, 910  # 右侧卡片可用区域

f = lambda s, i=0: ImageFont.truetype(CJK, s, index=i)


def gradient():
    base = Image.new("RGB", (W, H), "#0a1020")
    d = ImageDraw.Draw(base)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10 + 16 * t), int(16 + 26 * t), int(32 + 52 * t)))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(g)
    for x in range(0, W, 128):
        dg.line([(x, 0), (x, H)], fill=(120, 170, 255, 14))
    for y in range(0, H, 128):
        dg.line([(0, y), (W, y)], fill=(120, 170, 255, 14))
    base = Image.alpha_composite(base.convert("RGBA"), g)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([-520, -640, 1240, 840], fill=(64, 120, 255, 60))
    return Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(240)))


def rounded(img, r=56):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], radius=r, fill=255)
    o = img.convert("RGBA")
    o.putalpha(m)
    return o


def compose(i):
    bg = gradient()
    d = ImageDraw.Draw(bg)
    d.text((150, 290), "PROTOCOL  /  MCP", font=f(58), fill=(120, 180, 255))
    d.line([(150, 386), (470, 386)], fill=(255, 122, 69), width=8)
    d.text((150, 452), "MCP 全解", font=f(184, 1), fill=(255, 255, 255))
    d.text((150, 706), "从 stdio 到无状态，", font=f(96, 1), fill=(210, 226, 255))
    d.text((150, 838), "再到网关与高并发", font=f(96, 1), fill=(210, 226, 255))
    d.text((150, 1000), "两种传输 · 五个版本 · 无状态改造", font=f(46), fill=(150, 172, 205))
    d.text((150, 1062), "网关聚合 · 扩容套路 · 三十行跑通", font=f(46), fill=(150, 172, 205))

    src = Image.open(SRC)
    src.seek(i % getattr(src, "n_frames", 1))
    fr = src.convert("RGBA")
    r = min(CW / fr.width, CH / fr.height)
    fr = fr.resize((int(fr.width * r), int(fr.height * r)), Image.LANCZOS)
    card = rounded(fr)
    x0 = CX0 + (CW - card.width) // 2
    y0 = CY0 + (CH - card.height) // 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [x0 + 18, y0 + 32, x0 + card.width + 18, y0 + card.height + 32], radius=60, fill=(0, 0, 0, 140))
    bg = Image.alpha_composite(bg, sh.filter(ImageFilter.GaussianBlur(44)))
    bg.alpha_composite(card, (x0, y0))
    return bg.convert("RGB").resize((1000, 563), Image.LANCZOS)


os.makedirs(OUT_DIR, exist_ok=True)
frames = [compose(i).quantize(colors=128, method=Image.MEDIANCUT) for i in (0, 2, 4, 6, 8, 10)]
frames[0].save(os.path.join(OUT_DIR, "cover.gif"), save_all=True,
               append_images=frames[1:], duration=170, loop=0, optimize=True)
frames[0].convert("RGB").save(os.path.join(OUT_DIR, "cover.jpg"), quality=90)

# 正文插图：等比缩到 720 宽，保留 12 帧动画
ill = Image.open(SRC)
n = getattr(ill, "n_frames", 1)
nw = 720
nh = int(ill.size[1] * nw / ill.size[0])
out = []
for i in range(n):
    ill.seek(i)
    out.append(ill.convert("RGB").resize((nw, nh), Image.LANCZOS).quantize(colors=128, method=Image.MEDIANCUT))
out[0].save(os.path.join(OUT_DIR, "mcp-illustration.gif"), save_all=True,
            append_images=out[1:], duration=110, loop=0, optimize=True)

for name in ("cover.gif", "cover.jpg", "mcp-illustration.gif"):
    print(name, os.path.getsize(os.path.join(OUT_DIR, name)))
