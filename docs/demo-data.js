/* 生成文件：由 scripts/build_demo_data.py 生成，勿手改。 */
window.DEMO_DATA = {
  "_meta": {
    "generatedAt": "2026-09-29T14:41Z",
    "note": "由 scripts/build_demo_data.py 生成；全部内容取自 demo/ 下的真实产物（表格任务 JSON、chunk 源/译文、manifest 公式、validation 报告）。请勿手工编辑。",
    "sources": {
      "table": "demo/transformer/table_tasks.T0001.json",
      "prose": "demo/transformer/chunks/0003.source.md + 0003.translated.md (B000061-B000065)",
      "formulas": "demo/.build/transformer/chunks/manifest.json (I000001, I000004)",
      "metrics": [
        "demo/transformer/validation.md",
        "demo/resnet/validation.md",
        "demo/deepseek-r1/validation.md"
      ],
      "figure": "demo/transformer/images/_pages_subset.pdf-0003-00.png -> docs/assets/figure-1.png"
    }
  },
  "brand": {
    "name": "academic-pdf-zh"
  },
  "prose": {
    "heading": {
      "en": "3.5 Positional Encoding",
      "cn": "3.5 位置编码"
    },
    "para1": {
      "en": "Since our model contains no recurrence and no convolution, in order for the model to make use of the order of the sequence, we must inject some information about the relative or absolute position of the tokens in the sequence. To this end, we add \"positional encodings\" to the input embeddings at the bottoms of the encoder and decoder stacks. The positional encodings have the same dimension <span class='im'>d_{\\text{model}}</span> as the embeddings, so that the two can be summed. There are many choices of positional encodings, learned and fixed [9].",
      "cn": "由于我们的模型不含循环也不含卷积，为了让模型能够利用序列的顺序信息，我们必须向序列中注入一些关于词元相对或绝对位置的信息。为此，我们在编码器与解码器堆栈底部的输入嵌入中加入\"位置编码\"（positional encodings）。位置编码与嵌入具有相同的维度 <span class='im'>d_{\\text{model}}</span>，因此二者可以相加。位置编码有多种选择，既可学习也可固定 [9]。"
    },
    "line": {
      "en": "In this work, we use sine and cosine functions of different frequencies:",
      "cn": "在本工作中，我们使用不同频率的正弦与余弦函数："
    },
    "formulaToken": "PE",
    "para2": {
      "en": "where <span class='im'>pos</span> is the position and <span class='im'>i</span> is the dimension. That is, each dimension of the positional encoding corresponds to a sinusoid. The wavelengths form a geometric progression from <span class='im'>2\\pi</span> to <span class='im'>10000 \\cdot 2\\pi</span>. We chose this function because we hypothesized it would allow the model to easily learn to attend by relative positions, since for any fixed offset <span class='im'>k</span>, <span class='im'>PE_{pos+k}</span> can be represented as a linear function of <span class='im'>PE_{pos}</span>.",
      "cn": "其中 <span class='im'>pos</span> 是位置，<span class='im'>i</span> 是维度。也就是说，位置编码的每个维度都对应于一条正弦曲线。这些波长构成一个从 <span class='im'>2\\pi</span> 到 <span class='im'>10000 \\cdot 2\\pi</span> 的几何级数。我们之所以选择这一函数，是因为我们假设它能让模型更容易地学会按相对位置进行关注，因为对任意固定偏移量 <span class='im'>k</span>，<span class='im'>PE_{pos+k}</span> 都可以表示为 <span class='im'>PE_{pos}</span> 的线性函数。"
    }
  },
  "formulas": {
    "attention": "\\mathrm{Attention}(Q, K, V) = \\mathrm{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V \\tag{1}",
    "pe": "\\begin{aligned}PE_{(pos,2i)} = \\sin(pos/10000^{2i/d_{\\text{model}}}) \\\\ PE_{(pos,2i+1)} = \\cos(pos/10000^{2i/d_{\\text{model}}})\\end{aligned}"
  },
  "table": {
    "id": "T0001",
    "headers": [
      {
        "src": "Layer Type",
        "dst": "层类型",
        "changed": true,
        "protectedIds": []
      },
      {
        "src": "Complexity per Layer",
        "dst": "每层复杂度",
        "changed": true,
        "protectedIds": []
      },
      {
        "src": "Sequential<br>Operations",
        "dst": "串行<br>操作数",
        "changed": true,
        "protectedIds": []
      },
      {
        "src": "Maximum Path Length",
        "dst": "最大路径长度",
        "changed": true,
        "protectedIds": []
      }
    ],
    "body": [
      [
        {
          "src": "Self-Attention",
          "dst": "自注意力",
          "changed": true,
          "protectedIds": []
        },
        {
          "src": "O(n² · d)",
          "dst": "O(n² · d)",
          "changed": false,
          "protectedIds": []
        },
        {
          "src": "O(1)",
          "dst": "O(1)",
          "changed": false,
          "protectedIds": [
            "P001"
          ]
        },
        {
          "src": "O(1)",
          "dst": "O(1)",
          "changed": false,
          "protectedIds": [
            "P001"
          ]
        }
      ],
      [
        {
          "src": "Recurrent",
          "dst": "循环",
          "changed": true,
          "protectedIds": []
        },
        {
          "src": "O(n · d²)",
          "dst": "O(n · d²)",
          "changed": false,
          "protectedIds": []
        },
        {
          "src": "O(n)",
          "dst": "O(n)",
          "changed": false,
          "protectedIds": []
        },
        {
          "src": "O(n)",
          "dst": "O(n)",
          "changed": false,
          "protectedIds": []
        }
      ],
      [
        {
          "src": "Convolutional",
          "dst": "卷积",
          "changed": true,
          "protectedIds": []
        },
        {
          "src": "O(k · n · d²)",
          "dst": "O(k · n · d²)",
          "changed": false,
          "protectedIds": []
        },
        {
          "src": "O(1)",
          "dst": "O(1)",
          "changed": false,
          "protectedIds": [
            "P001"
          ]
        },
        {
          "src": "O(logₖ(n))",
          "dst": "O(logₖ(n))",
          "changed": false,
          "protectedIds": []
        }
      ],
      [
        {
          "src": "Self-Attention (restricted)",
          "dst": "自注意力（受限）",
          "changed": true,
          "protectedIds": []
        },
        {
          "src": "O(r · n · d)",
          "dst": "O(r · n · d)",
          "changed": false,
          "protectedIds": []
        },
        {
          "src": "O(1)",
          "dst": "O(1)",
          "changed": false,
          "protectedIds": [
            "P001"
          ]
        },
        {
          "src": "O(n/r)",
          "dst": "O(n/r)",
          "changed": false,
          "protectedIds": []
        }
      ]
    ],
    "cellCount": 20,
    "changedCount": 8,
    "protectedCount": 4,
    "caption": {
      "en": "Table 1: Maximum path lengths, per-layer complexity and minimum number of sequential operations for different layer types.",
      "cn": "表 1：不同层类型的最大路径长度、每层复杂度与最少串行操作数。"
    }
  },
  "papers": [
    {
      "key": "transformer",
      "titleCn": "Attention Is All You Need（注意力就是你所需要的一切）",
      "titleEn": "Attention Is All You Need",
      "venue": "NeurIPS 2017",
      "link": "samples/transformer/index.html",
      "report": "samples/transformer/validation.html",
      "validation": {
        "blocks": 71.0,
        "headings": [
          14,
          14
        ],
        "tables": [
          1,
          1
        ],
        "images": [
          3,
          3
        ],
        "latex": [
          66,
          66
        ],
        "cjkRatio": 1.606,
        "status": "PASS",
        "reportPath": "demo/transformer/validation.md"
      }
    },
    {
      "key": "resnet",
      "titleCn": "深度残差学习用于图像识别",
      "titleEn": "Deep Residual Learning for Image Recognition",
      "venue": "CVPR 2016",
      "link": "samples/resnet/index.html",
      "report": "samples/resnet/validation.html",
      "validation": {
        "blocks": 51.0,
        "headings": [
          8,
          8
        ],
        "tables": [
          0,
          0
        ],
        "images": [
          2,
          2
        ],
        "latex": [
          29,
          29
        ],
        "cjkRatio": 1.63,
        "status": "PASS",
        "reportPath": "demo/resnet/validation.md"
      }
    },
    {
      "key": "deepseek-r1",
      "titleCn": "DeepSeek-R1：通过强化学习激励大语言模型的推理能力",
      "titleEn": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via RL",
      "venue": "arXiv 2501.12948",
      "link": "samples/deepseek-r1/index.html",
      "report": "samples/deepseek-r1/validation.html",
      "validation": {
        "blocks": 40.0,
        "headings": [
          7,
          7
        ],
        "tables": [
          1,
          1
        ],
        "images": [
          2,
          2
        ],
        "latex": [
          24,
          24
        ],
        "cjkRatio": 1.671,
        "status": "PASS",
        "reportPath": "demo/deepseek-r1/validation.md"
      }
    }
  ],
  "figure": {
    "src": "assets/figure-1.png",
    "caption": "图 1：Transformer——模型架构。"
  }
};
