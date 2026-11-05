#!/usr/bin/env python3
"""《Pi 与 DSH 主循环对比》封面：左右各 50% 的拼装版。

左半：鲸鱼娘（DSH 系列用过的角色图，1024×1024，等比铺满 800×900，左右各裁 50px）
右半：Pi 的截图（1656×782，先铺一层同图模糊底，再把原图等比放进中间，不裁内容）
接缝：1px 半透明分割线

用法：
    python3 make-vs-cover.py            # 写到 ../../images/Agent主循环对比/cover.jpg
    python3 make-vs-cover.py --out /tmp/x.jpg
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFilter

W, H = 1600, 900
LEFT_W = W // 2

MAID = "/tmp/maid1024.png"
PI = "/Users/smzdm/Downloads/screenshot-20261105-095904.png"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "../../../images/Agent主循环对比/cover.jpg")


def cover(im, box, focus_x=0.5):
    """等比铺满 box，按 focus_x 决定横向裁切重心。"""
    bw, bh = box
    scale = max(bw / im.width, bh / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = round((nw - bw) * focus_x)
    y = round((nh - bh) / 2)
    return im.crop((x, y, x + bw, y + bh))


def rounded(im, radius):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--plate", type=float, default=0.38, help="右半模糊底的压暗系数")
    args = ap.parse_args()

    canvas = Image.new("RGB", (W, H), (234, 229, 227))

    # 左半：鲸鱼娘
    maid = Image.open(MAID).convert("RGB")
    canvas.paste(cover(maid, (LEFT_W, H), focus_x=0.5), (0, 0))

    # 右半：模糊底 + 原图
    pi = Image.open(PI).convert("RGB")
    plate = cover(pi, (LEFT_W, H)).filter(ImageFilter.GaussianBlur(26))
    k = args.plate
    plate = Image.eval(plate, lambda v: int(v * k) + 8)
    canvas.paste(plate, (LEFT_W, 0))

    inset = 40
    shot = pi.resize((LEFT_W - inset * 2, round(pi.height * (LEFT_W - inset * 2) / pi.width)), Image.LANCZOS)
    shot = rounded(shot, 10)
    sx, sy = LEFT_W + inset, (H - shot.height) // 2

    shadow = Image.new("RGBA", (shot.width + 48, shot.height + 48), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((24, 28, 24 + shot.width, 28 + shot.height), 12, fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    canvas.paste(Image.new("RGB", shadow.size, (0, 0, 0)), (sx - 24, sy - 24), shadow)

    canvas.paste(shot, (sx, sy), shot)
    ImageDraw.Draw(canvas).rounded_rectangle(
        (sx, sy, sx + shot.width - 1, sy + shot.height - 1), 10, outline=(255, 255, 255), width=1)

    # 接缝
    d = ImageDraw.Draw(canvas, "RGBA")
    d.line([(LEFT_W, 0), (LEFT_W, H)], fill=(0, 0, 0, 26), width=1)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    canvas.save(args.out, "JPEG", quality=84, optimize=True, progressive=True)
    print(f"{args.out} {canvas.size} {os.path.getsize(args.out):,} B")


if __name__ == "__main__":
    main()
