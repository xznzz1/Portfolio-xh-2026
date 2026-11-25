# Portfolio-xh-2026

XH 摄影作品集，使用 GitHub Pages 部署。

## 当前状态

仓库和自动部署配置已准备。作品集的页面及素材尚未导入，网站尚未上线。

原 Framer 编辑器项目需要登录，当前无法直接获取页面内容：

[Outdoor Photographer — Template (copy)](https://framer.com/projects/Outdoor-Photographer-Template-copy--oh9uG2xqocOzAXBWjHkZ-71Opk)

## 网站目录

将可部署的静态网页及图片、字体、脚本放在 `site/` 中，入口为 `site/index.html`。

GitHub Pages 的项目路径为 `/Portfolio-xh-2026/`。站内链接和资源路径需要支持这个路径，推荐使用相对路径。

## 部署

推送 `main` 分支中 `site/` 或部署工作流的更改时，GitHub Actions 会检查网站入口。入口存在且不为空时才发布 `site/`，否则跳过部署。也可在 Actions 中手动运行 **Deploy portfolio to GitHub Pages**。

预留访问地址（尚未部署）：https://xznzz1.github.io/Portfolio-xh-2026/

部署使用 [GitHub 官方 Pages Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 本地存储

本地项目根目录：`D:\Projects\xh_photos_online`。源码、素材、文档、输出、依赖、缓存及临时文件均保存在 D 盘，具体约束见 `AGENTS.md`。
