# 项目存储规则

- 项目根目录固定为 `D:\Projects\xh_photos_online`，所有命令从此目录或其子目录执行。
- 所有项目文件必须保存在 D 盘，严禁将源码、素材、文档、下载文件、依赖、构建产物、缓存或临时文件保存在 C 盘。
- 使用生成缓存或临时文件的工具前，将其临时目录和缓存目录显式配置到本项目的 `.tmp` 和 `.cache`；包括按需设置进程环境变量 `TEMP`、`TMP` 和相应工具的缓存配置。
- 不要在原 C 盘工作区创建项目文件；工具默认工作区指向 C 盘时，必须显式指定本项目 D 盘路径。

# 目录用途

- `src/`：源码。
- `site/`：GitHub Pages 发布目录；实际网站入口为 `site/index.html`。
- `cloudflare-site/`：Cloudflare Pages 发布目录，由 `scripts/build_cloudflare.py` 从 `site/` 生成，资源及站内导航使用域名根路径。
- `assets/`：图片等项目素材。
- `docs/`：项目文档。
- `output/`：生成结果及交付文件。
- `.cache/`：工具缓存。
- `.tmp/`：临时文件。
