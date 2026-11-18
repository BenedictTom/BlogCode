#!/usr/bin/env python3
"""《Context：从人与人到 Agent 与 Agent》配图生成器。

产出两张动图：
  layer-loss.gif  同一份信息穿过三层时的逐层丢失
  window.gif      上下文窗口的填充、压缩与二次摘要

用法：python3 make-gifs.py [--out DIR]
"""
import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
BG = (14, 21, 34)
FG = (232, 238, 250)
DIM = (140, 158, 188)
BLUE = (56, 189, 248)
RED = (248, 113, 113)
GREEN = (52, 211, 153)
AMBER = (251, 191, 36)
GRAY = (148, 163, 184)


def font(size):
    return ImageFont.truetype(FONT, size)


# ---------------------------------------------------------------- layer-loss
def make_layer_loss(out_path):
    W, H = 900, 340
    N = 12
    GATES = [(300, "人–人"), (560, "人–Agent"), (820, "Agent–Agent")]
    DROP1 = {8, 9, 10, 11}
    DROP2 = {4, 5, 6}
    frames = 40
    start_x, speed = 40, 12.5

    f_title = font(26)
    f_label = font(17)
    f_cap = font(19)
    caps = [
        (0, "同一份信息：12 条，包含记忆、知识、任务状态和对话历史"),
        (10, "人–人：共享经历补全了省略，一句话就够"),
        (22, "人–Agent：漏掉的不会被追问，只会被猜"),
        (32, "Agent–Agent：字段对得上，语义丢了一半"),
    ]

    imgs = []
    for fr in range(frames):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.text((40, 26), "同一份信息，三层传递，逐层丢失", font=f_title, fill=FG)

        # 通道底纹
        d.rounded_rectangle([40, 108, W - 40, 176], radius=8, outline=(38, 52, 78), width=2)

        # 闸门
        for gx, gl in GATES:
            for yy in range(96, 192, 12):
                d.line([(gx, yy), (gx, yy + 6)], fill=(52, 70, 100), width=2)
            tb = d.textbbox((0, 0), gl, font=f_label)
            d.text((gx - (tb[2] - tb[0]) / 2, 72), gl, font=f_label, fill=DIM)

        # 令牌
        for i in range(N):
            x = start_x + i * 26 + speed * fr
            y = 128
            dropping = False
            if i in DROP1 and x > GATES[0][0] + 6:
                dropping = True
                t = min(1.0, (x - GATES[0][0] - 6) / 60.0)
            elif (i not in DROP1) and i in DROP2 and x > GATES[1][0] + 6:
                dropping = True
                t = min(1.0, (x - GATES[1][0] - 6) / 60.0)
            if jumping := (i in DROP1 and x > GATES[0][0] and x < GATES[0][0] + 6):
                pass
            if dropping:
                yy = y + t * 46
                shade = tuple(int(c + (BG[k] - c) * t) for k, c in enumerate(RED))
                if t < 0.98:
                    d.rounded_rectangle([x, yy, x + 14, yy + 14], radius=3, fill=shade)
                continue
            if x > W - 46:
                continue
            col = BLUE if x < GATES[0][0] else (AMBER if x < GATES[1][0] else GREEN)
            d.rounded_rectangle([x, y, x + 14, y + 14], radius=3, fill=col)

        # 字幕
        cap = caps[0][1]
        for t0, txt in caps:
            if fr >= t0:
                cap = txt
        d.text((40, 268), cap, font=f_cap, fill=DIM)
        imgs.append(img.convert("P", palette=Image.ADAPTIVE, colors=64))

    imgs[0].save(out_path, save_all=True, append_images=imgs[1:], duration=110, loop=0)
    return out_path


