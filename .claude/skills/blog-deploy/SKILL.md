---
name: blog-deploy
description: 一键完成 Hexo 博客发布流程：创建新文章 → 提醒添加图片 → 清理并部署到 GitHub。当用户想要写博客、发布文章、部署博客时都要使用此技能。
---

# Hexo 博客发布流程

帮助你快速完成博客发布的固定流程。

## 使用方法

**语法：** `/blog-deploy <文章标题>`

**示例：**
```
/blog-deploy 今天的学习笔记
/blog-deploy Spring Boot 实战教程
```

## 流程说明

当用户调用此 skill 并传入文章标题时，按以下步骤执行：

### 步骤 1: 创建新文章

执行命令创建新文章：
```bash
hexo new post "<文章标题>"
```

告知用户文章已创建，路径为 `source/_posts/<文章标题>.md`

### 步骤 2: 提醒添加图片

提醒用户：
- 从网上找合适的图片并添加到文章中
- 完善文章内容和格式
- 可以添加 tags、categories 等 front-matter 信息

### 步骤 3: 等待用户编辑

询问用户是否已完成文章编辑。**必须得到用户确认后才能继续下一步**。

### 步骤 4: 清理并部署

用户确认完成后，执行：
```bash
hexo clean && hexo deploy
```

### 步骤 5: 完成

告知用户部署已完成，博客已推送到 GitHub Pages。

## 注意事项

- 确保在博客项目根目录下执行
- 确保已配置好 GitHub SSH key
- 确保已在 `_config.yml` 中配置好 deploy 信息
- 部署前会先询问用户是否已完成文章编辑
