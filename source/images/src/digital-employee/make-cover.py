#!/usr/bin/env python3
"""数字员工一文封面：1600x900。

素材是用户指定的 943x443 图（偏亮、均值 RGB 133/125/152）。做法固定：
整图放大模糊压暗当底，原图居中成卡片，底部加暗色渐变承载文字。

用法：
    python3 make-cover.py --src /tmp/cover-src.jpg --out ../../Pi-数字员工/cover.jpg
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2  # 超采样倍数，缩回目标尺寸时做抗锯齿
W, H = 1600 * S, 900 * S

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
KICKER = (146, 186, 255)
BODY = (196, 208, 228)
MUTED = (140, 154, 178)

TITLE = "如何使用 Pi 创建一个数字员工"
SUBTITLE = "从一份包定义，到记忆、流程、定时任务与连接器"


def font(size, weight=1):
    try:
        return ImageFont.truetype(FONT, size * S, index=weight)
    except OSError:
        return ImageFont.truetype(FONT, size * S, index=0)


def cover_scale(im, size):
    tw, th = size
    scale = max(tw / im.width, th / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    out = im.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return out.crop((left, top, left + tw, top + th))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    src = Image.open(args.src).convert("RGB")

    # 底：整图铺满 → 高斯模糊 → 压暗偏蓝
    bg = cover_scale(src, (W, H)).filter(ImageFilter.GaussianBlur(34 * S))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (9, 14, 28)), 0.56)

    canvas = bg.copy()

    # 卡片：按原图比例居中放置，留出上方呼吸位
    card_w = 1120 * S
    card_h = round(src.height * card_w / src.width)
    card = src.resize((card_w, card_h), Image.LANCZOS)
    cx = (W - card_w) // 2
    cy = 104 * S

    # 卡片投影（柔边暗块，贴图之前画）
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (cx - 8 * S, cy - 8 * S, cx + card_w + 8 * S, cy + card_h + 18 * S),
        radius=14 * S,
        fill=(0, 0, 0, 150),
    )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(12 * S)))
    canvas.paste(card, (cx, cy))
    canvas = canvas.convert("RGB")

    # 底部渐变：从卡片下沿淡出到纯暗色，给文字留对比
    band_top = cy + card_h - 40 * S
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for y in range(band_top, H):
        t = (y - band_top) / (H - band_top)
        a = int(232 * min(1.0, t ** 0.62))
        bd.line([(0, y), (W, y)], fill=(9, 13, 26, a))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), band).convert("RGB")

    d = ImageDraw.Draw(canvas)
    x = (W - card_w) // 2 + 24 * S

    d.text((x, 668 * S), "PI  ·  DIGITAL EMPLOYEE", font=font(24), fill=KICKER)

    size = 64
    while size > 40 and d.textlength(TITLE, font=font(size)) > card_w - 48 * S:
        size -= 2
    d.text((x, 708 * S), TITLE, font=font(size), fill="#ffffff")
    d.text((x, 800 * S), SUBTITLE, font=font(27, 0), fill=BODY)
    d.text((x, 848 * S), "一个目录就是一个员工", font=font(21, 0), fill=MUTED)

    # 程序化验收：文字区足够暗、标题不出界
    probe = canvas.convert("L").crop((x, 700 * S, x + card_w - 48 * S, 900 * S))
    mean = sum(probe.getdata()) / (probe.width * probe.height)
    tw = d.textlength(TITLE, font=font(size))
    print(f"标题 {size}px 宽 {tw / S:.0f}px / 可用 {card_w - 48 * S}px；文字区平均亮度 {mean:.1f}")
    assert tw <= card_w - 48 * S, "标题出界"
    assert mean < 64, f"文字区太亮，白字对比不足：{mean:.1f}"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    final = canvas.resize((1600, 900), Image.LANCZOS)
    final.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    print(f"写出 {out}  {out.stat().st_size:,} B")


if __name__ == "__main__":
    main()
