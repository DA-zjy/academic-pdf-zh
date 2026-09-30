# 发布验收报告（RELEASE_REPORT）

生成时间：2026-09-29。本报告由实际执行的检查汇总而成，明确区分 **自动检查 / 人工目视 / 未执行项目**。

## 交付物

- `academic-pdf-zh-release/` —— 可直接作为 GitHub 仓库根目录的项目文件夹（154 个文件，12.42 MB）
- `academic-pdf-zh-release.zip` —— 上述文件夹的压缩包（压缩包内仅一层项目文件夹）
- 本轮未创建远程仓库、未推送、未修改任何 GitHub 设置（按指令要求）

## 一、自动检查（脚本执行，全部通过）

`python scripts/check_site.py`（在开发目录与 `academic-pdf-zh-release/` 内分别运行，均通过）：

| 检查项 | 结果 |
|---|---|
| 内部 href/src 全部可解析（75 处引用 / 9 个 HTML） | ✅ |
| 无根绝对路径 `/assets/...`（子路径部署安全） | ✅ |
| 无 `../demo/`、本机盘符、localhost 引用 | ✅ |
| 全部 HTML 为严格 UTF-8，含 `<meta charset="utf-8">` 与 `lang="zh-CN"` | ✅ |
| 无占位符残留（数学占位符 `\u0001` 为零） | ✅ |
| 阅读页目录锚点与标题 id 一一对应（12/8/7，零悬空） | ✅ |
| **标题序列与源 Markdown 完全一致**（transformer 14 / resnet 8 / deepseek-r1 7，防吞并/截断） | ✅ |
| **图片引用集合与源 Markdown 一致**（3/2/2，全部存在） | ✅ |
| `translation.md` 与 `demo/` 源文件 sha256 一致（918dfdc2… / dcb1bd58… / f1e48fc1…） | ✅ |
| `sample.zip` 内含 Markdown 与其引用的全部图片（相对关系有效） | ✅ |
| `validation.html` 保留原始 STATUS 与全部指标（未改写） | ✅ |
| `.nojekyll`、vendored KaTeX（js/css/20 字体/auto-render）、reader.css 存在 | ✅ |

构建输入核对：

- `scripts/build_site.py` 只读 `site.config.json`、`demo/<key>/<key>_中文.md`、`validation.md`、`images/`，
  **不依赖** `demo/.build/.../manifest.json`（该文件缺失不影响阅读页构建）。
- `scripts/build_demo_data.py`（动画数据）在 manifest 缺失时**显式报错**并提示处理方式，不伪造数据。
- Markdown 解析使用仓库内置 `scripts/_site_libs/`（Markdown 3.11 纯 Python 源码副本，BSD-3-Clause，
  版本与 `requirements-site.txt` 一致），离线可构建；KaTeX 0.16.11 + auto-render 为既有 vendored 资源。

## 二、人工目视（浏览器实测，通过）

以 `academic-pdf-zh-release/docs/` 为站点根（http://127.0.0.1:8460/）：

| 项 | 结果 |
|---|---|
| 主页首屏、样章卡片（9 个站内链接：站内阅读/校验报告/下载资源包） | ✅ |
| 三篇阅读页：纸张排版、KaTeX 渲染（transformer 66 条公式 / 0 错误，与 validation 的 66/66 对应）、图片、图注、`<details>` 图内文字、`&lt;think&gt;` 字面标签 | ✅ |
| Transformer 阅读页开头 / 中部（公式 1、FFN 式 2、完整 Table 1 五行）/ 结尾（样章说明）逐段目检 | ✅ |
| 锚点直达 + 刷新定位；目录跳转；「返回主页」指向站点根（`../../index.html`） | ✅ |
| 校验报告页：顶部「报告展示（非重新执行校验）」横幅 + 原始指标 | ✅ |
| 移动端 390×844：无横向滚动、正文 17px、窄屏目录默认折叠可展开 | ✅ |
| 动画回归（release 副本）：播放推进（强制帧下 0→4.7s 连续）、seek(21) 精确、暂停保持、重播、结尾重播按钮 | ✅ |
| 各页控制台错误 | ✅ 零错误（KaTeX errorCallback 监控亦为零） |

子路径部署模拟（http://127.0.0.1:8461/academic-pdf-zh/，Pages 实际形态）：

- 首页 / 阅读页 / CSS / 图片 / sample.zip / `.nojekyll` 全部 200，样式与公式渲染正常 ✅
  （注：该模拟目录在报告生成后已清理；随时可用「复制 docs/ 到任意子目录」复测）

## 三、本轮修复清单（相对输入包）

