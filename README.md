# Hexo 博客搭建指南（安知鱼主题）

## 简介

本项目基于 [Hexo](https://hexo.io/zh-cn/) 博客框架，使用 [安知鱼主题](https://github.com/anzhiyu-c/hexo-theme-anzhiyu)。  
安知鱼主题是一款美观、功能丰富、支持高度自定义的 Hexo 主题，适合个人博客、相册、技术分享等多种场景。

## 快速开始

### 1. 安装依赖

请确保已安装 [Node.js](https://nodejs.org/zh-cn/) 和 [Git](https://git-scm.com/)。

```bash
npm install
```

### 2. 安装安知鱼主题

在博客根目录下执行：

```bash
git clone -b main https://github.com/anzhiyu-c/hexo-theme-anzhiyu.git themes/anzhiyu
```

### 3. 配置主题

编辑博客根目录下的 `_config.yml`，将主题设置为 anzhiyu：

```yaml
theme: anzhiyu
```

> 如果你没有安装 pug 和 stylus 渲染器，请执行：
> 
> ```bash
> npm install hexo-renderer-pug hexo-renderer-stylus --save
> ```

#### 推荐：使用主题覆盖配置

将 `themes/anzhiyu/_config.yml` 复制到博客根目录并重命名为 `_config.anzhiyu.yml`，以后只需修改该文件即可自定义主题配置，避免主题升级时丢失自定义内容。

### 4. 常用命令

- 启动本地预览：`npm run server`
- 生成静态文件：`npm run build`
- 清理缓存：`npm run clean`
- 部署到远程：`npm run deploy`

### 5. 文章与页面

- 文章存放于 `source/_posts/`
- 新建文章：`hexo new "文章标题"`
- 新建页面：`hexo new page "页面名"`


## 主题特色

- 页面与图片懒加载
- 多种代码高亮
- 多语言支持
- 多种评论系统
- 支持暗色模式
- 丰富的自定义标签与组件
- 支持 PWA、AI 摘要、音乐球、LaTeX、mermaid 流程图等

更多功能与详细配置请参考[官方文档](https://docs.anheyu.com/)。

## 参考链接

- Hexo 官方文档：https://hexo.io/zh-cn/docs/
- 安知鱼主题文档：https://docs.anheyu.com/
- 主题仓库：https://github.com/anzhiyu-c/hexo-theme-anzhiyu
