# 🧪 端到端真实演示 — 三篇经典论文

这三个演示不是摆拍：每篇论文都走完了 `academic-pdf-zh` 的**完整八阶段流水线**，所有产物（审计报告、冻结 token、分块、表格任务、终检报告）均由 `scripts/` 下的真实脚本生成，翻译由 Codex 逐块完成。

| 论文 | 样章 | 流水线亮点 | 终检 |
|---|---|---|---|
| [ResNet (2015)](https://arxiv.org/abs/1512.03385) | [resnet_中文.md](resnet/resnet_中文.md) | 残差公式 `y = F(x, {Wᵢ}) + x` 全程以 LaTeX 冻结还原；51 个块、191 个不可变 token | ✅ **PASS** |
| [Transformer (2017)](https://arxiv.org/abs/1706.03762) | [transformer_中文.md](transformer/transformer_中文.md) | Table 1（复杂度对比表）20 个单元格逐格任务化；注意力公式逐字校对 | ✅ **PASS** |
| [DeepSeek-R1 (2025)](https://arxiv.org/abs/2501.12948) | [deepseek-r1_中文.md](deepseek-r1/deepseek-r1_中文.md) | GRPO 目标函数；"aha moment" 表格中 15 个数字被 `[[TCP_*]]` token 保护，防 2.47 → 72.47 式篡改 | ✅ **PASS** |

> 表中 PASS 指各样章自身 `validation.md` 的结构终检结果（样章级）；数量一致 ≠ 语义无误。

## 每个文件夹里有什么

```text
demo/transformer/
├── transformer_中文.md        ← 最终成品：Obsidian 就绪的中文精读版
├── images/                    ← 与 Markdown 同行的图片资产
├── source-audit.md            ← 阶段 C 产物：解析审计（含公式/表格截图清单）
├── validation.md              ← 阶段 I 产物：终检报告（PASS / FAIL 的证据）
├── chunks/
│   ├── 0003.source.md         ← 分块源文：可见 [[IMM_*]] 冻结 token 与块标记
│   └── 0003.translated.md     ← 对应译文：token 原样保留、语义位置一致
└── table_tasks.T0001.json     ← 阶段 G 产物：逐格翻译任务（template + protected 数字）
```

## 这个 demo 真实证明了什么

1. **公式逐字保留** —— ResNet 的式 (1)(2)、Transformer 的缩放点积/多头/FFN/位置编码四组公式、DeepSeek 的 GRPO 目标函数，在成品 Markdown 中均为可渲染 LaTeX，与 PDF 原文逐字核对过。
2. **数字原样还原** —— 所有 `3.57%`、`8×`、`28.4 BLEU`、学习率 `3e-6`、`32,768` 等数字在翻译前被冻结为不可变 token，组装时按清单原样还原。
3. **表格逐格重建** —— 表格不进入自由翻译，而是拆成逐格 JSON 任务；`[[TCP_*]]` 保护数值，行数与数字清单由终检比对。
4. **结构可验证** —— 每个 `<!-- block:Bxxxxxx -->` 标记必须在译文中按序出现，少一个、乱一个，组装直接报错。

## 复现方式

```bash
# 以 Transformer 为例（页 1–6 样章）
python scripts/prepare_paper.py demo/papers/transformer.pdf \
    --project-root demo --work-dir demo/.build/transformer \
    --pages 1-6 --parser pymupdf4llm
# 之后按 SKILL.md 的 Phase D–I 继续（翻译由 Codex 完成）
```

> 样章均标注了抽取页码区间；对整篇论文运行同一命令（去掉 `--pages`）即为完整翻译。
