# 第三方材料与许可说明（THIRD_PARTY_NOTICES）

本仓库包含多类来源不同的内容，许可状态**分别**记录如下；任何单一仓库级许可声明都不覆盖以下全部内容。

## 1. 论文原文（demo/papers/）

| 文件 | 来源 | 许可状态 |
|---|---|---|
| `transformer.pdf` | arXiv:1706.03762（Vaswani et al., 2017） | arXiv 非独占许可下作者自存档版本；版权归原作者/出版方 |
| `resnet.pdf` | arXiv:1512.03385（He et al., 2015） | 同上 |
| `deepseek-r1.pdf` | arXiv:2501.12948（DeepSeek-AI, 2025） | 同上 |

说明：三者均为 arXiv 公开自存档 PDF，用于演示流水线的输入。论文译文
（`demo/*/​*_中文.md`，及由其生成的 `docs/samples/*/translation.md`）是本仓库对上述
论文的翻译演绎，仅用于展示翻译流水线效果；论文本身的著作权（含插图 `demo/*/images/`
与 `docs/samples/*/images/` 中由解析器提取的图片）属于原作者与出版方，本仓库不对其
主张任何权利。商业性再利用请自行核对各论文的原始许可。

## 2. 第三方代码与字体

| 组件 | 版本 | 来源 | 许可 |
|---|---|---|---|
| KaTeX（`docs/vendor/katex/`） | 0.16.11 | https://github.com/KaTeX/KaTeX | MIT（字体另见下方字体条目） |
| KaTeX 字体（`docs/vendor/katex/fonts/*.woff2`） | 0.16.11 | 同上 | SIL Open Font License 1.1 |
| GSAP（`docs/vendor/gsap.min.js`） | 3.12.5 | https://gsap.com | GSAP 标准许可（"Standard No Charge" license，文件头含许可与版权声明，允许免费用于直接面向最终用户的产品/页面，不得单独再分发源文件） |
| Markdown（`scripts/_site_libs/markdown/`） | 3.11 | https://python-markdown.github.io/ | BSD 3-Clause（源头文件含版权声明） |
| KaTeX auto-render 插件 | 0.16.11 | 同 KaTeX | MIT |

以上均为按原样引入的公开发行物，未修改功能代码。

## 3. 本仓库原创内容

- 流水线脚本（`scripts/`，除上述 vendored 副本外）、`docs/` 页面代码、动画代码、
  `demo/*/` 下的译文、审计/校验报告与表格任务 JSON：由本项目生成。
- **许可状态：待定**。仓库当前没有 LICENSE 文件，本说明不代项目所有者选择或声明
  任何许可证；发布前请由所有者决定并添加（例如 MIT/Apache-2.0 等），或在私有范围内使用。

## 4. 参考的学习材料（未引入其代码/文案）

制作本站动画时参考了两个 MIT 许可的开源仓库的实现思路（GSAP 单一时间轴、`?t=` seek
调试、固定舞台缩放等通用技术），未复制其代码、文案或品牌元素：

- iart-ai/web-animation-skills（MIT）
- zarazhangrui/frontend-slides（MIT）
