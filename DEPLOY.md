# 部署说明（GitHub Pages，Deploy from a branch）

本项目的网站是**纯静态预生成目录**：网站的全部内容都在 `docs/` 里（主页、动画播放器、
三篇样章阅读页、校验报告页、下载包、vendored KaTeX/GSAP）。GitHub Pages 只负责托管，
不需要任何构建任务、Jekyll 配置或自定义域名。

## 一、先分清两件事

| 你想做什么 | 用哪份内容 | 说明 |
|---|---|---|
| **直接预览已构建好的网站** | `docs/` | 网页已经生成完毕，改它就是改网站 |
| **修改译文/样章后重新生成网站** | `demo/`（源）+ `scripts/build_site.py` | 只上传 demo/ 不会自动更新 `docs/samples/` 下的预生成阅读页，必须重跑构建 |

重新构建（在仓库根目录）：

```bash
python scripts/build_site.py     # 从 demo/ 真实译文重新生成 docs/samples/（只覆盖生成产物，不动动画与手写文件）
python scripts/check_site.py     # 内部路径/编码/锚点/下载包一致性检查
```

依赖说明：构建使用仓库内置的 `scripts/_site_libs/`（Markdown 3.11 纯 Python 源码副本），
无网络也可运行；如需独立环境，见 `requirements-site.txt`。
注意：`scripts/build_demo_data.py`（动画数据）依赖 `demo/.build/.../manifest.json`，
缺失时会**显式报错**；阅读页构建不依赖它。

## 二、本地预览

Windows（PowerShell，在仓库根目录）：

```powershell
python -m http.server 8000
# 浏览器打开 http://127.0.0.1:8000/docs/
```

macOS / Linux：

```bash
python3 -m http.server 8000
# 浏览器打开 http://127.0.0.1:8000/docs/
```

> 上线验收时应以 `docs/` 本身为站点根测试：`cd docs && python -m http.server 8000`。

## 三、GitHub 网页上传与发布步骤（手动）

1. **创建仓库**：github.com → 右上角 `+` → New repository → 名称填 `academic-pdf-zh`
   → Public → **不要**勾选自动生成 README（本地已有）→ Create。
2. **上传内容**：仓库页 `Add file → Upload files`，把**本地仓库根目录的内容**
   （README.md、SKILL.md、docs/、demo/、scripts/ 等）拖进去。注意：
   - 浏览器上传一次最多 100 个文件，建议分批：先传根目录文件，再按 `docs/`、`demo/`、
     `scripts/`、`references/`、`assets/`、`agents/`、`tests/` 逐目录上传；
   - 单文件上限 100MB，本仓库远低于此（见 RELEASE_REPORT.md 的体积统计）；
   - `docs/.nojekyll` 必须在列表里（GitHub 网页上传不会把点开头文件改名，上传后点开
     该文件确认名字仍是 `.nojekyll`，没有变成 `.nojekyll.txt`）。
3. **开启 Pages**：仓库 Settings → Pages → Build and deployment → Source 选
   **Deploy from a branch** → Branch 选所在分支（默认 main）、目录选 **/docs** → Save。
4. **访问地址**：发布后为 `https://<用户名>.github.io/academic-pdf-zh/`
   —— **包含仓库名，不含 /docs/**（`/docs` 是源目录，不是 URL 前缀）。
5. **发布后需要替换的地址**（发布前这些位置均为相对链接，不影响本地）：
   - `README.md` 顶部的「演示与样章阅读站」链接 → 改为上面的 Pages 地址；
   - 如需加 GitHub 仓库角标/按钮：`site.config.json` 的 `github.owner` 填入真实用户名，
     重新生成或手改相应链接（当前为空，站内无仓库按钮，不留死链）。
6. **验证**：发布 1–2 分钟后打开 Pages 地址，检查首页 → 三个样章阅读页 → 校验报告 →
   下载包都能打开；首次部署或大改动可等几分钟并强刷（Ctrl/Cmd+Shift+R）。

### 只发布 docs/ 可以吗？

可以，但不推荐：Pages 只需要 `docs/`，可单独建一个仓库只上传 `docs/` 内容（此时
`docs/` 下的相对链接全部仍然成立，因为站点是自包含的）。缺点是 README、SKILL、
scripts、demo 证据链不在同一仓库，审阅者看不到数据来源。

## 四、常见问题定位

| 现象 | 先查什么 |
|---|---|
| 页面 404 | URL 是否带 `/docs/`（不该带）；文件是否真的上传到对应目录；大小写是否一致（GitHub 区分大小写） |
| 样式全丢、只有裸文本 | `docs/.nojekyll` 是否存在且名字正确；F12 Network 看 `reader.css`/`vendor/katex/katex.min.css` 是否 404 |
| 公式显示为红色原文 | 打开控制台看 `KaTeX 无法渲染` 警告（保留原文并记录，属预期降级）；多数是复制改动破坏了 `$...$` 配对 |
| 图片 404 | 阅读页图片在 `docs/samples/<key>/images/`；确认上传时目录结构没被压平 |
| 动画不动 | 播放需等待字体/公式/图片就绪（约 1 秒）；`?t=秒` 可直接定位验证 |
| 改了 demo/ 译文但网页没变 | 预生成页面不会自动更新，重跑 `python scripts/build_site.py` 后再上传 docs/ |

## 五、不要做的事

- 不要为发布修改 GitHub Actions / 添加 Jekyll 配置 / CNAME（本轮约定：分支 + /docs 即可）；
- 不要把 `demo/.build/`（构建中间物）上传到仓库——`.gitignore` 已排除；
- 不要替他人重新分发论文 PDF 前忽略 THIRD_PARTY_NOTICES.md 中的来源与许可说明。