# ------------------------------------------------------------------- window
def make_window(out_path):
    W, H = 900, 300
    CELLS = 24
    x0, x1, y0, y1 = 60, 840, 92, 178
    cw = (x1 - x0) / CELLS
    SEG = [(0, 3, BLUE, "记忆"), (3, 9, GREEN, "知识"), (9, 12, AMBER, "任务状态"), (12, 24, GRAY, "对话历史")]
    NEWGRAY = (176, 186, 202)

    f_title = font(25)
    f_legend = font(15)
    f_cap = font(19)
    f_small = font(14)

    def base_color(i):
        for a, b, c, _ in SEG:
            if a <= i < b:
                return c
        return GRAY

    FILL_END, COMP_END, REFILL_END = 12, 22, 34

    imgs = []
    for fr in range(REFILL_END):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.text((60, 26), "上下文窗口：填满 → 压缩 → 又被填满", font=f_title, fill=FG)

        lx = 60
        for _, _, c, name in SEG:
            d.rounded_rectangle([lx, 64, lx + 12, 76], radius=2, fill=c)
            d.text((lx + 18, 62), name, font=f_legend, fill=DIM)
            lx += 22 + int(d.textbbox((0, 0), name, font=f_legend)[2]) + 22

        # 各阶段：哪些格子有内容、什么颜色
        cells = {}
        note = None
        if fr < FILL_END:
            filled = int((fr + 1) / FILL_END * CELLS)
            for i in range(filled):
                cells[i] = base_color(i)
            cap = "记忆、知识、任务状态、对话历史挤进同一个窗口"
        elif fr < COMP_END:
            step = fr - FILL_END + 1            # 1..10
            for i in range(0, 12):
                cells[i] = base_color(i)
            for i in range(12, 16):
                cells[i] = (120, 132, 152)      # 摘要块
            keep = max(0, 8 - step)             # 16..23 逐格消失
            for i in range(16, 16 + keep):
                cells[i] = GRAY
            note = "压缩"
            cap = "触发压缩：12 格历史压成 4 格摘要，细节不可逆"
        else:
            step = fr - COMP_END + 1            # 1..12
            for i in range(0, 12):
                cells[i] = base_color(i)
            for i in range(12, 16):
                cells[i] = (120, 132, 152)
            for i in range(16, min(24, 16 + step)):
                cells[i] = NEWGRAY
            cap = "新对话继续进来；摘要再被摘要，误差累积"

        for i in range(CELLS):
            cx0, cx1 = x0 + i * cw + 2, x0 + (i + 1) * cw - 2
            d.rounded_rectangle([cx0, y0, cx1, y1], radius=3, outline=(38, 52, 78), width=1)
            if i in cells:
                d.rounded_rectangle([cx0, y0, cx1, y1], radius=3, fill=cells[i])

        # 满/压缩 时的红框
        if FILL_END <= fr < COMP_END:
            d.rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], radius=6, outline=RED, width=3)
            tb = d.textbbox((0, 0), "满", font=f_small)
            d.text((x1 - (tb[2] - tb[0]), y0 - 26), "满", font=f_small, fill=RED)

        if fr >= FILL_END:
            sx = x0 + 12 * cw
            d.line([(sx, y1 + 6), (sx, y1 + 20)], fill=DIM, width=1)
            d.text((sx - 4, y1 + 22), "摘要（有损）", font=f_small, fill=DIM)

        if fr >= COMP_END + 6:
            d.text((x0 + 13 * cw, y0 - 26), "第 2 次摘要 · 误差累积", font=f_small, fill=RED)

        # 占用计数：保证每帧都有变化，避免被合并
        used = len([i for i in cells if cells[i] is not None])
        d.text((60, 236), f"占用 {used:2d}/{CELLS} 格    " + cap, font=f_cap, fill=DIM)
        imgs.append(img.convert("P", palette=Image.ADAPTIVE, colors=64))

    imgs[0].save(out_path, save_all=True, append_images=imgs[1:], duration=120, loop=0)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "..", "Context-从人到Agent"))
    args = ap.parse_args()
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    for fn in (make_layer_loss, make_window):
        p = os.path.join(out_dir, "layer-loss.gif" if fn is make_layer_loss else "window.gif")
        fn(p)
        print(f"{p}  {os.path.getsize(p)} bytes")


if __name__ == "__main__":
    main()
