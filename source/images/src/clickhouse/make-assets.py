#!/usr/bin/env python3
"""《ClickHouse 入门》配图生成器：封面 + 两张动图。

用法：
    python3 make-assets.py                 # 全部生成到 ../../images/ClickHouse入门/
    python3 make-assets.py --only cover    # cover | merge-gif | scan-gif

产物：
    cover.jpg      1600×900  封面
    merge.gif      900×360   后台合并：小 part 合并成大 part
    scan.gif       900×360   行存扫全列 vs 列存只扫需要的列
"""
import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ClickHouse入门"))
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"

BG_TOP, BG_BOT = (12, 18, 33), (22, 32, 55)
ACCENT = (249, 115, 22)
ACCENT_SOFT = (253, 186, 116)
TEXT = (236, 240, 247)
MUTED = (140, 154, 178)
DIM = (44, 56, 80)


def font(size):
    return ImageFont.truetype(FONT, size)


def gradient(w, h, top=BG_TOP, bot=BG_BOT):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return img


# ---------------------------------------------------------------- 封面
def make_cover():
    W, H, S = 1600, 900, 2
    img = gradient(W * S, H * S)
    d = ImageDraw.Draw(img)

    # 右侧示意：6 列，其中 2 列被查询命中
    base_x, base_y = 1010 * S, 250 * S
    col_w, gap, rows, cell_h = 52 * S, 10 * S, 14, 19 * S
    hit = {1, 4}
    for c in range(6):
        x = base_x + c * (col_w + gap)
        for r in range(rows):
            y = base_y + r * (cell_h + 4 * S)
            if c in hit:
                fill = ACCENT if r % 3 else ACCENT_SOFT
            else:
                shade = DIM[0] + int(10 * (r / rows))
                fill = (shade, shade + 12, shade + 30)
            d.rounded_rectangle([x, y, x + col_w, y + cell_h], radius=3 * S, fill=fill)
    d.text((base_x, base_y - 34 * S), "只读 2 / 6 列", font=font(20 * S), fill=MUTED)

    # 左侧文字
    x = 120 * S
    d.text((x, 250 * S), "DATABASE  ·  OLAP", font=font(22 * S), fill=ACCENT)
    d.text((x, 306 * S), "ClickHouse 入门", font=font(84 * S), fill=TEXT)
    d.text((x, 430 * S), "一个分析型数据库", font=font(40 * S), fill=TEXT)
    d.text((x, 486 * S), "为什么长这样", font=font(40 * S), fill=ACCENT_SOFT)
    d.text((x, 600 * S), "列存 · 向量化 · 稀疏索引 · MergeTree", font=font(23 * S), fill=MUTED)
    d.text((x, 780 * S), "26.8.41.14 LTS  ·  10,000,000 rows 实测", font=font(20 * S), fill=MUTED)

    img = img.resize((W, H), Image.LANCZOS)
    path = os.path.join(OUT, "cover.jpg")
    img.save(path, "JPEG", quality=88, optimize=True)
    # 断言：标题区不应过暗到看不清
    px = img.crop((110, 290, 900, 400)).convert("L")
    print(f"cover {path} {os.path.getsize(path)}B title-band luma={sum(px.getdata()) / (px.width * px.height):.1f}")


