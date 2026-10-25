/* =====================================================================
   Diagramas de microrredes (SVG + fragmentos), no padrão de
   NovaPresent/anims/diagramas.js: cada etapa é um fragmento do revealjs
   (traços "se desenham", ícones e rótulos surgem). Alguns diagramas têm
   animação contínua: fluxo de potência (tracejado que corre), turbina
   eólica girando e a chave do PCC abrindo/fechando.

   Uso (o <script> uma vez por deck, depois do primeiro diagrama):
     ::: {.nova-svg data-nova-diagram="microrrede"}
     :::
     <script src="anims/microrredes.js"></script>

   Diagramas: rede-convencional, geracao-distribuida, microrrede, pcc,
   conversor-interface, estruturas-controle, componentes, modo-conectado,
   modo-ilhado, arq-ca, arq-cc, arq-hibrida, gfl-gfm, circuito-linha,
   droop-curva, droop-blocos, hierarquia, nivel0, nivel1, nivel2, nivel3,
   impedancia-virtual
   ===================================================================== */
(function () {
  "use strict";

  const C = { ink: "#1D1C1A", muted: "#77736A", grey: "#5F6368", rule: "#DDD7CB", navy: "#1B365D",
    rose: "#A63D4A", paper: "#F7F5F0", flow: "#D27A22", dc: "#7B4FD0", green: "#2E9C6B",
    blue: "#3A6EDB", sun: "#E0A21B" };
  const SERIF = '"Source Serif 4", Georgia, serif', SANS = '"Inter", sans-serif';
  const NS = "http://www.w3.org/2000/svg";

  // estilos das animações contínuas (uma vez por página)
  if (!document.getElementById("mg-style")) {
    const st = document.createElement("style");
    st.id = "mg-style";
    st.textContent = `
      .reveal .nova-svg .mg-flow { stroke-dasharray: 14 16; animation: mg-flow 1.3s linear infinite; }
      @keyframes mg-flow { to { stroke-dashoffset: -30; } }
      .reveal .nova-svg .mg-spin { transform-box: view-box; animation: mg-spin 4s linear infinite; }
      @keyframes mg-spin { to { transform: rotate(360deg); } }
      .reveal .nova-svg .mg-blade { transform-box: view-box; animation: mg-blade 8s ease-in-out infinite; }
      @keyframes mg-blade { 0%,42% { transform: rotate(0); } 50%,92% { transform: rotate(-32deg); } 100% { transform: rotate(0); } }
      .reveal .nova-svg .mg-on { animation: mg-on 8s ease-in-out infinite; }
      @keyframes mg-on { 0%,42% { opacity: 1; } 50%,92% { opacity: 0; } 100% { opacity: 1; } }
      .reveal .nova-svg .mg-off { animation: mg-off 8s ease-in-out infinite; }
      @keyframes mg-off { 0%,42% { opacity: 0; } 50%,92% { opacity: 1; } 100% { opacity: 0; } }
      @media (prefers-reduced-motion: reduce) {
        .reveal .nova-svg .mg-flow, .reveal .nova-svg .mg-spin, .reveal .nova-svg .mg-blade { animation: none; }
      }
      html.print-pdf .reveal .nova-svg .mg-flow, html.print-pdf .reveal .nova-svg .mg-spin,
      html.print-pdf .reveal .nova-svg .mg-blade, html.print-pdf .reveal .nova-svg .mg-on { animation: none; }
      html.print-pdf .reveal .nova-svg .mg-off { animation: none; opacity: 0; }`;
    document.head.appendChild(st);
  }

  // ---------------------------------------------------------------
  // Primitivas
  // ---------------------------------------------------------------
  const el = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  };
  // Texto; "P_1" e "ω_{MG}" viram subscritos
  function txt(p, s, x, y, o = {}) {
    const t = el("text", { x, y, "text-anchor": o.anchor || "middle", fill: o.color || C.ink,
      "font-family": o.family || SANS, "font-size": o.size || 20, "font-style": o.italic ? "italic" : "normal",
      "font-weight": o.weight || 400, class: "fade" + (o.cls ? " " + o.cls : "") }, p);
    let down = false;
    String(s).split(/(_\{[^}]*\}|_[\wα-ωΑ-Ω*]+)/).forEach((part) => {
      if (!part) return;
      const sub = part.match(/^_\{?([^}]*)\}?$/);
      const ts = el("tspan", sub ? { dy: "0.3em", "font-size": "72%" } : down ? { dy: "-0.3em" } : {}, t);
      ts.textContent = sub ? sub[1] : part;
      down = !!sub;
    });
    return t;
  }
  const serif = (p, s, x, y, o = {}) => txt(p, s, x, y, { family: SERIF, size: 28, ...o });
  const math = (p, s, x, y, o = {}) => txt(p, s, x, y, { family: SERIF, italic: true, size: 30, ...o });
  const note = (p, s, x, y, o = {}) => txt(p, s, x, y, { family: SERIF, italic: true, size: 24, color: C.rose, ...o });
  const cap = (p, s, x, y, o = {}) => txt(p, s, x, y, { size: 19, color: C.grey, ...o });
  const title = (p, s, x, y, o = {}) => txt(p, s, x, y, { family: SERIF, size: 30, weight: 600, color: C.navy, ...o });

  // traço que se desenha (dentro de fragmentos)
  const ink = (p, d, color = C.ink, w = 3, extra = {}) => el("path", { d, fill: "none", stroke: color,
    "stroke-width": w, "stroke-linecap": "round", "stroke-linejoin": "round", pathLength: 1, class: "ink", ...extra }, p);
  const poly = (pts) => "M" + pts.map((q) => q.join(",")).join(" L");
  const wire = (p, pts, color = C.ink, w = 3) => ink(p, poly(pts), color, w);
  // traço estático (surge com fade)
  const path = (p, d, o = {}) => el("path", { d, fill: o.fill || "none", stroke: o.color || C.ink,
    "stroke-width": o.w || 2.5, "stroke-linecap": "round", "stroke-linejoin": "round",
    ...(o.dash ? { "stroke-dasharray": o.dash } : {}), class: "fade" + (o.cls ? " " + o.cls : ""),
    ...(o.style ? { style: o.style } : {}), ...(o.opacity != null ? { opacity: o.opacity } : {}) }, p);
  const dashed = (p, pts, color = C.rose, w = 2.2) => path(p, poly(pts), { color, w, dash: "7 7" });
  function head(p, x, y, dir, color = C.ink, L = 15, Wd = 7) {
    const pts = { r: [[x, y], [x - L, y - Wd], [x - L, y + Wd]], l: [[x, y], [x + L, y - Wd], [x + L, y + Wd]],
      u: [[x, y], [x - Wd, y + L], [x + Wd, y + L]], d: [[x, y], [x - Wd, y - L], [x + Wd, y - L]] }[dir];
    el("polygon", { points: pts.map((q) => q.join(",")).join(" "), fill: color, class: "fade" }, p);
  }
  const dirOf = (a, b) => (b[0] > a[0] ? "r" : b[0] < a[0] ? "l" : b[1] < a[1] ? "u" : "d");
  function arrow(p, pts, color = C.ink, w = 2.8) {
    wire(p, pts, color, w);
    const [a, b] = pts.slice(-2);
    head(p, b[0], b[1], dirOf(a, b), color);
  }
  function darrow(p, pts, color = C.rose, w = 2.2) {
    dashed(p, pts, color, w);
    const [a, b] = pts.slice(-2);
    head(p, b[0], b[1], dirOf(a, b), color, 13, 6);
  }
  // fluxo de potência: tracejado que corre no sentido do caminho
  const flow = (p, pts, o = {}) => path(p, poly(pts), { color: o.color || C.flow, w: o.w || 5,
    cls: "mg-flow" + (o.cls ? " " + o.cls : ""), opacity: o.opacity ?? 0.85 });
  const dot = (p, x, y, r = 6, color = C.ink) => el("circle", { cx: x, cy: y, r, fill: color, class: "fade" }, p);

  // barramento (linha grossa)
  function bus(p, x1, x2, y, color = C.navy, label, o = {}) {
    ink(p, `M${x1},${y} L${x2},${y}`, color, 8);
    if (label) cap(p, label, o.lx ?? x2, o.ly ?? y - 16, { anchor: o.anchor || "end", color, weight: 600, size: 18 });
  }
  function vbus(p, x, y1, y2, color = C.navy, label) {
    ink(p, `M${x},${y1} L${x},${y2}`, color, 8);
    if (label) cap(p, label, x, y1 - 14, { color, weight: 600, size: 18 });
  }
  // caixa com uma ou mais linhas (1ª em serifa)
  function box(p, x, y, w, h, lines, o = {}) {
    const col = o.color || C.navy;
    el("rect", { x, y, width: w, height: h, rx: 10, fill: o.fill || "rgba(27,54,93,0.06)", stroke: col,
      "stroke-width": o.sw || 2.5, class: "fade" }, p);
    const L = [].concat(lines), gap = o.gap || 30;
    const y0 = y + h / 2 - ((L.length - 1) * gap) / 2 + 8;
    L.forEach((s, i) => {
      if (i === 0 && !o.sans) txt(p, s, x + w / 2, y0, { family: SERIF, size: o.size || 26, color: col,
        italic: o.italic, weight: o.weight || 400 });
      else txt(p, s, x + w / 2, y0 + i * gap, { size: o.sub || 18, color: i === 0 ? col : C.grey });
    });
  }
  function sum(p, x, y, signs = {}) {
    el("circle", { cx: x, cy: y, r: 22, fill: C.paper, stroke: C.ink, "stroke-width": 2.5, class: "fade" }, p);
    txt(p, "Σ", x, y + 8, { family: SERIF, size: 22 });
    if (signs.left) txt(p, signs.left, x - 34, y - 14, { size: 22 });
    if (signs.bottom) txt(p, signs.bottom, x - 18, y + 46, { size: 26, color: C.rose });
  }

  // ---------------------------------------------------------------
  // Símbolos e ícones
  // ---------------------------------------------------------------
  function sym(p, k, x, y, w, color) {
    if (k === "=") {
      path(p, `M${x - w / 2},${y - 4} H${x + w / 2}`, { color, w: 2.2 });
      path(p, `M${x - w / 2},${y + 4} H${x + w / 2}`, { color, w: 2.2, dash: "4 3" });
    } else path(p, `M${x - w / 2},${y} q${w / 4},${-w / 2.4} ${w / 2},0 t${w / 2},0`, { color, w: 2.2 });
  }
  // conversor: quadrado com diagonal; a (entrada) em cima à esquerda, b embaixo à direita
  function conv(p, x, y, a = "=", b = "~", s = 60, o = {}) {
    const h = s / 2, col = o.color || C.ink;
    el("rect", { x: x - h, y: y - h, width: s, height: s, rx: 6, fill: o.fill || C.paper, stroke: col,
      "stroke-width": o.sw || 2.5, class: "fade" }, p);
    el("line", { x1: x - h, y1: y + h, x2: x + h, y2: y - h, stroke: col, "stroke-width": 1.6, class: "fade" }, p);
    sym(p, a, x - h * 0.45, y - h * 0.42, s * 0.3, col);
    sym(p, b, x + h * 0.45, y + h * 0.48, s * 0.3, col);
    if (o.label) cap(p, o.label, x + h + 10, y + 6, { anchor: "start", size: o.lsize || 17, color: o.lcolor || C.grey,
      weight: o.lweight || 400 });
  }
  // gerador síncrono
  function gen(p, x, y, r = 36, label, o = {}) {
    el("circle", { cx: x, cy: y, r, fill: o.fill || C.paper, stroke: o.color || C.ink, "stroke-width": 2.6, class: "fade" }, p);
    sym(p, "~", x, y + 4, r * 1.1, o.color || C.ink);
    if (label) cap(p, label, x, y + r + 26, { size: 18 });
  }
  function xfmr(p, x, y, r = 22, color = C.ink) {
    el("circle", { cx: x - r * 0.55, cy: y, r, fill: "none", stroke: color, "stroke-width": 2.4, class: "fade" }, p);
    el("circle", { cx: x + r * 0.55, cy: y, r, fill: "none", stroke: color, "stroke-width": 2.4, class: "fade" }, p);
  }
  // torre de transmissão (topo em y, altura h)
  function tower(p, x, y, h, color = C.grey) {
    const w = h * 0.26;
    path(p, `M${x - w},${y + h} L${x},${y} L${x + w},${y + h}`, { color, w: 2.4 });
    path(p, `M${x - w * 0.9},${y + h * 0.12} H${x + w * 0.9} M${x - w * 0.7},${y + h * 0.3} H${x + w * 0.7}`, { color, w: 2.4 });
    path(p, `M${x - w * 0.55},${y + h * 0.55} L${x + w * 0.35},${y + h * 0.75} M${x + w * 0.55},${y + h * 0.55} L${x - w * 0.35},${y + h * 0.75}`, { color, w: 1.6 });
  }
  function house(p, x, yb, s = 70, o = {}) {
    const col = o.color || C.ink;
    path(p, `M${x - s / 2},${yb} V${yb - s * 0.6} L${x},${yb - s * 1.02} L${x + s / 2},${yb - s * 0.6} V${yb} Z`,
      { color: col, w: 2.4, fill: o.fill || "rgba(27,54,93,0.05)" });
    path(p, `M${x - s * 0.1},${yb} V${yb - s * 0.32} H${x + s * 0.1} V${yb}`, { color: col, w: 2 });
    if (o.label) cap(p, o.label, x, yb + 26, { size: 17 });
  }
  function factory(p, x, yb, s = 90, o = {}) {
    const col = o.color || C.ink, L = x - s / 2;
    path(p, `M${L},${yb} V${yb - s * 0.45} L${L + s / 4},${yb - s * 0.65} V${yb - s * 0.45} L${L + s / 2},${yb - s * 0.65} V${yb - s * 0.45} L${L + s * 0.75},${yb - s * 0.65} V${yb - s * 0.9} H${L + s * 0.88} V${yb - s * 0.45} H${L + s} V${yb} Z`,
      { color: col, w: 2.4, fill: "rgba(27,54,93,0.05)" });
    if (o.label) cap(p, o.label, x, yb + 26, { size: 17 });
  }
  function pv(p, x, y, s = 80, o = {}) {
    const a = [x - s / 2, y + s * 0.22], b = [x - s / 4, y - s * 0.22], c = [x + s / 2, y - s * 0.22], d = [x + s / 4, y + s * 0.22];
    path(p, poly([a, b, c, d]) + " Z", { color: C.blue, w: 2.4, fill: "rgba(58,110,219,0.12)" });
    path(p, `M${x - s * 0.375},${y} H${x + s * 0.375} M${x - s / 12},${y - s * 0.22} L${x - s / 3 + s / 12},${y + s * 0.22} M${x + s / 6},${y - s * 0.22} L${x - s / 12 + s / 12},${y + s * 0.22}`,
      { color: C.blue, w: 1.4 });
    if (o.sun !== false) {
      const sx = x + s * 0.5, sy = y - s * 0.55, r = s * 0.11;
      el("circle", { cx: sx, cy: sy, r, fill: "rgba(224,162,27,0.25)", stroke: C.sun, "stroke-width": 2, class: "fade" }, p);
      let d = "";
      for (let k = 0; k < 8; k++) {
        const t = (k * Math.PI) / 4;
        d += `M${sx + Math.cos(t) * r * 1.5},${sy + Math.sin(t) * r * 1.5} L${sx + Math.cos(t) * r * 2.2},${sy + Math.sin(t) * r * 2.2} `;
      }
      path(p, d, { color: C.sun, w: 1.8 });
    }
    if (o.label) cap(p, o.label, x, y + s * 0.22 + 28, { size: 17 });
  }
  // turbina eólica: base em yb, altura s; pás giram
  function wind(p, x, yb, s = 120, o = {}) {
    const hy = yb - s;
    path(p, `M${x - s * 0.04},${yb} L${x - s * 0.015},${hy} M${x + s * 0.04},${yb} L${x + s * 0.015},${hy}`, { color: C.ink, w: 2.4 });
    const g = el("g", { class: "mg-spin", style: `transform-origin: ${x}px ${hy}px` }, p);
    for (let k = 0; k < 3; k++) {
      const t = -Math.PI / 2 + (k * 2 * Math.PI) / 3, L = s * 0.48, c = Math.cos(t), sn = Math.sin(t);
      const tipx = x + c * L, tipy = hy + sn * L, nx = -sn * s * 0.05, ny = c * s * 0.05;
      path(g, `M${x},${hy} Q${x + c * L * 0.35 + nx},${hy + sn * L * 0.35 + ny} ${tipx},${tipy} Q${x + c * L * 0.5},${hy + sn * L * 0.5} ${x},${hy} Z`,
        { color: C.ink, w: 1.8, fill: "rgba(29,28,26,0.08)" });
    }
    dot(p, x, hy, 5);
    if (o.label) cap(p, o.label, x, yb + 26, { size: 17 });
  }
  function battery(p, x, y, s = 70, o = {}) {
    const w = s, h = s * 0.62;
    el("rect", { x: x - w / 2, y: y - h / 2, width: w, height: h, rx: 6, fill: "rgba(46,156,107,0.12)",
      stroke: C.green, "stroke-width": 2.4, class: "fade" }, p);
    el("rect", { x: x - w * 0.12, y: y - h / 2 - 8, width: w * 0.24, height: 8, rx: 2, fill: C.green, class: "fade" }, p);
    txt(p, "+  −", x, y + 8, { size: s * 0.3, color: C.green, weight: 600 });
    if (o.label) cap(p, o.label, x, y + h / 2 + 26, { size: 17 });
  }
  function dcload(p, x, y, s = 70, o = {}) {
    el("rect", { x: x - s / 2, y: y - s * 0.35, width: s, height: s * 0.7, rx: 6, fill: "rgba(123,79,208,0.08)",
      stroke: C.dc, "stroke-width": 2.4, class: "fade" }, p);
    sym(p, "=", x, y, s * 0.4, C.dc);
    if (o.label) cap(p, o.label, x, y + s * 0.35 + 26, { size: 17 });
  }
  // terminal de terra
  const ground = (p, x, y) => path(p, `M${x - 22},${y} H${x + 22} M${x - 14},${y + 8} H${x + 14} M${x - 6},${y + 16} H${x + 6}`, { w: 2.4 });
  // chave: terminais em x±30; "anim" = abre e fecha em ciclo
  function sw(p, x, y, o = {}) {
    const col = o.color || C.ink;
    el("circle", { cx: x - 30, cy: y, r: 5, fill: col, class: "fade" }, p);
    el("circle", { cx: x + 30, cy: y, r: 5, fill: C.paper, stroke: col, "stroke-width": 2.4, class: "fade" }, p);
    const end = o.open ? `${x + 20},${y - 34}` : `${x + 26},${y}`;
    path(p, `M${x - 30},${y} L${end}`, { color: col, w: 3.4, cls: o.anim ? "mg-blade" : "",
      style: o.anim ? `transform-origin: ${x - 30}px ${y}px` : undefined });
  }
  // indutor (bobina) de x1 a x2 na altura y
  function coil(p, x1, x2, y, n = 4, color = C.ink) {
    const step = (x2 - x1) / n;
    let d = `M${x1},${y}`;
    for (let k = 0; k < n; k++) d += ` a${step / 2},${step / 2} 0 0,1 ${step},0`;
    ink(p, d, color, 3);
  }
  // capacitor em derivação: nó (x, y) até o terra
  function shuntCap(p, x, y, h = 40) {
    wire(p, [[x, y], [x, y + h]]);
    path(p, `M${x - 20},${y + h} H${x + 20} M${x - 20},${y + h + 12} H${x + 20}`, { w: 3 });
    wire(p, [[x, y + h + 12], [x, y + h + 40]]);
    ground(p, x, y + h + 40);
  }
  // fonte de corrente (seta) ou de tensão (~)
  function source(p, x, y, r, kind, color = C.ink) {
    el("circle", { cx: x, cy: y, r, fill: C.paper, stroke: color, "stroke-width": 2.6, class: "fade" }, p);
    if (kind === "i") { path(p, `M${x},${y + r * 0.55} V${y - r * 0.5}`, { color, w: 2.6 }); head(p, x, y - r * 0.6, "u", color, 12, 6); }
    else sym(p, "~", x, y + 4, r * 1.1, color);
  }
  // unidade pendurada num barramento: cadeia de conversores (de cima p/ baixo) + ícone
  function unit(p, x, yBus, chain, icon, o = {}) {
    const s = 56, gap = 84;
    let y = yBus;
    chain.forEach(([a, b], i) => {
      const cy = yBus + 70 + i * gap;
      wire(p, [[x, y], [x, cy - s / 2]]);
      conv(p, x, cy, a, b, s, { color: o.color });
      y = cy + s / 2;
    });
    const iy = yBus + 70 + chain.length * gap + 10;
    wire(p, [[x, y], [x, iy - 40]]);
    const L = o.label;
    if (icon === "pv") pv(p, x, iy - 5, 84, { label: L });
    else if (icon === "battery") battery(p, x, iy, 72, { label: L });
    else if (icon === "wind") wind(p, x, iy + 130, 110, { label: L });
    else if (icon === "house") house(p, x, iy + 38, 70, { label: L });
    else if (icon === "dcload") dcload(p, x, iy, 70, { label: L });
    else if (icon === "gen") gen(p, x, iy, 34, L);
    return { n: chain.length, yEnd: iy };
  }
  // número de estágios de conversão
  function badge(p, x, y, n) {
    el("circle", { cx: x, cy: y, r: 17, fill: n ? C.rose : C.green, class: "fade" }, p);
    txt(p, String(n), x, y + 7, { size: 19, color: "#fff", weight: 700 });
  }

  // ---------------------------------------------------------------
  // Diagramas
  // ---------------------------------------------------------------
  function modo(svg, g, ilhado) {
    svg.setAttribute("viewBox", "0 0 1500 520");
    const Y = 230;
    const R = el("g", ilhado ? { opacity: 0.32 } : {}, svg);
    tower(R, 95, 110, 200);
    cap(R, "rede principal", 95, 345, { size: 18 });
    wire(R, [[120, Y], [250, Y]]);
    sw(svg, 280, Y, { open: ilhado, color: ilhado ? C.rose : C.ink });
    txt(svg, "PCC", 280, Y + 40, { size: 19, weight: 700, color: ilhado ? C.rose : C.ink });
    bus(svg, 310, 1440, Y, C.navy, "barramento CA", { ly: Y + 34 });
    // armazenamento e FV
    wire(svg, [[520, Y], [520, 290]]);
    conv(svg, 520, 320, "=", "~", 60, ilhado ? { color: C.navy, sw: 4.5 } : {});
    wire(svg, [[520, 350], [520, 400]]);
    battery(svg, 520, 430, 76);
    wire(svg, [[780, Y], [780, 290]]);
    conv(svg, 780, 320, "=", "~", 60);
    wire(svg, [[780, 350], [780, 400]]);
    pv(svg, 780, 425, 86, { sun: true });
    wire(svg, [[1030, Y], [1030, 318]]);
    house(svg, 1030, 400, 80, { label: "cargas" });
    wire(svg, [[1240, Y], [1240, 320]]);
    factory(svg, 1240, 400, 100);
    let G = g(1);
    if (!ilhado) {
      cap(G, "segue a rede (P, Q)", 560, 326, { anchor: "start", size: 17 });
      cap(G, "segue a rede (P, Q)", 820, 326, { anchor: "start", size: 17 });
      txt(G, "a rede impõe V e f", 95, 75, { family: SERIF, italic: true, size: 24, color: C.navy });
    } else {
      cap(G, "forma a rede (V, f)", 560, 326, { anchor: "start", size: 18, color: C.navy, weight: 700 });
      cap(G, "segue (P, Q)", 820, 326, { anchor: "start", size: 17 });
      note(G, "chave aberta", 280, Y - 50);
    }
    G = g(2);
    if (!ilhado) {
      flow(G, [[160, 200], [1300, 200]]);
      flow(G, [[1300, 174], [160, 174]], { color: C.green });
      cap(G, "importa", 1312, 206, { anchor: "start", color: C.flow, weight: 600 });
      cap(G, "exporta", 1312, 180, { anchor: "start", color: C.green, weight: 600 });
    } else {
      flow(G, [[520, 286], [520, 246], [1020, 246]]);
      flow(G, [[780, 286], [780, 262], [1230, 262], [1230, 300]]);
      note(G, "V e f definidas pela própria microrrede", 900, 510, { color: C.navy });
    }
  }

  function arqFrame(svg, opts) {
    svg.setAttribute("viewBox", "0 0 1500 520");
    const Y = 150;
    tower(svg, 80, 40, 180);
    cap(svg, "rede", 80, 250, { size: 18 });
    wire(svg, [[100, Y], [150, Y]]);
    sw(svg, 180, Y);
    return Y;
  }

  const DIAGRAMS = {
    // ---------------- rede convencional ----------------
    "rede-convencional"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 540");
      const Y = 280;
      let G = g(1);
      title(G, "Geração centralizada", 165, 60);
      cap(G, "grandes usinas síncronas", 165, 92);
      gen(G, 100, 200, 36, "UHE");
      gen(G, 100, 380, 36, "UTE");
      wire(G, [[136, 200], [195, 200], [195, 380], [136, 380]]);
      wire(G, [[195, Y], [232, Y]]);
      xfmr(G, 256, Y);
      G = g(2);
      title(G, "Transmissão", 610, 60);
      cap(G, "alta tensão, longas distâncias", 610, 92);
      wire(G, [[281, Y], [930, Y]]);
      [430, 610, 790].forEach((x) => tower(G, x, Y, 170));
      G = g(3);
      title(G, "Distribuição e cargas", 1220, 60);
      cap(G, "média e baixa tensão", 1220, 92);
      xfmr(G, 955, Y);
      wire(G, [[980, Y], [1460, Y]]);
      [[1070, "h"], [1210, "h"], [1370, "f"]].forEach(([x, k]) => {
        wire(G, [[x, Y], [x, 370]]);
        if (k === "h") house(G, x, 450, 76); else factory(G, x, 455, 100);
      });
      G = g(4);
      flow(G, [[140, 240], [1440, 240]]);
      txt(G, "fluxo de potência unidirecional →", 800, 225, { family: SERIF, italic: true, size: 24, color: C.flow });
      note(G, "a inércia das máquinas síncronas sustenta a frequência", 750, 525, { color: C.navy });
    },

    // ---------------- geração distribuída ----------------
    "geracao-distribuida"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 540");
      const Y = 250;
      let G = g(1);
      cap(G, "transmissão", 30, Y - 18, { anchor: "start" });
      wire(G, [[40, Y], [148, Y]]);
      xfmr(G, 172, Y);
      cap(G, "subestação", 172, Y + 52);
      wire(G, [[197, Y], [1460, Y]]);
      [[250, "h"], [720, "h"], [1200, "f"], [1370, "h"]].forEach(([x, k]) => {
        wire(G, [[x, Y], [x, 380]]);
        if (k === "h") house(G, x, 460, 76); else factory(G, x, 465, 100);
      });
      G = g(2);
      [[420, "pv"], [570, "wind"], [880, "battery"], [1040, "pv"]].forEach(([x, k]) => {
        wire(G, [[x, Y], [x, 302]]);
        conv(G, x, 330, k === "wind" ? "~" : "=", "~", 56);
        wire(G, [[x, 358], [x, k === "wind" ? 372 : 392]]);
        if (k === "pv") pv(G, x, 425, 84);
        else if (k === "battery") battery(G, x, 425, 72);
        else wind(G, x, 530, 110);
      });
      note(G, "geração distribuída conectada por conversores", 750, 60, { color: C.navy });
      G = g(3);
      [420, 570, 880, 1040].forEach((x) => flow(G, [[x, 300], [x, 262]], { w: 4 }));
      flow(G, [[1440, 212], [200, 212]]);
      txt(G, "← a potência pode voltar à subestação: fluxo bidirecional", 820, 196,
        { family: SERIF, italic: true, size: 24, color: C.flow });
    },

    // ---------------- a microrrede ----------------
    microrrede(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 600");
      const Y = 250;
      let G = g(1);
      el("rect", { x: 250, y: 30, width: 1235, height: 555, rx: 22, fill: "rgba(27,54,93,0.025)", stroke: C.muted,
        "stroke-width": 2, "stroke-dasharray": "9 8", class: "fade" }, G);
      txt(G, "fronteira da microrrede", 1465, 64, { family: SERIF, italic: true, size: 22, color: C.muted, anchor: "end" });
      tower(G, 90, 140, 200);
      cap(G, "rede principal", 90, 370);
      wire(G, [[112, Y], [260, Y]]);
      sw(G, 290, Y);
      txt(G, "PCC", 290, Y - 40, { size: 20, weight: 700, color: C.rose });
      bus(G, 320, 1450, Y, C.navy);
      G = g(2);
      wire(G, [[430, Y], [430, 312]]); conv(G, 430, 340, "=", "~", 56);
      wire(G, [[430, 368], [430, 410]]); pv(G, 430, 445, 84, { label: "fotovoltaica" });
      wire(G, [[600, Y], [600, 312]]); conv(G, 600, 340, "~", "~", 56);
      wire(G, [[600, 368], [600, 392]]); wind(G, 600, 560, 120);
      cap(G, "eólica", 640, 560, { anchor: "start", size: 17 });
      G = g(3);
      wire(G, [[770, Y], [770, 312]]); conv(G, 770, 340, "=", "~", 56);
      wire(G, [[770, 368], [770, 418]]); battery(G, 770, 450, 76, { label: "baterias" });
      wire(G, [[940, Y], [940, 384]]); gen(G, 940, 420, 36, "gerador diesel");
      G = g(4);
      wire(G, [[1110, Y], [1110, 342]]); house(G, 1110, 420, 80, { label: "carga crítica" });
      wire(G, [[1270, Y], [1270, 335]]); factory(G, 1270, 425, 100, { label: "carga não crítica" });
      wire(G, [[1410, Y], [1410, 350]]); house(G, 1410, 420, 66);
      G = g(5);
      box(G, 660, 70, 300, 64, ["controle central (MGCC)"], { size: 22 });
      [290, 430, 600, 770, 940, 1110, 1270].forEach((x) => {
        dashed(G, [[810, 134], [x, Y - 22]]);
        dot(G, x, Y - 22, 5, C.rose);
      });
      note(G, "comunicação", 1000, 115, { anchor: "start", size: 20 });
    },

    // ---------------- PCC (abre e fecha em ciclo) ----------------
    pcc(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 470");
      const Y = 240;
      tower(svg, 100, 120, 210);
      cap(svg, "rede principal", 100, 360);
      wire(svg, [[125, Y], [300, Y]]);
      xfmr(svg, 330, Y);
      wire(svg, [[355, Y], [540, Y]]);
      el("circle", { cx: 450, cy: Y, r: 11, fill: C.paper, stroke: C.navy, "stroke-width": 2.5, class: "fade" }, svg);
      cap(svg, "medição", 450, Y + 40, { color: C.navy, size: 17 });
      sw(svg, 570, Y, { anim: true });
      txt(svg, "PCC", 570, Y + 50, { size: 22, weight: 700, color: C.rose });
      txt(svg, "conectada", 570, Y - 60, { family: SERIF, italic: true, size: 26, color: C.navy, cls: "mg-on" });
      txt(svg, "ilhada", 570, Y - 60, { family: SERIF, italic: true, size: 26, color: C.rose, cls: "mg-off" });
      wire(svg, [[600, Y], [720, Y]]);
      el("rect", { x: 700, y: 100, width: 760, height: 300, rx: 22, fill: "rgba(27,54,93,0.025)", stroke: C.muted,
        "stroke-width": 2, "stroke-dasharray": "9 8", class: "fade" }, svg);
      txt(svg, "microrrede", 1440, 134, { family: SERIF, italic: true, size: 22, color: C.muted, anchor: "end" });
      bus(svg, 720, 1420, Y, C.navy);
      wire(svg, [[860, Y], [860, 300]]); house(svg, 860, 370, 64);
      wire(svg, [[1060, Y], [1060, 290]]); conv(svg, 1060, 312, "=", "~", 44);
      wire(svg, [[1060, 334], [1060, 346]]); battery(svg, 1060, 368, 52);
      wire(svg, [[1260, Y], [1260, 290]]); conv(svg, 1260, 312, "=", "~", 44);
      wire(svg, [[1260, 334], [1260, 350]]); pv(svg, 1260, 368, 60, { sun: false });
      flow(svg, [[130, 205], [700, 205]], { cls: "mg-on" });
      const G = g(1);
      [[300, "isola a microrrede em faltas"], [750, "mede o intercâmbio P, Q"], [1200, "sincroniza antes de reconectar"]]
        .forEach(([x, s]) => txt(G, "• " + s, x, 450, { family: SERIF, size: 25, color: C.navy }));
    },

    // ---------------- o conversor como interface ----------------
    "conversor-interface"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 520");
      const Y = 230;
      let G = g(1);
      [[110, "fonte primária"], [300, "barramento CC"], [480, "inversor (VSI)"], [690, "filtro LC"], [920, "barramento CA"]]
        .forEach(([x, s]) => cap(G, s, x, 110, { size: 18, weight: 600, color: C.navy }));
      pv(G, 110, Y + 10, 110, { sun: true });
      wire(G, [[165, Y], [430, Y]]);
      shuntCap(G, 300, Y, 30);
      conv(G, 480, Y, "=", "~", 100);
      wire(G, [[530, Y], [600, Y]]);
      coil(G, 600, 720, Y);
      wire(G, [[720, Y], [900, Y]]);
      shuntCap(G, 770, Y, 30);
      vbus(G, 920, 150, 320);
      G = g(2);
      box(G, 360, 410, 240, 64, ["controle digital"], { size: 22 });
      arrow(G, [[480, 410], [480, 282]], C.navy);
      cap(G, "PWM", 494, 360, { anchor: "start", color: C.navy, weight: 600 });
      darrow(G, [[850, Y], [850, 442], [602, 442]], C.navy);
      cap(G, "v, i medidos", 864, 400, { anchor: "start", color: C.navy });
      G = g(3);
      ["a rede “vê” o conversor", "pelo que o controle impõe:", "fonte de tensão, de corrente,", "inércia virtual…"]
        .forEach((s, i) => note(G, s, 1010, 190 + i * 40, { anchor: "start", size: 27 }));
    },

    // ---------------- centralizado × descentralizado × distribuído ----------------
    "estruturas-controle"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 560");
      [500, 1000].forEach((x) => path(svg, `M${x},20 V540`, { color: C.rule, w: 2 }));
      const panel = (G, cx, name, kind, l1, l2) => {
        title(G, name, cx, 45);
        bus(G, cx - 200, cx + 200, 440, C.navy);
        const xs = [cx - 130, cx, cx + 130];
        xs.forEach((x) => { wire(G, [[x, 440], [x, 398]]); conv(G, x, 370, "=", "~", 56); });
        if (kind === "central") {
          box(G, cx - 120, 105, 240, 60, ["controlador central"], { size: 21 });
          xs.forEach((x) => darrow(G, [[cx, 165], [x, 334]]));
        } else {
          xs.forEach((x) => {
            box(G, x - 34, 230, 68, 52, ["C"], { italic: true });
            wire(G, [[x, 282], [x, 342]], C.navy, 2.5);
          });
          if (kind === "distrib") {
            [[xs[0] + 34, xs[1] - 34], [xs[1] + 34, xs[2] - 34]].forEach(([a, b]) => {
              dashed(G, [[a, 248], [b, 248]]);
              dashed(G, [[b, 264], [a, 264]]);
            });
            path(G, `M${xs[0]},230 Q${cx},150 ${xs[2]},230`, { color: C.rose, w: 2.2, dash: "7 7" });
          } else {
            xs.forEach((x) => cap(G, "medida local", x, 215, { size: 15, color: C.muted }));
          }
        }
        cap(G, l1, cx, 500, { size: 20, color: C.ink });
        cap(G, l2, cx, 530, { size: 18 });
      };
      panel(g(1), 250, "Centralizado", "central", "um controlador decide por todos", "depende de comunicação rápida");
      panel(g(2), 750, "Descentralizado", "local", "cada unidade decide com medidas locais", "sem comunicação (ex.: droop)");
      panel(g(3), 1250, "Distribuído", "distrib", "cada unidade conversa com vizinhos", "sem ponto central de falha");
    },

    // ---------------- componentes ----------------
    componentes(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 570");
      const YB = 480;
      bus(svg, 40, 1460, YB, C.navy);
      let G = g(1);
      title(G, "Geração", 190, 40);
      pv(G, 110, 175, 96);
      wind(G, 280, 300, 130);
      wire(G, [[110, 200], [110, 300]]); conv(G, 110, 330, "=", "~", 56);
      wire(G, [[280, 300], [280, 302]]); conv(G, 280, 330, "~", "~", 56);
      wire(G, [[110, 358], [110, YB]]); wire(G, [[280, 358], [280, YB]]);
      cap(G, "FV, eólica, PCH, diesel", 190, 530);
      G = g(2);
      title(G, "Armazenamento", 560, 40);
      battery(G, 560, 160, 90, {});
      wire(G, [[560, 188], [560, 252]]); conv(G, 560, 280, "=", "=", 56, { label: "CC-CC" });
      wire(G, [[560, 308], [560, 352]]); conv(G, 560, 380, "=", "~", 56, { label: "CC-CA" });
      wire(G, [[560, 408], [560, YB]]);
      cap(G, "baterias, supercapacitores", 560, 530);
      G = g(3);
      title(G, "Conversores", 940, 40);
      const top = 120, bot = 360, legs = [880, 950, 1020];
      wire(G, [[830, top], [1040, top]]); wire(G, [[830, bot], [1040, bot]]);
      txt(G, "+", 815, top + 8, { size: 24 }); txt(G, "−", 815, bot + 8, { size: 24 });
      legs.forEach((x, i) => {
        wire(G, [[x, top], [x, bot]], C.ink, 2.4);
        [top + 30, bot - 80].forEach((y) => el("rect", { x: x - 13, y, width: 26, height: 50, rx: 4,
          fill: "rgba(27,54,93,0.15)", stroke: C.navy, "stroke-width": 2, class: "fade" }, G));
        dot(G, x, 240, 5);
        wire(G, [[x, 240], [x + 28, 240]], C.ink, 2.2);
        cap(G, "abc"[i], x + 38, 246, { size: 17, anchor: "start" });
      });
      wire(G, [[1082, 240], [1100, 240], [1100, YB]]);
      path(G, `M1088,${YB - 70} L1112,${YB - 94}`, { w: 2 });
      cap(G, "3", 1120, YB - 82, { anchor: "start", size: 16 });
      cap(G, "a interface: CC-CA, CC-CC, CA-CC", 940, 530);
      G = g(4);
      title(G, "Cargas", 1310, 40);
      house(G, 1240, 290, 90, {}); cap(G, "crítica", 1240, 182, { size: 17 });
      factory(G, 1390, 290, 110, {}); cap(G, "não crítica", 1390, 176, { size: 17 });
      wire(G, [[1240, 290], [1240, YB]]);
      wire(G, [[1390, 290], [1390, 360]]);
      sw(G, 1390, 390, { open: true, color: C.rose });
      wire(G, [[1390, 420], [1390, YB]]);
      cap(G, "corte de", 1432, 384, { size: 15, anchor: "start", color: C.rose });
      cap(G, "carga", 1432, 402, { size: 15, anchor: "start", color: C.rose });
      cap(G, "críticas e não críticas", 1310, 530);
    },

    "modo-conectado"(svg, g) { modo(svg, g, false); },
    "modo-ilhado"(svg, g) { modo(svg, g, true); },

    // ---------------- arquiteturas ----------------
    "arq-ca"(svg, g) {
      const Y = arqFrame(svg);
      let G = g(1);
      bus(G, 210, 1460, Y, C.navy, "barramento CA", { lx: 1460, ly: Y - 18 });
      G = g(2);
      const u = [
        [360, [["=", "="], ["=", "~"]], "pv", "FV"],
        [580, [["=", "~"]], "battery", "bateria"],
        [800, [["~", "="], ["=", "~"]], "wind", "eólica"],
      ].map(([x, ch, ic, l]) => [x, unit(G, x, Y, ch, ic, { label: l }).n]);
      G = g(3);
      const v = [
        [1040, [], "house", "carga CA"],
        [1260, [["~", "="]], "dcload", "carga CC"],
      ].map(([x, ch, ic, l]) => [x, unit(G, x, Y, ch, ic, { label: l }).n]);
      G = g(4);
      [...u, ...v].forEach(([x, n]) => badge(G, x + 52, Y + 40, n));
      note(G, "nº de conversões até o barramento: cada uma custa perdas", 1460, 500, { anchor: "end", size: 22 });
    },
    "arq-cc"(svg, g) {
      const Y = arqFrame(svg);
      let G = g(1);
      wire(G, [[210, Y], [232, Y]]);
      conv(G, 265, Y, "~", "=", 60, { color: C.dc });
      bus(G, 298, 1460, Y, C.dc, "barramento CC", { lx: 1460, ly: Y - 18 });
      G = g(2);
      const u = [
        [420, [["=", "="]], "pv", "FV"],
        [620, [["=", "="]], "battery", "bateria"],
        [820, [["~", "="]], "wind", "eólica"],
      ].map(([x, ch, ic, l]) => [x, unit(G, x, Y, ch, ic, { label: l }).n]);
      G = g(3);
      const v = [
        [1040, [["=", "~"]], "house", "carga CA"],
        [1260, [], "dcload", "carga CC"],
      ].map(([x, ch, ic, l]) => [x, unit(G, x, Y, ch, ic, { label: l }).n]);
      G = g(4);
      [...u, ...v].forEach(([x, n]) => badge(G, x + 52, Y + 40, n));
      badge(G, 265, Y - 52, 1);
      note(G, "sem frequência nem reativo; mas proteção CC é mais difícil", 1460, 500, { anchor: "end", size: 22 });
    },
    "arq-hibrida"(svg, g) {
      const Y = arqFrame(svg);
      let G = g(1);
      bus(G, 210, 690, Y, C.navy, "barramento CA", { lx: 690, ly: Y - 18 });
      unit(G, 360, Y, [], "gen", { label: "diesel" });
      unit(G, 560, Y, [], "house", { label: "carga CA" });
      G = g(2);
      bus(G, 910, 1460, Y, C.dc, "barramento CC", { lx: 1460, ly: Y - 18 });
      unit(G, 1010, Y, [["=", "="]], "pv", { label: "FV" });
      unit(G, 1190, Y, [["=", "="]], "battery", { label: "bateria" });
      unit(G, 1370, Y, [], "dcload", { label: "carga CC" });
      G = g(3);
      wire(G, [[690, Y], [760, Y]]); wire(G, [[840, Y], [910, Y]]);
      conv(G, 800, Y, "~", "=", 80, { color: C.rose, sw: 4 });
      txt(G, "conversor de interligação", 800, Y + 80, { family: SERIF, italic: true, size: 24, color: C.rose });
      txt(G, "(ILC)", 800, Y + 110, { family: SERIF, italic: true, size: 24, color: C.rose });
      note(G, "cada fonte e carga no barramento mais natural", 800, 500, { color: C.navy });
    },

    // ---------------- seguidor × formador de rede ----------------
    "gfl-gfm"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 560");
      path(svg, "M750,20 V540", { color: C.rule, w: 2 });
      let G = g(1);
      title(G, "Seguidor de rede", 375, 40);
      txt(G, "grid-following", 375, 72, { family: SERIF, italic: true, size: 22, color: C.muted });
      vbus(G, 640, 128, 470, C.navy);
      cap(G, "rede (v)", 660, 470, { anchor: "start", color: C.navy, weight: 600, size: 18 });
      source(G, 330, 380, 42, "i");
      wire(G, [[330, 338], [330, 250], [640, 250]]);
      wire(G, [[330, 422], [330, 450]]); ground(G, 330, 450);
      math(G, "i = i*", 390, 390, { anchor: "start", size: 28 });
      box(G, 200, 115, 240, 56, ["P*, Q* → i*"], { size: 22 });
      box(G, 490, 115, 110, 56, ["PLL"], { size: 22 });
      darrow(G, [[640, 143], [602, 143]], C.navy);
      arrow(G, [[490, 143], [442, 143]], C.navy);
      cap(G, "θ", 466, 132, { color: C.navy });
      arrow(G, [[200, 143], [160, 143], [160, 380], [286, 380]], C.navy);
      cap(G, "fonte de corrente sincronizada (PLL):", 375, 505, { size: 20, color: C.ink });
      cap(G, "precisa de uma tensão já existente", 375, 533, { size: 19 });
      G = g(2);
      title(G, "Formador de rede", 1125, 40);
      txt(G, "grid-forming", 1125, 72, { family: SERIF, italic: true, size: 22, color: C.muted });
      vbus(G, 1400, 128, 470, C.navy);
      cap(G, "barramento", 1390, 500, { anchor: "end", color: C.navy, weight: 600, size: 18 });
      source(G, 900, 380, 42, "v");
      math(G, "E∠δ", 955, 400, { anchor: "start" });
      wire(G, [[900, 338], [900, 250], [1000, 250]]);
      coil(G, 1000, 1120, 250);
      math(G, "X", 1060, 225, { size: 26 });
      wire(G, [[1120, 250], [1400, 250]]);
      wire(G, [[900, 422], [900, 450]]); ground(G, 900, 450);
      box(G, 940, 115, 300, 56, ["ω*, E* → droop → ω, E"], { size: 21 });
      darrow(G, [[1400, 143], [1242, 143]], C.navy);
      cap(G, "P, Q", 1320, 132, { color: C.navy });
      arrow(G, [[940, 143], [800, 143], [800, 380], [856, 380]], C.navy);
      cap(G, "fonte de tensão: define V e f", 1125, 505, { size: 20, color: C.ink });
      cap(G, "indispensável no modo ilhado", 1125, 533, { size: 19 });
    },

    // ---------------- duas fontes e uma linha indutiva ----------------
    "circuito-linha"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 420");
      let G = g(1);
      source(G, 300, 250, 50, "v");
      math(G, "E∠δ", 225, 262, { anchor: "end", size: 36, color: "#D2457E" });
      wire(G, [[300, 200], [300, 140], [620, 140]]);
      coil(G, 620, 860, 140, 6);
      math(G, "jX", 740, 105, { size: 36, color: "#3A6EDB" });
      cap(G, "linha indutiva (R ≪ X)", 740, 190);
      wire(G, [[860, 140], [1200, 140], [1200, 200]]);
      source(G, 1200, 250, 50, "v");
      math(G, "V∠0", 1275, 262, { anchor: "start", size: 36 });
      wire(G, [[300, 300], [300, 360], [1200, 360], [1200, 300]]);
      G = g(2);
      arrow(G, [[400, 112], [540, 112]], C.rose);
      math(G, "I", 470, 96, { color: C.rose });
      arrow(G, [[930, 112], [1110, 112]], C.flow);
      math(G, "S = P + jQ", 1020, 96, { color: C.flow, size: 28 });
      
    },

    // ---------------- curva de droop ----------------
    "droop-curva"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 560");
      const X0 = 170, Y0 = 470, ys = 100, ymin = 400;
      const P1 = (y) => X0 + ((y - ys) / (ymin - ys)) * 1000, P2 = (y) => X0 + ((y - ys) / (ymin - ys)) * 500;
      let G = g(1);
      arrow(G, [[X0, Y0], [1330, Y0]], C.ink, 2.4); math(G, "P", 1350, Y0 + 10, { anchor: "start" });
      arrow(G, [[X0, Y0], [X0, 40]], C.ink, 2.4); math(G, "ω", X0 - 18, 50, { anchor: "end" });
      dashed(G, [[X0, ys], [1300, ys]], C.muted, 1.8); math(G, "ω*", X0 - 14, ys + 10, { anchor: "end", size: 26 });
      dashed(G, [[X0, ymin], [1300, ymin]], C.muted, 1.8); math(G, "ω_{min}", X0 - 14, ymin + 10, { anchor: "end", size: 26 });
      wire(G, [[X0, ys], [P1(ymin), ymin]], C.blue, 4);
      cap(G, "unidade 1", P1(ymin) + 14, ymin - 10, { anchor: "start", color: C.blue, weight: 600, size: 20 });
      math(G, "inclinação −m_p", 1010, 318, { anchor: "start", size: 26, color: C.blue });
      const yA = 190;
      dot(G, P1(yA), yA, 9, C.blue);
      dashed(G, [[P1(yA), yA], [P1(yA), Y0]], C.muted, 1.5);
      G = g(2);
      const yB = 280;
      arrow(G, [[P1(yA) + 24, yA + 4], [P1(yB) - 6, yB - 22]], C.rose, 3);
      dot(G, P1(yB), yB, 9, C.blue);
      note(G, "mais carga ⇒ frequência menor", 600, 172, { anchor: "start", size: 26 });
      G = g(3);
      wire(G, [[X0, ys], [P2(ymin), ymin]], C.flow, 4);
      cap(G, "unidade 2", P2(ymin) - 14, ymin + 32, { anchor: "end", color: C.flow, weight: 600, size: 20 });
      dashed(G, [[X0, yB], [1250, yB]], C.rose, 2);
      dot(G, P2(yB), yB, 9, C.flow); dot(G, P1(yB), yB, 9, C.blue);
      dashed(G, [[P2(yB), yB], [P2(yB), Y0]], C.flow, 1.8);
      dashed(G, [[P1(yB), yB], [P1(yB), Y0]], C.blue, 1.8);
      math(G, "P_2", P2(yB), Y0 + 40, { color: C.flow }); math(G, "P_1", P1(yB), Y0 + 40, { color: C.blue });
      note(G, "mesma ω em toda a rede ⇒ P_1 = 2 P_2", 1250, 255, { anchor: "end", size: 26, color: C.navy });
    },

    // ---------------- diagrama de blocos do droop ----------------
    "droop-blocos"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 520");
      let G = g(1);
      box(G, 40, 200, 190, 140, ["p, q", "potência", "instantânea"], { italic: true, gap: 26 });
      box(G, 310, 140, 170, 80, ["filtro", "ω_c/(s+ω_c)"], { size: 22, gap: 26 });
      box(G, 310, 320, 170, 80, ["filtro", "ω_c/(s+ω_c)"], { size: 22, gap: 26 });
      arrow(G, [[230, 240], [270, 240], [270, 180], [310, 180]]);
      arrow(G, [[230, 300], [270, 300], [270, 360], [310, 360]]);
      G = g(2);
      box(G, 560, 140, 230, 80, ["ω = ω* − m_p P"], { italic: true, size: 25 });
      box(G, 560, 320, 230, 80, ["E = E* − n_q Q"], { italic: true, size: 25 });
      arrow(G, [[480, 180], [560, 180]]); math(G, "P", 520, 168, { size: 24 });
      arrow(G, [[480, 360], [560, 360]]); math(G, "Q", 520, 348, { size: 24 });
      G = g(3);
      box(G, 860, 140, 80, 80, ["∫"], { size: 34 });
      arrow(G, [[790, 180], [860, 180]]); math(G, "ω", 825, 168, { size: 24 });
      box(G, 960, 240, 260, 80, ["v* = E sin(ω t + δ)"], { italic: true, size: 23 });
      arrow(G, [[940, 180], [1090, 180], [1090, 240]]); math(G, "δ", 1010, 168, { size: 24 });
      arrow(G, [[790, 360], [1090, 360], [1090, 320]]); math(G, "E", 940, 348, { size: 24 });
      G = g(4);
      box(G, 1280, 230, 190, 100, ["nível 0", "malhas V/I + PWM"], { size: 22 });
      arrow(G, [[1220, 280], [1280, 280]]);
      arrow(G, [[1375, 330], [1375, 470], [135, 470], [135, 340]], C.navy);
      cap(G, "tensão e corrente de saída medidas", 760, 500, { color: C.navy });
      note(G, "malha de potência: lenta (filtro)", 560, 115, { anchor: "start", size: 22 });
    },

    // ---------------- hierarquia ----------------
    hierarquia(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 640");
      const ux = [60, 380, 700], tx = 1150;
      const lvl = (G, y, a, b, color = C.navy) => {
        cap(G, a, tx + 30, y, { anchor: "start", size: 22, color, weight: 600 });
        cap(G, b, tx + 30, y + 26, { anchor: "start", size: 18 });
      };
      let G = g(1);
      arrow(G, [[tx, 610], [tx, 50]], C.muted, 2.4);
      cap(G, "mais lento", tx - 14, 60, { anchor: "end", size: 16, color: C.muted });
      cap(G, "mais rápido", tx - 14, 610, { anchor: "end", size: 16, color: C.muted });
      bus(G, 60, 980, 620, C.navy);
      ux.forEach((x, i) => {
        el("rect", { x, y: 430, width: 280, height: 160, rx: 12, fill: "none", stroke: C.ink, "stroke-width": 2,
          class: "fade" }, G);
        box(G, x + 15, 515, 250, 60, ["nível 0: malhas V/I"], { sans: true, sub: 18, fill: "rgba(29,28,26,0.04)", color: C.ink });
        wire(G, [[x + 140, 590], [x + 140, 620]]);
      });
      lvl(G, 545, "Nível 0  ·  μs – ms", "malhas internas de tensão e corrente");
      G = g(2);
      ux.forEach((x) => box(G, x + 15, 445, 250, 60, ["primário: droop"], { sans: true, sub: 18 }));
      lvl(G, 465, "Primário  ·  ms – s", "partilha de potência sem comunicação");
      G = g(3);
      box(G, 260, 250, 520, 80, ["secundário (MGCC)", "restaura ω e E nominais"], { size: 24 });
      ux.forEach((x) => darrow(G, [[520, 330], [x + 140, 428]]));
      note(G, "δω, δE", 560, 395, { anchor: "start", size: 22 });
      lvl(G, 280, "Secundário  ·  s – min", "corrige os desvios do droop");
      G = g(4);
      box(G, 260, 60, 520, 80, ["terciário", "intercâmbio com a rede, despacho econômico"], { size: 24 });
      arrow(G, [[520, 140], [520, 250]], C.navy);
      math(G, "ω*, E*", 535, 205, { anchor: "start", size: 24, color: C.navy });
      lvl(G, 92, "Terciário  ·  min – h", "otimização, mercado");
    },

    // ---------------- nível 0: malhas internas ----------------
    nivel0(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 420");
      const Y = 180;
      let G = g(1);
      sum(G, 450, Y, { left: "+", bottom: "−" });
      arrow(G, [[380, Y], [428, Y]]); math(G, "i*", 395, Y - 16, { size: 24 });
      arrow(G, [[472, Y], [530, Y]]);
      box(G, 530, Y - 40, 140, 80, ["PI_i"], { italic: true });
      arrow(G, [[670, Y], [740, Y]]); math(G, "u", 705, Y - 16, { size: 24 });
      box(G, 740, Y - 40, 180, 80, ["PWM + ponte"], { size: 22 });
      arrow(G, [[920, Y], [1010, Y]]); math(G, "i_L", 965, Y - 16, { size: 24 });
      box(G, 1010, Y - 40, 180, 80, ["filtro LC"], { size: 22 });
      dot(G, 960, Y, 6);
      arrow(G, [[960, Y], [960, 290], [450, 290], [450, Y + 22]], C.rose);
      cap(G, "corrente medida", 700, 316, { color: C.rose });
      G = g(2);
      sum(G, 110, Y, { left: "+", bottom: "−" });
      arrow(G, [[20, Y], [88, Y]]); math(G, "v*", 40, Y - 16, { size: 24 });
      arrow(G, [[132, Y], [200, Y]]);
      box(G, 200, Y - 40, 140, 80, ["PI_v"], { italic: true });
      wire(G, [[340, Y], [380, Y]]);
      arrow(G, [[1190, Y], [1440, Y]]); math(G, "v_o", 1400, Y - 16, { size: 24 });
      dot(G, 1300, Y, 6);
      arrow(G, [[1300, Y], [1300, 370], [110, 370], [110, Y + 22]], C.navy);
      cap(G, "tensão medida", 700, 396, { color: C.navy });
      G = g(3);
      note(G, "malha interna (corrente): rápida, ~ kHz", 860, 70);
      note(G, "malha externa (tensão): ~10× mais lenta", 300, 70, { color: C.navy });
    },

    // ---------------- nível 1: droop em cada unidade ----------------
    nivel1(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 500");
      const YB = 450, yw = 175;
      bus(svg, 100, 1400, YB, C.navy, "barramento CA (mesma frequência)", { lx: 750, ly: YB + 40, anchor: "middle" });
      const plot = (G, x0, slope, color, name, k) => {
        const Y0 = 270, ys = 90;
        arrow(G, [[x0, Y0], [x0 + 300, Y0]], C.ink, 2); math(G, "P", x0 + 310, Y0 + 8, { anchor: "start", size: 24 });
        arrow(G, [[x0, Y0], [x0, 60]], C.ink, 2); math(G, "ω", x0 - 12, 70, { anchor: "end", size: 24 });
        dashed(G, [[x0, ys], [x0 + 280, ys]], C.muted, 1.5); math(G, "ω*", x0 - 10, ys + 8, { anchor: "end", size: 22 });
        wire(G, [[x0, ys], [x0 + slope, 250]], color, 4);
        cap(G, name, x0 + 150, 40, { color, weight: 600 });
        const xp = x0 + ((yw - ys) / (250 - ys)) * slope;
        wire(G, [[x0 + 150, 300], [x0 + 150, 350]]);
        conv(G, x0 + 150, 378, "=", "~", 56);
        wire(G, [[x0 + 150, 406], [x0 + 150, YB]]);
        return xp;
      };
      let G = g(1);
      const xa = plot(G, 220, 270, C.blue, "unidade A (maior)");
      G = g(2);
      const xb = plot(G, 980, 150, C.flow, "unidade B (menor)");
      G = g(3);
      dashed(G, [[220, yw], [1260, yw]], C.rose, 2);
      dot(G, xa, yw, 8, C.blue); dot(G, xb, yw, 8, C.flow);
      dashed(G, [[xa, yw], [xa, 270]], C.blue, 1.6); dashed(G, [[xb, yw], [xb, 270]], C.flow, 1.6);
      ["cada unidade mede a", "frequência local e ajusta P", "pela sua reta: sem", "comunicação"]
        .forEach((s, i) => note(G, s, 750, 230 + i * 32, { size: 23, color: C.navy }));
    },

    // ---------------- nível 2: secundário ----------------
    nivel2(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 520");
      const YB = 470, xs = [260, 600, 940];
      let G = g(1);
      bus(G, 80, 1440, YB, C.navy);
      xs.forEach((x) => {
        box(G, x - 150, 270, 300, 60, ["ω = ω* − m_p P + δω"], { italic: true, size: 22 });
        wire(G, [[x, 330], [x, 372]]);
        conv(G, x, 400, "=", "~", 56);
        wire(G, [[x, 428], [x, YB]]);
      });
      G = g(2);
      box(G, 1120, 60, 330, 150, ["secundário (MGCC)", "δω = k_p e_ω + k_i ∫ e_ω", "e_ω = ω* − ω_{MG}"], { size: 24, gap: 36 });
      arrow(G, [[1380, YB], [1380, 210]], C.navy);
      cap(G, "mede ω_{MG}, E_{MG}", 1370, 360, { anchor: "end", color: C.navy });
      G = g(3);
      dashed(G, [[1120, 135], [xs[0], 135]]);
      xs.forEach((x) => darrow(G, [[x, 135], [x, 268]]));
      note(G, "δω, δE — comunicação lenta, de baixa banda", 600, 115, { size: 22 });
    },

    // ---------------- nível 3: terciário ----------------
    nivel3(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 440");
      const Y = 320;
      let G = g(1);
      tower(G, 100, 180, 200);
      cap(G, "rede principal", 100, 410);
      wire(G, [[125, Y], [300, Y]]);
      sw(G, 330, Y);
      txt(G, "PCC", 330, Y + 44, { size: 18, weight: 700, color: C.rose });
      wire(G, [[360, Y], [540, Y]]);
      el("circle", { cx: 450, cy: Y, r: 11, fill: C.paper, stroke: C.navy, "stroke-width": 2.5, class: "fade" }, G);
      box(G, 540, 250, 440, 140, ["microrrede", "níveis 0, 1 e 2"], { size: 28 });
      G = g(2);
      box(G, 1080, 250, 380, 140, ["terciário", "P_{G}* − P_G → ω*", "Q_{G}* − Q_G → E*"], { size: 26, gap: 34 });
      darrow(G, [[450, Y - 12], [450, 190], [1180, 190], [1180, 248]], C.navy);
      cap(G, "P_G, Q_G medidos no PCC", 800, 176, { color: C.navy });
      arrow(G, [[1080, Y], [982, Y]], C.navy);
      math(G, "ω*, E*", 1030, Y - 12, { size: 22, color: C.navy });
      G = g(3);
      box(G, 1230, 30, 230, 90, ["despacho", "operador, mercado"], { size: 24 });
      arrow(G, [[1345, 120], [1345, 248]], C.rose);
      math(G, "P_{G}*, Q_{G}*", 1360, 185, { anchor: "start", size: 22, color: C.rose });
    },

    // ---------------- impedância virtual ----------------
    "impedancia-virtual"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 460");
      const Y = 170;
      let G = g(1);
      box(G, 40, Y - 45, 230, 90, ["droop", "ω, E → v*"], { size: 24 });
      arrow(G, [[270, Y], [478, Y]]); math(G, "v*", 370, Y - 16, { size: 24 });
      sum(G, 500, Y, { left: "+", bottom: "−" });
      arrow(G, [[522, Y], [640, Y]]); math(G, "v_{ref}", 580, Y - 16, { size: 24 });
      box(G, 640, Y - 45, 240, 90, ["nível 0", "malhas V/I + PWM"], { size: 24 });
      arrow(G, [[880, Y], [1000, Y]]);
      conv(G, 1040, Y, "=", "~", 76);
      wire(G, [[1078, Y], [1300, Y]]);
      vbus(G, 1320, 80, 260);
      G = g(2);
      dot(G, 1200, Y, 6);
      arrow(G, [[1200, Y], [1200, 340], [880, 340]], C.rose);
      math(G, "i_o", 1215, 260, { anchor: "start", size: 24, color: C.rose });
      box(G, 640, 295, 240, 90, ["Z_v(s) = R_v + s L_v"], { italic: true, size: 23, color: C.rose, fill: "rgba(166,61,74,0.06)" });
      arrow(G, [[640, 340], [500, 340], [500, Y + 22]], C.rose);
      G = g(3);
      ["a saída “parece” ter uma", "impedância indutiva R_v + j ω L_v"]
        .forEach((t, i) => note(G, t, 960, 412 + i * 34, { anchor: "start", size: 23 }));
    },
  };

  const buildAll = () => {
    let n = 0;
    document.querySelectorAll("[data-nova-diagram]:not(.built)").forEach((host) => {
      const make = DIAGRAMS[host.dataset.novaDiagram];
      if (!make) return;
      host.classList.add("built");
      const svg = el("svg", { role: "img", "aria-label": host.dataset.novaDiagram }, host);
      const g = (i) => el("g", { class: "fragment draw", "data-fragment-index": i }, svg);
      make(svg, g);
      n++;
    });
    return n;
  };
  buildAll();
  window.addEventListener("load", () => {
    if (buildAll() && window.Reveal && Reveal.isReady && Reveal.isReady()) Reveal.sync();
  });
})();
