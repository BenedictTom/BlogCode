#!/usr/bin/env python3
"""《Pi 与 DSH 主循环对比》封面：左右各 50% 的拼装版。

素材全部取自本地，不用外链图床：
    左半  source/images/DSH-Agent主循环/maid.png      440×440，带透明通道的立绘
    右半  /Users/smzdm/Downloads/screenshot-20261105-095904.png  1656×782，Pi 截图
版式：1600×900，中缝对半分；两侧同底色（取自截图背景 #eae5e3）；
      左半立绘按可见内容高度 88% 竖直居中，右半截图按宽度铺满、不裁内容。

用法：
    python3 make-vs-cover.py                 # 写到 ../../images/Agent主循环对比/cover.jpg
    python3 make-vs-cover.py --fit fill      # 右半改成铺满裁切
    python3 make-vs-cover.py --out /tmp/x.jpg
"""
import argparse
import os

from PIL import Image, ImageDraw

W, H = 1600, 900
LEFT_W = W // 2
BG = (234, 229, 227)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
MAID = os.path.join(REPO, "source/images/DSH-Agent主循环/maid.png")
PI = "/Users/smzdm/Downloads/screenshot-20261105-095904.png"
OUT = os.path.join(REPO, "source/images/Agent主循环对比/cover.jpg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--fit", choices=["contain", "fill"], default="fill",
                    help="右半截图的放法：contain 完整显示，fill 铺满裁切")
    args = ap.parse_args()

    canvas = Image.new("RGB", (W, H), BG)

    # 左半：立绘按可见内容高度 88% 居中（原图 440 见方，放大后靠 LANCZOS 收敛）
    maid = Image.open(MAID).convert("RGBA")
    char = maid.crop(maid.getbbox())
    scale = (H * 0.88) / char.height
    if round(char.width * scale) > LEFT_W * 0.94:
        scale = LEFT_W * 0.94 / char.width
    char = char.resize((max(1, round(char.width * scale)), max(1, round(char.height * scale))), Image.LANCZOS)
    canvas.paste(char, ((LEFT_W - char.width) // 2, (H - char.height) // 2), char)

    # 右半：截图
    pi = Image.open(PI).convert("RGB")
    if args.fit == "fill":
        s = max(LEFT_W / pi.width, H / pi.height)
        nw, nh = round(pi.width * s), round(pi.height * s)
        shot = pi.resize((nw, nh), Image.LANCZOS)
        x, y = (nw - LEFT_W) // 2, (nh - H) // 2
        shot = shot.crop((x, y, x + LEFT_W, y + H))
    else:
        shot = pi.resize((LEFT_W, round(pi.height * LEFT_W / pi.width)), Image.LANCZOS)
    canvas.paste(shot, (LEFT_W, (H - shot.height) // 2))

    # 中缝
    ImageDraw.Draw(canvas, "RGBA").line([(LEFT_W, 0), (LEFT_W, H)], fill=(0, 0, 0, 22), width=1)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    canvas.save(args.out, "JPEG", quality=88, optimize=True, progressive=True)
    print(f"{args.out} {canvas.size} {os.path.getsize(args.out):,} B "
          f"(maid {char.width}×{char.height} @ {(LEFT_W-char.width)//2},{(H-char.height)//2}; "
          f"pi {shot.width}×{shot.height} @ {LEFT_W},{(H-shot.height)//2})")


if __name__ == "__main__":
    main()