# ---------------------------------------------------------------- 合并动图
def make_merge_gif():
    W, H, S = 900, 360, 2
    frames = []
    # 32 → 16 → 8 → 4 → 2 → 1
    stages = [32, 16, 8, 4, 2, 1]
    per_stage = 6
    for stage in stages:
        for k in range(per_stage):
            img = gradient(W * S, H * S, (14, 20, 36), (24, 34, 58))
            d = ImageDraw.Draw(img)
            d.text((40 * S, 34 * S), "后台合并：小 part → 大 part", font=font(26 * S), fill=TEXT)
            d.text((40 * S, 74 * S), f"活跃 part 数：{stage}", font=font(22 * S), fill=ACCENT)
            d.text((40 * S, 108 * S), "写入只追加，从不原地修改；合并是异步的", font=font(17 * S), fill=MUTED)

            n = stage
            total_w = 800 * S
            bw = min(46 * S, total_w / n - 4 * S)
            gap = (total_w - n * bw) / max(1, n - 1)
            base_y = 190 * S
            bh = 70 * S
            glow = 1 - k / per_stage  # 越靠后越暗，表示「刚合并完」
            for i in range(n):
                x = 50 * S + i * (bw + gap)
                c = tuple(int(ACCENT[j] * (0.55 + 0.45 * glow)) for j in range(3))
                d.rounded_rectangle([x, base_y, x + bw, base_y + bh], radius=5 * S,
                                    fill=c, outline=(255, 255, 255, 40), width=1 * S)
            d.text((50 * S, 300 * S), "merge 由后台调度，写入路径不等它", font=font(17 * S), fill=MUTED)
            frames.append(img.resize((W, H), Image.LANCZOS))
    path = os.path.join(OUT, "merge.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=110, loop=0, optimize=True)
    print(f"merge-gif {path} {os.path.getsize(path)}B frames={len(frames)}")


# ---------------------------------------------------------------- 扫描动图
def make_scan_gif():
    W, H, S = 900, 380, 2
    cols, rows = 6, 12
    cell_w, cell_h = 46 * S, 16 * S
    gx, gy = 70 * S, 120 * S
    hit_cols = {1, 4}
    frames = []
    total = rows

    # 阶段一：行存，逐行扫全部列
    for r in range(total):
        img = gradient(W * S, H * S, (16, 22, 38), (26, 36, 60))
        d = ImageDraw.Draw(img)
        d.text((40 * S, 28 * S), "同一个查询：只要第 2 和第 5 列", font=font(22 * S), fill=TEXT)
        d.text((40 * S, 62 * S), "行存：读一行 = 读全部 6 列", font=font(19 * S), fill=(248, 113, 113))
        for c in range(cols):
            for rr in range(rows):
                x = gx + c * (cell_w + 6 * S)
                y = gy + rr * (cell_h + 5 * S)
                if rr == r:
                    fill = (239, 68, 68) if c not in hit_cols else ACCENT
                elif rr < r:
                    fill = (90, 60, 60) if c not in hit_cols else (120, 80, 40)
                else:
                    fill = DIM
                d.rounded_rectangle([x, y, x + cell_w, y + cell_h], radius=3 * S, fill=fill)
        read = (r + 1) * cols
        d.text((40 * S, 340 * S), f"已读列数 {read} / 目标 {total * 2}", font=font(19 * S), fill=MUTED)
        frames.append(img.resize((W, H), Image.LANCZOS))

    # 阶段二：列存，只扫需要的列
    for r in range(total):
        img = gradient(W * S, H * S, (16, 22, 38), (26, 36, 60))
        d = ImageDraw.Draw(img)
        d.text((40 * S, 28 * S), "同一个查询：只要第 2 和第 5 列", font=font(22 * S), fill=TEXT)
        d.text((40 * S, 62 * S), "列存：只读这 2 列，其余 4 列一个字节都不碰", font=font(19 * S), fill=(74, 222, 128))
        for c in range(cols):
            for rr in range(rows):
                x = gx + c * (cell_w + 6 * S)
                y = gy + rr * (cell_h + 5 * S)
                if c in hit_cols:
                    fill = ACCENT if rr <= r else (120, 80, 40)
                else:
                    fill = DIM
                d.rounded_rectangle([x, y, x + cell_w, y + cell_h], radius=3 * S, fill=fill)
        read = min((r + 1) * 2, total * 2)
        d.text((40 * S, 340 * S), f"已读列数 {read} / 目标 {total * 2}", font=font(19 * S), fill=MUTED)
        frames.append(img.resize((W, H), Image.LANCZOS))

    path = os.path.join(OUT, "scan.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=140, loop=0, optimize=True)
    print(f"scan-gif {path} {os.path.getsize(path)}B frames={len(frames)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["cover", "merge-gif", "scan-gif"])
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.only in (None, "cover"):
        make_cover()
    if a.only in (None, "merge-gif"):
        make_merge_gif()
    if a.only in (None, "scan-gif"):
        make_scan_gif()
