#!/usr/bin/env python3
"""Pi 系列封面生成器。

素材：用户提供的截图（默认 /Users/smzdm/Downloads/screenshot-20261105-095904.png）
版式：深色品牌底 + 顶部标题区 + 居中截图卡片（等比完整显示，不裁切）+ 底部来源行。

用法：
    python3 make-cover.py                 # 生成全部九张到 ../../images/<slug>/cover.png
    python3 make-cover.py --slug Pi-入门   # 只生成一张
    python3 make-cover.py --out /tmp/x     # 输出到别的目录（预览用，不动仓库）
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 900
S = 2                      # 超采样倍数
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
ART = "/Users/smzdm/Downloads/screenshot-20261105-095904.png"

# slug -> (kicker序号, 标题行列表, 副标题)
ARTICLES = {
    "Pi-入门":      (1, ["Pi 入门", "从一条命令，到一个会改代码的 agent"]),
    "Pi-Loop":      (2, ["Pi 的 Agent Loop", "一次请求转几圈，它凭什么知道该停了"]),
    "Pi-会话树":    (3, ["Pi 的会话树", "一条对话为什么不是一条线"]),
    "Pi-上下文":    (4, ["Pi 的上下文工程", "每次请求，模型到底看到了什么"]),
    "Pi-工具":      (5, ["Pi 怎么定义一个工具", "一张卡片上的十个字段"]),
    "Pi-ai":        (6, ["pi-ai", "43 个供应商，10 种协议，一套流"]),
    "Pi-Durable-上": (7, ["Pi Durable（上）", "先落盘，再显示"]),
    "Pi-Durable-下": (8, ["Pi Durable（下）", "谁在跑，谁在看"]),
    "Pi-Codemode":  (9, ["Pi-Codemode", "让模型写一段脚本去调工具"]),
    # 跨系列对比篇：同版式，但 kicker 与页脚换成两边仓库
    "Agent主循环对比": (10, ["同一个 Agent 主循环",
                          "两种工程答案：Pi 与 DSH 对照解剖"]),
    "Pi-MCP与Codemode": (10, ["Codemode 与 MCP",
                              "先拒绝，为什么又加回来"]),
}

OVERRIDES = {
    "Agent主循环对比": {
        "kicker": "AGENT  ·  PI vs DSH",
        "footer_card": "earendil-works/pi 395f3e0  ·  @deepseek-ai/dsh-agent-loop",
        "footer_bleed": "earendil-works/pi 395f3e0  ·  dsh-agent-loop",
    },
    "Pi-MCP与Codemode": {
        "kicker": "PI SERIES  ·  MCP × CODEMODE",
        "footer_card": "earendil-works/pi 395f3e0  ·  coding-agent 1.5.0  ·  mcp.json",
        "footer_bleed": "earendil-works/pi  ·  MCP × CODEMODE",
    },
}


def meta(slug):
    ov = OVERRIDES.get(slug, {})
    return ov.get("kicker") or f"PI SERIES  ·  {ARTICLES[slug][0]:02d} / 09", ov

BG_TOP, BG_BOT = (11, 18, 32), (20, 30, 52)
ACCENT = "#f97316"
KICKER = "#7dd3fc"
BODY = "#c7d2e3"
MUTED = "#7f8ea8"


def font(size, weight=1):
    try:
        return ImageFont.truetype(FONT, size * S, index=weight)
    except Exception:
        return ImageFont.truetype(FONT, size * S, index=0)


def make(slug, art_path=ART, out_dir=None):
    idx, lines = ARTICLES[slug]
    canvas = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))
    d = ImageDraw.Draw(canvas)

    # 背景渐变
    for y in range(H * S):
        t = y / (H * S - 1)
        d.line([(0, y), (W * S, y)],
               fill=tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3)) + (255,))
    # 网格
    for x in range(0, W * S, 80 * S):
        d.line([(x, 0), (x, H * S)], fill=(28, 39, 62, 255))
    for y in range(0, H * S, 80 * S):
        d.line([(0, y), (W * S, y)], fill=(28, 39, 62, 255))

    # 顶部文字区
    kicker, ov = meta(slug)
    d.text((96 * S, 62 * S), kicker, font=font(26), fill=KICKER)
    d.text((96 * S, 112 * S), lines[0], font=font(62), fill="#ffffff")
    d.text((96 * S, 196 * S), lines[1], font=font(30, 0), fill=BODY)

    # 右侧序号大数字
    big = font(120)
    tw = d.textlength(f"{idx:02d}", font=big)
    d.text((W * S - 96 * S - tw, 84 * S), f"{idx:02d}", font=big, fill=(255, 255, 255, 18))

    # 截图卡片：限制在 (96,272)-(1504,838) 内等比完整显示
    art = Image.open(art_path).convert("RGBA")
    box_w, box_h = (1504 - 96) * S, (838 - 272) * S
    scale = min(box_w / art.width, box_h / art.height)
    aw, ah = int(art.width * scale), int(art.height * scale)
    art = art.resize((aw, ah), Image.LANCZOS)
    ax = (W * S - aw) // 2
    ay = (272 * S) + (box_h - ah) // 2

    # 投影
    shadow = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([ax - 6 * S, ay + 10 * S, ax + aw + 6 * S, ay + ah + 18 * S],
                         radius=18 * S, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18 * S))
    canvas = Image.alpha_composite(canvas, shadow)

    # 圆角遮罩贴图
    mask = Image.new("L", (aw, ah), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, aw - 1, ah - 1], radius=14 * S, fill=255)
    canvas.paste(art, (ax, ay), mask)

    # 描边
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([ax, ay, ax + aw - 1, ay + ah - 1], radius=14 * S,
                        outline=(255, 255, 255, 60), width=2 * S)

    # 底部来源行
    d.text((96 * S, 856 * S),
           ov.get("footer_card") or "earendil-works/pi  ·  HEAD 395f3e0  ·  coding-agent 1.5.0",
           font=font(22, 0), fill=MUTED)

    out = canvas.resize((W, H), Image.LANCZOS).convert("RGB")
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{slug}.jpg")
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "..", slug, "cover.jpg")
        os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path, quality=88, optimize=True, progressive=True)
    return path


def make_bleed(slug, art_path=ART, out_dir=None):
    """变体 B：截图铺满整张封面（左右各裁一部分），左侧压深色渐变放标题。"""
    idx, lines = ARTICLES[slug]
    canvas = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))

    art = Image.open(art_path).convert("RGBA")
    scale = max(W * S / art.width, H * S / art.height)
    art = art.resize((int(art.width * scale) + 1, int(art.height * scale) + 1), Image.LANCZOS)
    left = (art.width - W * S) // 2
    top = (art.height - H * S) // 2
    canvas.paste(art, (-left, -top))

    # 左侧渐变遮罩：前 30% 几乎不透明，到 72% 处淡出
    scrim = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    stop = int(W * S * 0.72)
    flat = int(stop * 0.30)
    for x in range(stop):
        if x < flat:
            a = 250
        else:
            t = (x - flat) / (stop - flat - 1)
            a = int(250 * (1 - t) ** 1.4)
        sd.line([(x, 0), (x, H * S)], fill=(9, 14, 26, a))
    canvas = Image.alpha_composite(canvas, scrim)

    d = ImageDraw.Draw(canvas)
    d.rectangle([96 * S, 296 * S, 104 * S, 476 * S], fill=ACCENT)
    kicker, ov = meta(slug)
    d.text((132 * S, 250 * S), kicker, font=font(26), fill=KICKER)

    # 标题按可用宽度自适应，最多 620px
    max_w = 620
    size = 62
    while size > 40 and d.textlength(lines[0], font=font(size)) > max_w:
        size -= 2
    d.text((132 * S, 300 * S), lines[0], font=font(size), fill="#ffffff")

    # 副标题按 15 字换行
    sub = lines[1]
    chunks = [sub[i:i + 15] for i in range(0, len(sub), 15)]
    for i, c in enumerate(chunks):
        d.text((132 * S, (398 + i * 42) * S), c, font=font(30, 0), fill=BODY)
    d.text((132 * S, 856 * S),
           ov.get("footer_bleed") or "earendil-works/pi  ·  HEAD 395f3e0", font=font(22, 0), fill="#9aa8bd")

    out = canvas.resize((W, H), Image.LANCZOS).convert("RGB")
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{slug}.jpg")
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "..", slug, "cover.jpg")
        os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path, quality=88, optimize=True, progressive=True)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--art", default=ART)
    ap.add_argument("--out")
    ap.add_argument("--variant", default="card", choices=["card", "bleed"])
    a = ap.parse_args()
    slugs = [a.slug] if a.slug else list(ARTICLES)
    fn = make_bleed if a.variant == "bleed" else make
    for s in slugs:
        if s not in ARTICLES:
            sys.exit(f"unknown slug: {s}")
        print("saved", fn(s, a.art, a.out))
