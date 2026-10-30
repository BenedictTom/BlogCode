# 配图源文件（Excalidraw）

这里存放**可编辑的图源**，渲染出的 PNG 放在上一级 `source/images/`，两边同名配对。

## 命名与配对

```
source/images/src/hexo-flow.excalidraw   ← 源文件，入库
source/images/hexo-flow.png              ← 渲染产物，正文引用它
```

- 用 kebab-case，语义化命名（`k8s-scheduler-flow`、`redis-hash-struct`），不要用 `图1`、`diagram`。
- 一篇文章多张图时加序号前缀：`a2a-01-topology`、`a2a-02-handshake`。
- 正文引用写绝对路径：`![说明](/images/hexo-flow.png)`（`post_asset_folder` 为 false，只能这样写）。

## 渲染命令

项目内已装好独立的渲染环境，直接跑：

```bash
cd /Users/smzdm/chw/BlogCode/.claude/skills/excalidraw-diagram/references

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/python render_excalidraw.py \
  /Users/smzdm/chw/BlogCode/source/images/src/hexo-flow.excalidraw \
  --output /Users/smzdm/chw/BlogCode/source/images/hexo-flow.png \
  --scale 2
```

`--scale 2` 出 2 倍图，Retina 屏不糊。单张约 12–14 秒。

**已知约束**：

- `UV_CACHE_DIR` 必须指到可写目录（沙箱下 `~/.cache/uv` 不可写），只在需要 `uv sync` 重建环境时才要带。
- 渲染时需联网：模板从 `esm.sh` 拉 `@excalidraw/excalidraw@0.18.0`。断网会白屏。
- `.venv/`（约 148 MB）已被 skill 自带的 `.gitignore` 排除，不会入库。

## 什么时候放这里，什么时候用 mermaid

| 图的类型 | 用什么 | 放哪 |
|---|---|---|
| 时序图、流程图、类图、ER 图、状态机 | mermaid | 直接写进 md 代码块，不进本目录 |
| 架构图、机制拆解、对比图、概念隐喻 | Excalidraw | 源文件进本目录，PNG 进 `source/images/` |

判据：**能被一段文字描述结构、且经常改动的流程图用 mermaid**（可搜索、零体积、改一行就变）；
**要一眼看懂结构关系、或要视觉冲击力的门面图用 Excalidraw**（不可搜索、改图要重跑渲染）。

默认一篇长文：2–3 张 mermaid + 1 张 Excalidraw 门面图。

## 出图纪律

Excalidraw 不会一次成型。渲染完必须自己看一眼（读 PNG），检查标签是否压箭头、文字是否溢出盒子、
留白是否失衡，然后改 JSON 坐标重渲染，直到干净为止。这一张 `hexo-flow` 就改了 3 轮。
