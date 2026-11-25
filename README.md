# Portfolio-xh-2026

XH 摄影作品集，使用 GitHub Pages 部署。

## 网站

[查看作品集](https://xznzz1.github.io/Portfolio-xh-2026/)

[Cloudflare Pages 地址](https://portfolio-xh-2026.pages.dev/)

本仓库保存 [Framer 已发布作品集](https://successful-sandwich-977344.framer.app/) 的静态副本，包括首页、9 个作品详情页，以及页面所需的图片、字体、脚本和 CMS 索引。导航、资源路径和作品路由已适配 GitHub Pages 项目路径。

## 网站目录

将可部署的静态网页及图片、字体、脚本放在 `site/` 中，入口为 `site/index.html`。

GitHub Pages 的项目路径为 `/Portfolio-xh-2026/`。站内链接和资源路径需要支持这个路径，推荐使用相对路径。

## 部署

推送 `main` 分支中 `site/` 或部署工作流的更改时，GitHub Actions 会检查网站入口。入口存在且不为空时才发布 `site/`，否则跳过部署。也可在 Actions 中手动运行 **Deploy portfolio to GitHub Pages**。

部署使用 [GitHub 官方 Pages Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

### Cloudflare Pages

`wrangler.jsonc` 将 Cloudflare Pages 的发布目录设为 `cloudflare-site/`，其首页为 `cloudflare-site/index.html`。此目录使用域名根路径；`site/` 则使用 GitHub Pages 的项目路径。

Cloudflare 设置：框架预设 **None**，生产分支 `main`，根目录为仓库根目录，构建命令 `exit 0`，构建输出目录 `cloudflare-site`。仓库已包含生成的发布文件，无需在云端下载原 Framer 站点。

如需从当前 `site/` 重新生成 Cloudflare 版本，运行 `python scripts/build_cloudflare.py`。[Cloudflare 静态站点部署说明](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/)。

## 从 Framer 更新

在 Framer 发布更改后，从本项目目录运行：

```powershell
$env:TEMP = 'D:\Projects\xh_photos_online\.tmp'
$env:TMP = $env:TEMP
python scripts/export_framer.py
git add site cloudflare-site docs/export-manifest.json
git commit -m "Update portfolio from Framer"
git push
```

`scripts/export_framer.py` 使用 Python 标准库下载已发布页面与静态资源，更新站内路径和 CMS 索引地址。资源下载缓存位于 `.cache/framer-source/`，导出清单位于 `docs/export-manifest.json`。

导出完成后会自动生成 `cloudflare-site/`。推送后，GitHub Pages 和已连接此仓库的 Cloudflare Pages 分别发布各自的目录。

GitHub 上的版本是发布时的副本。Framer 编辑器中的后续修改需要重新导出和推送后才会同步。Framer 的在线编辑和统计服务属于原托管平台，导出副本不连接这些服务。

## 本地存储

本地项目根目录：`D:\Projects\xh_photos_online`。源码、素材、文档、输出、依赖、缓存及临时文件均保存在 D 盘，具体约束见 `AGENTS.md`。
