/* academic-pdf-zh · V2 演示动画
   架构：单一 GSAP master timeline（分镜标签）。所有状态变化都是 fromTo/.set，
   任意时刻 seek 都能还原正确画面；UI 状态（进度/章节/遮罩）由 ticker 从
   tl.time() 推导，不依赖顺序回调。
   布局：设计画布 1600×900，纸张 860×800 @ (370,50)。 */
(function () {
  "use strict";

  var D = window.DEMO_DATA;
  var CFG = {
    duration: 36,
    designW: 1600,
    designH: 900,
    chapters: [
      { t: 0,  label: "结果" },
      { t: 4,  label: "输入" },
      { t: 8,  label: "正文与公式" },
      { t: 17, label: "表格逐格转换" },
      { t: 25, label: "阅读预览" },
      { t: 31, label: "收束" }
    ]
  };

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  var canvas = $("#canvas");
  var stage = $("#stage");
  var paperEn = $("#paperEn");
  var paperCn = $("#paperCn");

  /* ============ DOM 构建 ============ */

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function renderFormula(tex, mount) {
    try {
      window.katex.render(tex, mount, { displayMode: true, throwOnError: false });
    } catch (e) {
      mount.textContent = tex;
    }
  }

  /* 行内数学（.im span 内是去掉 $ 的原文 LaTeX），KaTeX inline 渲染 */
  function renderInlineMath(root) {
    $$(".im", root).forEach(function (n) {
      try {
        window.katex.render(n.textContent, n, { displayMode: false, throwOnError: false });
        n.classList.add("im-r");
      } catch (e) { /* 保留原文 */ }
    });
  }

  function buildDuoTable(mount) {
    var t = D.table;
    var tbl = el("table", "tbl");
    var thead = el("thead");
    var trh = el("tr");
    t.headers.forEach(function (c) {
      trh.appendChild(el("th", null,
        '<span class="c-en">' + c.src + '</span><span class="c-cn">' + c.dst + "</span>"));
    });
    thead.appendChild(trh);
    tbl.appendChild(thead);
    var tbody = el("tbody");
    t.body.forEach(function (row) {
      var tr = el("tr");
      row.forEach(function (c, i) {
        var td = el("td");
        if (i > 0) td.className = "cnm";
        td.innerHTML = '<span class="c-en">' + c.src + '</span><span class="c-cn">' + c.dst + "</span>";
        if (c.protectedIds.length) {
          var b = el("span", "badge", "✓");
          b.title = "保护 token " + c.protectedIds.join(", ") + " · 数值原样还原";
          td.appendChild(b);
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tbl.appendChild(tbody);
    mount.appendChild(tbl);
    return tbl;
  }

  function buildCnTable() {
    var t = D.table;
    var tbl = el("table", "tbl");
    var trh = el("tr");
    t.headers.forEach(function (c) { trh.appendChild(el("th", null, c.dst)); });
    var thead = el("thead");
    thead.appendChild(trh);
    tbl.appendChild(thead);
    var tbody = el("tbody");
    t.body.forEach(function (row) {
      var tr = el("tr");
      row.forEach(function (c, i) {
        var td = el("td");
        if (i > 0) td.className = "cnm";
        td.textContent = c.dst;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tbl.appendChild(tbody);
    return tbl;
  }

  var QS = D.prose;

  /* ---- EN 主纸（S1–S4） ---- */
  var innerSrc = $(".body-src .inner", paperEn);
  innerSrc.appendChild(el("div", "p-head",
    '<span class="doc-ico"></span><span class="t">' + D.papers[0].titleEn + "</span>" +
    '<span class="meta">原文（英文）· <b>PDF 解析</b></span>'));
  var pzone = el("div", "pzone");
  pzone.innerHTML =
    '<h3><span class="h-en">' + QS.heading.en + '</span><span class="h-cn">' + QS.heading.cn + '</span><span class="uline"></span></h3>' +
    '<div class="stk pz-p1"><p class="s-en">' + QS.para1.en + '</p><p class="s-cn">' + QS.para1.cn + "</p></div>" +
    '<div class="stk pz-line"><p class="s-en">' + QS.line.en + '</p><p class="s-cn">' + QS.line.cn + "</p></div>" +
    '<div class="formula f-pe" id="fPe"><span class="ftag"><span class="chip"><span class="dot"></span>公式 · 原样保留</span></span><span class="frame"></span><span class="fx"></span></div>' +
    '<div class="stk pz-p2"><p class="s-en">' + QS.para2.en + '</p><p class="s-cn">' + QS.para2.cn + "</p></div>";
  innerSrc.appendChild(pzone);
  var tzone = el("div", "tzone");
  var mainTCap = el("div", "t-cap", D.table.caption.en);
  tzone.appendChild(mainTCap);
  var duoMount = el("div");
  tzone.appendChild(duoMount);
  innerSrc.appendChild(tzone);
  buildDuoTable(duoMount);
  renderInlineMath(pzone);

  /* ---- S1 中文迷你纸（结果先行） ---- */
  var innerMini = $(".inner", paperCn);
  innerMini.appendChild(el("div", "p-head",
    '<span class="doc-ico"></span><span class="t">' + D.papers[0].titleCn + "</span>" +
    '<span class="meta">译文（中文）· <b>Markdown</b></span>'));
  var miniBody = el("div", "mini-body");
  var miniP2 = QS.para2.cn.split("。").slice(0, 2).join("。") + "。";
  miniBody.innerHTML =
    '<p style="margin-top:14px">' + QS.para1.cn + "</p>" +
    '<p class="pz-line">' + QS.line.cn + "</p>" +
    '<div class="formula f-pe-mini"><span class="fx"></span></div>' +
    '<p class="pz-line">' + miniP2 + "</p>";
  innerMini.appendChild(miniBody);
  var miniTz = el("div", "tzone");
  miniTz.appendChild(el("div", "t-cap", D.table.caption.cn));
  miniTz.appendChild(buildCnTable());
  innerMini.appendChild(miniTz);
  renderInlineMath(innerMini);

  /* ---- S5 阅读版式（同一张纸，切换内容） ---- */
  var bodyRead = el("div", "body-read");
  paperEn.appendChild(bodyRead);
  var rInner = el("div", "inner");
  bodyRead.appendChild(rInner);
  var rItems = [];
  var rTitle = el("h2", "r-title", D.papers[0].titleCn);
  var rMeta = el("div", "r-meta", "Attention Is All You Need · Vaswani et al., NeurIPS 2017 · 中文译文（样章摘录）");
  var rPara = el("p", null, QS.para1.cn);
  var rFormula = el("div", "formula f-pe-read");
  rFormula.appendChild(el("span", "fx"));
  var rTz = el("div", "tzone");
  rTz.appendChild(el("div", "t-cap", D.table.caption.cn));
  rTz.appendChild(buildCnTable());
  var rFig = el("div", "figrow",
    '<img src="' + D.figure.src + '" alt="Figure 1">' +
    '<span class="fig-cap">' + D.figure.caption + "</span>");
  [rTitle, rMeta, rPara, rFormula, rTz, rFig].forEach(function (n) {
    rInner.appendChild(n);
    rItems.push(n);
  });
  renderInlineMath(rInner);

  /* ---- KaTeX ---- */
  renderFormula(D.formulas.pe, $("#fPe .fx"));
  renderFormula(D.formulas.pe, $(".f-pe-mini .fx", paperCn));
  renderFormula(D.formulas.pe, $(".f-pe-read .fx"));

  /* ---- S2 输入条 / 流程 token ---- */
  var inputbar = el("div", "inputbar");
  inputbar.innerHTML =
    '<div class="who"><span class="uav">你</span>对话输入</div>' +
    '<div class="msg"><code>$academic-pdf-zh</code> 将这篇论文完整翻译为中文 Markdown</div>' +
    '<span class="file"><span class="pdf"></span>Attention_Is_All_You_Need.pdf · PDF 输入示意</span>';
  canvas.appendChild(inputbar);
  var toks = el("div", "pipeline-tokens");
  toks.innerHTML =
    '<span class="tok"><i>01</i>解析 PDF</span><span class="tok"><i>02</i>冻结公式 / 数字</span><span class="tok"><i>03</i>分块翻译</span>';
  canvas.appendChild(toks);

  /* ---- 章节提示芯片 ---- */
  var CUES = [
    { k: "k0", text: "逐段翻译 · 正文" },
    { k: "k1", text: "行内数学 · 未改动" },
    { k: "k2", text: "定位到表 1" },
    { k: "k3", text: "表头 · 逐格翻译" },
    { k: "k4", text: "行 1/4 · Self-Attention → 自注意力" },
    { k: "k5", text: "行 2/4 · Recurrent → 循环" },
    { k: "k6", text: "行 3/4 · Convolutional → 卷积" },
    { k: "k7", text: "行 4/4 · Self-Attention (restricted) → 自注意力（受限）" },
    { k: "k8", text: "表达式与数值 · 保持原样" },
    { k: "k9", text: "Markdown 阅读预览" }
  ];
  var cueWrap = el("div", "stepchips");
  CUES.forEach(function (c) {
    var chip = el("span", "chip", '<span class="dot"></span>' + c.text);
    chip.dataset.k = c.k;
    cueWrap.appendChild(chip);
  });
  canvas.appendChild(cueWrap);

  /* ---- S6 证据卡 + 收束 ---- */
  var v = D.papers[0].validation;
  var evidence = el("div", "evidence");
  evidence.innerHTML =
    '<div class="e-head"><span class="dot"></span>结构终检 · validation.md（已有样章报告）</div>' +
    '<div class="e-grid">' +
    '<div class="e-cell"><div class="k">Manifest 区块</div><div class="v">' + v.blocks + "</div></div>" +
    '<div class="e-cell"><div class="k">标题</div><div class="v">' + v.headings[0] + "<i>/" + v.headings[1] + "</i></div></div>" +
    '<div class="e-cell"><div class="k">表格</div><div class="v">' + v.tables[0] + "<i>/" + v.tables[1] + "</i></div></div>" +
    '<div class="e-cell"><div class="k">图片</div><div class="v">' + v.images[0] + "<i>/" + v.images[1] + "</i></div></div>" +
    '<div class="e-cell"><div class="k">LaTeX 公式</div><div class="v">' + v.latex[0] + "<i>/" + v.latex[1] + "</i></div></div>" +
    '<div class="e-cell"><div class="k">中英篇幅比</div><div class="v">' + v.cjkRatio.toFixed(3) + "</div></div>" +
    "</div>" +
    '<div class="e-status"><span class="pass">STATUS: PASS</span><span class="src">数量一致 ≠ 语义无误 · 样章级结果</span></div>';
  canvas.appendChild(evidence);

  var lockup = el("div", "lockup");
  lockup.innerHTML =
    '<span class="cmd">$academic-pdf-zh 将这篇论文完整翻译为中文 Markdown</span>' +
    '<div class="brand">academic<em>-pdf-zh</em></div>' +
    '<div class="tag">把英文学术 PDF 变成可精读的中文 Markdown</div>';
  canvas.appendChild(lockup);

  /* ---- 页面下方区块 ---- */
  (function renderSamples() {
    var mount = $("#cards");
    if (!mount) return;
    D.papers.forEach(function (p) {
      var vv = p.validation;
      mount.appendChild(el("div", "card",
        '<div class="venue">' + p.venue + ' · <b style="color:var(--keep)">PASS</b></div>' +
        '<div class="t-cn">' + p.titleCn + "</div>" +
        '<div class="t-en">' + p.titleEn + "</div>" +
        '<div class="m">标题 ' + vv.headings.join("/") + " · 表格 " + vv.tables.join("/") +
        " · 图片 " + vv.images.join("/") + " · 公式 " + vv.latex.join("/") +
        " · 区块 " + vv.blocks + " · 篇幅比 " + vv.cjkRatio.toFixed(3) + "</div>" +
        '<div class="links"><a href="' + p.link + '">站内阅读</a><a href="' + p.report + '">校验报告</a><a href="' + p.link.replace('index.html', 'sample.zip') + '" download>下载资源包</a></div>'));
    });
  })();

  (function renderReportExcerpt() {
    var pre = $("#reportExcerpt");
    if (!pre) return;
    pre.innerHTML = [
      "<span class='cm'># demo/transformer/validation.md 摘录（报告回放，非实时校验）</span>",
      "Manifest blocks: " + v.blocks,
      "Source / translated headings: " + v.headings.join(" / "),
      "Source / translated tables: " + v.tables.join(" / "),
      "Source / translated images: " + v.images.join(" / "),
      "Source / translated LaTeX expressions: " + v.latex.join(" / "),
      "CJK chars per source English word: " + v.cjkRatio,
      "Status: <span class='ok'>PASS</span>   <span class='cm'>← 该样章自身终检结果（样章级）</span>"
    ].join("\n");
  })();

  /* ============ 主时间轴 ============ */
  var tl;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var started = false;
  var AY = 780;   // 表格中心相对纸张顶部（ready 后实测）
  var AF = 450;   // 公式中心相对纸张顶部（ready 后实测）
  var PT = 30;    // 纸张 CSS top
  var RC = 450;   // 纸张相对中心（900 高的一半）；渲染点公式：stageY = PT + y + O + (p-O)*s
  var AFC = 380; // CN 迷你纸公式中心
  var cap1, conn, connTag;

  // origin=表格中心 AY 时，让纸张相对中心 RC 在缩放 s 下落在 wantCenter
  function yTable(s, wantCenter) { return wantCenter - PT - AY - (RC - AY) * s; }

  function buildTimeline() {
    tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
    tl.addLabel("s1", 0).addLabel("s2", 4).addLabel("s3", 8)
      .addLabel("s4", 17).addLabel("s5", 25).addLabel("s6", 31);

    /* ----- S1 · 0–4 结果优先 ----- */
    tl.fromTo(paperEn, { autoAlpha: 0, y: 24, x: -348, scale: 0.66 }, { autoAlpha: 1, y: -44, duration: 0.7, ease: "power3.out" }, 0.1);
    tl.fromTo(paperCn, { autoAlpha: 0, y: 24, x: 348, scale: 0.66 }, { autoAlpha: 1, y: -44, duration: 0.7, ease: "power3.out" }, 0.24);

    cap1 = el("div", "caption", "翻译正文，<i>保留</i>科研细节。");
    canvas.appendChild(cap1);
    tl.fromTo(cap1, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.5 }, 0.95);

    conn = el("div");
    var yEN = 436 + (AF - RC) * 0.66, yCN = 436 + (AFC - RC) * 0.66;
    var ang = Math.atan2(yCN - yEN, 128) * 180 / Math.PI;
    conn.style.cssText = "position:absolute;left:736px;top:" + yEN + "px;width:128px;height:2px;background:var(--accent);transform-origin:0 50%;box-shadow:0 0 12px rgba(201,80,63,.7)";
    canvas.appendChild(conn);
    tl.fromTo(conn, { autoAlpha: 0, scaleX: 0, rotation: 0 }, { autoAlpha: 1, scaleX: 1, rotation: ang, duration: 0.55, ease: "power2.inOut" }, 1.75);
    connTag = el("span", "chip", '<span class="dot"></span>公式 · 表格 · 数字　对应还原');
    connTag.style.cssText = "position:absolute;left:800px;top:" + (Math.min(yEN, yCN) - 64) + "px;transform:translateX(-50%)";
    canvas.appendChild(connTag);
    tl.fromTo(connTag, { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, duration: 0.4 }, 1.95);
    tl.to(connTag, { autoAlpha: 0, duration: 0.35 }, 2.85);
    tl.to(conn, { autoAlpha: 0, duration: 0.4 }, 2.9);

    tl.to(cap1, { autoAlpha: 0, y: -14, duration: 0.4 }, 3.3);
    tl.fromTo(paperEn, { x: -348, y: -44, scale: 0.66 }, { x: -60, y: -22, scale: 0.95, duration: 0.75, ease: "power3.inOut" }, 3.35);
    tl.fromTo(paperCn, { x: 348, y: -44, scale: 0.66, autoAlpha: 1 }, { x: 640, y: 310, scale: 0.135, autoAlpha: 0.5, duration: 0.75, ease: "power3.inOut" }, 3.35);

    /* ----- S2 · 4–8 输入 ----- */
    tl.fromTo(inputbar, { autoAlpha: 0, y: 34 }, { autoAlpha: 1, y: 0, duration: 0.6 }, 4.35);
    tl.fromTo(toks.children, { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: 0.4, stagger: 0.18 }, 5.3);
    tl.fromTo(paperCn, { autoAlpha: 0.5 }, { autoAlpha: 0, duration: 0.5 }, 4.2);
    tl.to(toks, { autoAlpha: 0, duration: 0.4 }, 6.45);
    tl.to(inputbar, { autoAlpha: 0, y: -16, duration: 0.5 }, 6.5);
    tl.fromTo(paperEn,
      { boxShadow: "0 24px 70px rgba(0,0,0,.5), 0 0 0 0px rgba(201,80,63,0)" },
      { boxShadow: "0 24px 70px rgba(0,0,0,.5), 0 0 0 4px rgba(201,80,63,.75)", duration: 0.45, ease: "power1.inOut", yoyo: true, repeat: 1 }, 6.95);

    /* ----- S3 · 8–17 正文与公式 ----- */
    var h3 = $(".pzone h3", paperEn);
    tl.fromTo($(".h-en", h3), { autoAlpha: 1, y: 0 }, { autoAlpha: 0, y: -12, duration: 0.5 }, 8.15);
    tl.fromTo($(".h-cn", h3), { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: 0.5 }, 8.3);
    tl.fromTo($(".uline", h3), { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: "power3.out" }, 8.45);

    var p1 = $(".pz-p1", paperEn);
    tl.fromTo($(".s-en", p1), { autoAlpha: 1, y: 0 }, { autoAlpha: 0, y: -14, duration: 0.55 }, 9.0);
    tl.fromTo($(".s-cn", p1), { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.55 }, 9.25);

    var pline = $(".pz-line", paperEn);
    tl.fromTo($(".s-en", pline), { autoAlpha: 1, y: 0 }, { autoAlpha: 0, y: -10, duration: 0.45 }, 10.85);
    tl.fromTo($(".s-cn", pline), { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, duration: 0.45 }, 11.0);

    var fPe = $("#fPe", paperEn);
    tl.fromTo($(".frame", fPe), { autoAlpha: 0, scale: 0.94 }, { autoAlpha: 1, scale: 1, duration: 0.5 }, 11.9);
    tl.fromTo($(".ftag", fPe), { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, duration: 0.4 }, 12.15);
    tl.to($(".ftag", fPe), { autoAlpha: 0, duration: 0.4 }, 14.6);
    tl.to($(".frame", fPe), { autoAlpha: 0, duration: 0.5 }, 15.0);

    var p2 = $(".pz-p2", paperEn);
    tl.fromTo($(".s-en", p2), { autoAlpha: 1, y: 0 }, { autoAlpha: 0, y: -14, duration: 0.55 }, 13.6);
    tl.fromTo($(".s-cn", p2), { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.55 }, 13.85);

    $$(".im", $(".s-cn", p2)).forEach(function (n, i) {
      var t0 = 15.1 + i * 0.22;
      tl.fromTo(n, { boxShadow: "0 0 0 0px rgba(46,143,106,0)", backgroundColor: "rgba(46,143,106,0)" },
        { boxShadow: "0 0 0 3px rgba(46,143,106,.85)", backgroundColor: "rgba(46,143,106,.12)", duration: 0.26 }, t0);
      tl.to(n, { boxShadow: "0 0 0 0px rgba(46,143,106,0)", duration: 0.34 }, t0 + 0.42);
    });

    /* ----- S4 · 17–25 表格逐格转换 ----- */
    // 16.98：切换 zoom 原点到表格中心并补偿 y，保证切换瞬间画面不跳
    tl.set(paperEn, { transformOrigin: "430px " + AY + "px", y: yTable(0.95, 458) }, 16.98);
    tl.fromTo(paperEn, { scale: 0.95 }, { scale: 1.7, y: 450 - PT - AY, duration: 0.9, ease: "power3.inOut" }, 17.0);
    tl.to($(".p-head", paperEn), { autoAlpha: 0.08, duration: 0.5 }, 17.0);
    tl.to(pzone, { autoAlpha: 0.06, duration: 0.5 }, 17.0);
    tl.fromTo(mainTCap, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.4 }, 17.3);
    
    $$("thead th", duoMount).forEach(function (th, i) {
      var t0 = 18.0 + i * 0.5;
      tl.fromTo($(".c-en", th), { autoAlpha: 1, y: 0 }, { autoAlpha: 0, y: -8, duration: 0.38 }, t0);
      tl.fromTo($(".c-cn", th), { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, duration: 0.38 }, t0 + 0.15);
    });

    $$("tbody tr", duoMount).forEach(function (tr, r) {
      var t0 = 20.3 + r * 1.0;
      tl.fromTo(tr, { backgroundColor: "rgba(201,80,63,0)" }, { backgroundColor: "rgba(201,80,63,0.10)", duration: 0.3 }, t0);
      tl.to(tr, { backgroundColor: "rgba(201,80,63,0)", duration: 0.35 }, t0 + 0.75);
      var nameTd = tr.children[0];
      tl.fromTo($(".c-en", nameTd), { autoAlpha: 1, y: 0 }, { autoAlpha: 0, y: -8, duration: 0.35 }, t0 + 0.12);
      tl.fromTo($(".c-cn", nameTd), { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, duration: 0.35 }, t0 + 0.25);
      $$(".badge", tr).forEach(function (b) {
        tl.fromTo(b, { autoAlpha: 0, scale: 0.5 }, { autoAlpha: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }, t0 + 0.45);
        tl.fromTo(b.parentElement, { boxShadow: "0 0 0 0px rgba(46,143,106,0)" },
          { boxShadow: "0 0 0 3px rgba(46,143,106,.7)", duration: 0.3 }, t0 + 0.5);
        tl.to(b.parentElement, { boxShadow: "0 0 0 0px rgba(46,143,106,0)", duration: 0.35 }, t0 + 0.9);
      });
    });

    /* ----- S5 · 25–31 阅读版式 ----- */
    tl.fromTo(paperEn, { scale: 1.7, y: 450 - PT - AY }, { scale: 0.95, y: yTable(0.95, 456), duration: 0.95, ease: "power3.inOut" }, 25.0);
    tl.to(innerSrc, { autoAlpha: 0, duration: 0.35 }, 25.3);
    tl.fromTo(bodyRead, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3 }, 25.4);
    tl.fromTo(rItems, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.28, ease: "power3.out" }, 25.9);
    tl.fromTo(rInner, { y: 0 }, { y: -14, duration: 1.4, ease: "power2.inOut" }, 26.4);

    /* ----- S6 · 31–36 证据 + 收束 ----- */
    // 原点切回纸张中心；保持视觉：渲染中心 = 50 + y + RC → y = 456 - 480
    tl.set(paperEn, { transformOrigin: "50% 50%", y: -24 }, 30.98);
    tl.fromTo(paperEn, { scale: 0.95, x: 0 }, { scale: 0.8, x: -190, y: -88, duration: 0.9, ease: "power3.inOut" }, 31.0);
    tl.fromTo(evidence, { autoAlpha: 0, x: 60 }, { autoAlpha: 1, x: 0, duration: 0.7 }, 31.2);
    tl.fromTo($$(".e-cell", evidence), { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.09 }, 31.5);
    tl.fromTo($(".e-status", evidence), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.5 }, 31.9);
    tl.fromTo(lockup, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.6 }, 32.8);
    tl.set({}, {}, CFG.duration); // 结尾定格：总时长必须等于 36s

    /* ----- 章节提示芯片 ----- */
    cueShow(9.0, 10.9, "k0");
    cueShow(15.1, 16.35, "k1");
    cueShow(16.45, 17.3, "k2");
    cueShow(17.95, 20.15, "k3");
    cueShow(20.3, 21.25, "k4");
    cueShow(21.3, 22.25, "k5");
    cueShow(22.3, 23.25, "k6");
    cueShow(23.3, 24.25, "k7");
    cueShow(24.3, 25.15, "k8");
    cueShow(26.05, 30.6, "k9");

    function cueShow(t0, t1, k) {
      var chip = cueWrap.querySelector('[data-k="' + k + '"]');
      tl.fromTo(chip, { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.35 }, t0);
      tl.to(chip, { autoAlpha: 0, y: -8, duration: 0.3 }, t1);
    }
    return tl;
  }

  /* 预播放初始态（防止时间轴渲染前闪现） */
  function initStates() {
    gsap.set([paperEn, paperCn, evidence, lockup, bodyRead], { autoAlpha: 0 });
    gsap.set(cueWrap.children, { autoAlpha: 0 });
    gsap.set([cap1, conn, connTag, inputbar, toks], { autoAlpha: 0 });
    gsap.set(Array.prototype.slice.call(toks.children), { autoAlpha: 0 });
    gsap.set($$(".h-cn, .s-cn, .c-cn, .badge, .frame, .ftag", canvas), { autoAlpha: 0 });
    gsap.set($(".uline", paperEn), { scaleX: 0 });
    gsap.set(mainTCap, { autoAlpha: 0 });
  }

  /* ============ 控制器 ============ */
  var btnPlay = $("#btnPlay");
  var btnReplay = $("#btnReplay");
  var bigPlay = $("#bigPlay");
  var scrub = $("#scrub");
  var fill = $(".fill", scrub);
  var knob = $(".knob", scrub);
  var timeLabel = $("#timeLabel");
  var chapterNow = $("#chapterNow");
  var endmask = $("#endmask");
  var rmNote = $("#rmNote");
  var dragging = false;

  function fmt(t) {
    t = Math.max(0, Math.min(CFG.duration, t));
    return Math.floor(t / 60) + ":" + ("0" + Math.floor(t % 60)).slice(-2);
  }
  function chapterAt(t) {
    var c = CFG.chapters[0];
    CFG.chapters.forEach(function (ch) { if (t >= ch.t - 0.01) c = ch; });
    return c;
  }
  function play() {
    if (!tl) return;
    if (tl.time() >= CFG.duration - 0.02) tl.seek(0);
    started = true;
    tl.play();
    syncButtons();
  }
  function pause() { if (tl) { tl.pause(); syncButtons(); } }
  function toggle() { if (tl && tl.paused()) play(); else pause(); }
  function replay() { if (!tl) return; started = true; tl.pause(0); tl.play(); syncButtons(); }
  function seek(t) {
    if (!tl) return;
    started = started || t > 0;
    tl.pause(Math.max(0, Math.min(CFG.duration, t)));
    syncButtons();
  }
  function syncButtons() {
    var paused = !tl || tl.paused();
    btnPlay.innerHTML = paused
      ? '<svg width="13" height="14" viewBox="0 0 13 14"><path d="M1 1l11 6-11 6z" fill="currentColor"/></svg>'
      : '<svg width="12" height="14" viewBox="0 0 12 14"><path d="M1 1h3.4v12H1zM7.6 1H11v12H7.6z" fill="currentColor"/></svg>';
    btnPlay.title = paused ? "播放" : "暂停";
  }

  gsap.ticker.add(function () {
    if (!tl) return;
    var t = tl.time();
    var pct = (t / CFG.duration) * 100;
    fill.style.width = pct + "%";
    knob.style.left = pct + "%";
    timeLabel.textContent = fmt(t) + " / " + fmt(CFG.duration);
    chapterNow.textContent = chapterAt(t).label;
    var ended = CFG.duration - t < 0.04;
    endmask.style.visibility = ended ? "visible" : "hidden";
    bigPlay.style.visibility = !started && t < 0.05 ? "visible" : "hidden";
    $$(".tick", scrub).forEach(function (tick) {
      tick.classList.toggle("lit", t >= parseFloat(tick.dataset.t) - 0.01);
    });
  });

  btnPlay.addEventListener("click", toggle);
  bigPlay.addEventListener("click", play);
  $("#maskReplay").addEventListener("click", replay);
  btnReplay.addEventListener("click", replay);

  (function buildTicks() {
    CFG.chapters.forEach(function (ch) {
      var tick = el("div", "tick");
      tick.dataset.t = ch.t;
      tick.style.left = (ch.t / CFG.duration) * 100 + "%";
      tick.title = ch.label + " · " + fmt(ch.t);
      scrub.appendChild(tick);
    });
  })();

  function scrubTo(e) {
    var r = scrub.getBoundingClientRect();
    var p = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    seek(p * CFG.duration);
  }
  scrub.addEventListener("pointerdown", function (e) {
    dragging = true;
    scrub.setPointerCapture(e.pointerId);
    scrubTo(e);
  });
  scrub.addEventListener("pointermove", function (e) { if (dragging) scrubTo(e); });
  scrub.addEventListener("pointerup", function () { dragging = false; });

  /* ============ 舞台缩放 ============ */
  function fit() {
    var r = stage.getBoundingClientRect();
    var k = Math.min(r.width / CFG.designW, r.height / CFG.designH);
    gsap.set(canvas, { scale: k });
    document.documentElement.style.setProperty("--stage-w", r.width + "px");
  }
  if (window.ResizeObserver) new ResizeObserver(fit).observe(stage);
  else window.addEventListener("resize", fit);

  /* ============ 就绪门控 + 入口 ============ */
  function whenReady() {
    var jobs = [document.fonts ? document.fonts.ready : Promise.resolve()];
    $$("img", canvas).forEach(function (img) {
      if (!img.complete) jobs.push(new Promise(function (res) { img.onload = img.onerror = res; }));
    });
    // rAF 在被遮挡/后台标签页里可能长时间不触发，加 900ms 超时兜底，
    // 保证就绪门控总能结算（真正播放仍在用户点击后开始）
    jobs.push(new Promise(function (res) {
      var done = false;
      function fin() { if (!done) { done = true; res(); } }
      requestAnimationFrame(function () { requestAnimationFrame(fin); });
      setTimeout(fin, 900);
    }));
    return Promise.all(jobs);
  }

  function measure() {
    var paperRect = paperEn.getBoundingClientRect();
    var k = paperRect.width / 860 || 1;
    // 先定 .stk 高度（中英文取较高者，会推动下方表格），再测量关键锚点
    $$(".stk", pzone).forEach(function (stk) {
      var en = $(".s-en", stk), cn = $(".s-cn", stk);
      if (en && cn) {
        stk.style.minHeight = Math.max(en.offsetHeight, cn.offsetHeight) / k + "px";
      }
    });
    var tblRect = duoMount.querySelector("table").getBoundingClientRect();
    var fRect = $("#fPe", paperEn).getBoundingClientRect();
    var fcnRect = $(".f-pe-mini", paperCn).getBoundingClientRect();
    var cnRect = paperCn.getBoundingClientRect();
    AY = Math.round((tblRect.top + tblRect.height / 2 - paperRect.top) / k);
    AF = Math.round((fRect.top + fRect.height / 2 - paperRect.top) / k);
    AFC = Math.round((fcnRect.top + fcnRect.height / 2 - cnRect.top) / k);
    AY = Math.max(420, Math.min(896, AY));
    AF = Math.max(300, Math.min(720, AF));
    AFC = Math.max(200, Math.min(860, AFC));
  }

  whenReady().then(function () {
    measure();
    buildTimeline();
    initStates();
    tl.pause(0);
    fit();
    syncButtons();

    var params = new URLSearchParams(location.search);
    var tq = params.get("t");
    if (tq != null && !isNaN(parseFloat(tq))) {
      seek(parseFloat(tq));
    } else if (reduced) {
      seek(CFG.duration - 0.05);
      rmNote.style.visibility = "visible";
    } else if (params.get("autoplay") === "1") {
      play();
    }
    window.demo = {
      play: play, pause: pause, toggle: toggle, seek: seek, replay: replay,
      time: function () { return tl ? tl.time() : 0; },
      timeline: function () { return tl; }
    };
    document.documentElement.classList.add("demo-ready");
  });
})();