1. **三个站内阅读页 + 报告页 + 下载包**（原为直接打开 ../demo/*.md，且仅发布 docs/ 时为死链）。
2. **无效命令修正**：`validate_markdown.py` → `validate_translation.py`；删除不存在的 `--out` 参数；
   组装/校验命令改为与 argparse 一致的真实形式（`assemble_markdown.py WORK/chunks/manifest.json`、
   `validate_translation.py --manifest … --source … --translated … --report …`）。
3. **阶段口径统一**：SKILL.md 为 Phase A–I 九个阶段，README「八个阶段/8_phases 徽章/目录树注释」
   已改为九个阶段（A–I）；「八项终检」属实（Phase I 列出 8 类 material FAIL）予以保留。
4. **渲染层修复（不改源译文）**：构建时为「表格块后缺空行」补空行——否则 python-markdown 会把
   后续整节吞进表格（transformer/deepseek 各 1 处）；`<think>` 模板字面标签转义显示；
   YAML front matter 不进正文。源 Markdown 未改动一字。
5. **动画健壮性**：就绪门控的 rAF 等待加 900ms 兜底——修复在后台/被遮挡标签页中
   `window.demo` 永远不就绪的问题。
6. **主页/文档链接**：样章卡片全部改为站内相对路径；`build_demo_data.py` 链接生成同步改为站内路径，
   今后重新生成不会再产出 `../demo/` 链接；README 演示入口改为「docs/（发布后为 Pages 首页）」，
   用户名未定期间不放任何指向 github.com 首页或虚构地址的按钮。
7. **发布卫生**：`.gitignore`（排除 `demo/.build/`、zip、虚拟环境等）；THIRD_PARTY_NOTICES.md
   分项记录论文 PDF/译文/插图/代码/字体的来源与许可；README 徽章与「3/3 PASS」表述
   均限定为样章级结果。

## 四、体积与上传建议

- 共 **154 个文件 / 12.42 MB**；最大单文件 `demo/papers/deepseek-r1.pdf` 4.8 MB（远低于 GitHub 单文件 100MB 限制）。
- 分布：demo/ 8.0 MB（含三个原 PDF 7.9 MB）、docs/ 3.98 MB、其余 < 0.5 MB。
- GitHub 网页上传一次最多 100 个文件，建议分 **6 批**：
  ① 根目录散文件（README/SKILL/DEPLOY/REPORT/NOTICES/config/requirements/.gitignore ≈ 8 个）；
  ② `docs/` 根文件 + assets/ + screenshots/（约 20 个）；
  ③ `docs/vendor/` + `docs/samples/`（约 40 个）；
  ④ `scripts/` + `tests/` + `references/` + `agents/` + `assets/`（约 30 个）；
  ⑤ `demo/transformer/` + `demo/resnet/`（约 30 个）；
  ⑥ `demo/deepseek-r1/` + `demo/papers/`（约 20 个，含 3 个 PDF）。
  或使用 Git 命令行一次性推送（如本地可用）。

## 五、部署记录（2026-09-30 更新）

- 仓库：`DA-zjy/academic-pdf-zh`（public），提交署名 DA-zjy <jinyuan-23@mails.tsinghua.edu.cn>
- Pages：main 分支 `/docs`，Deploy from a branch；上线地址 **https://da-zjy.github.io/academic-pdf-zh/**
- 首次上线验证：首页/播放器/三篇阅读页/三份报告页/图片/字体/`.nojekyll` 全部 200
- 上线后修正：`.gitignore` 由 `*.zip` 改为根目录锚定 `/*.zip`，使 `docs/samples/*/sample.zip`
  进入版本库（首次提交被 ignore 排除导致线上 404），随后补提交并确认线上 200
- README 演示入口与 `site.config.json` 的 `github.owner` 已回填真实地址/用户名

## 六、未执行项目与剩余事项

1. **语义质量**：自动检查与目视覆盖结构/渲染层；翻译语义正确性未做逐句审校（不在本轮范围）。
2. **LICENSE 缺失**：仓库无 LICENSE 文件，本轮不代为选择许可证（THIRD_PARTY_NOTICES.md 已注明待定）。
3. **语义质量**：自动检查与目视覆盖结构/渲染层；翻译语义正确性未做逐句审校（不在本轮范围）。
4. **reduced-motion**：阅读页无动画不涉及；动画主页的 prefers-reduced-motion 代码路径沿用上一轮实现，
   本轮未在模拟环境下重复验证（测试环境无法模拟 matchMedia）。
5. **demo/.build/ 构建中间物未打包进发布版**（.gitignore 排除）：动画数据 demo-data.js 已是预生成文件；
   若需重建动画数据，需先按 SKILL.md 流程重建 manifest（build_demo_data.py 缺输入时会显式报错）。
6. **视频录制**：沿上一轮结论——应用内录屏接口在本环境只能产出亚秒级空片段，未提供自动录制视频；
   录制方法见 DEPLOY.md / 主页「录制视图」。
