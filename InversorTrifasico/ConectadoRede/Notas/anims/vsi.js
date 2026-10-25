/* =====================================================================
   Diagramas do VSI na bancada (SVG + fragmentos), no padrão de
   NovaPresent/anims/diagramas.js e MicroGrids/Notas/anims/microrredes.js:
   cada etapa é um fragmento do revealjs (traços "se desenham", rótulos surgem).

   Uso (o <script> uma vez por deck, no fim):
     ::: {.nova-svg data-nova-diagram="bancada"}
     :::
     <script src="anims/vsi.js"></script>

   Diagramas: bancada, vsi-circuito, amostragem, atraso, tempo-morto,
   modelo-firmware, modelo-simples
   ===================================================================== */
(function () {
  "use strict";

  const C = { ink: "#1D1C1A", muted: "#77736A", grey: "#5F6368", rule: "#DDD7CB", navy: "#1B365D",
    rose: "#A63D4A", paper: "#F7F5F0", flow: "#D27A22", green: "#2E9C6B", blue: "#3A6EDB" };
  const SERIF = '"Source Serif 4", Georgia, serif', SANS = '"Inter", sans-serif';
  const NS = "http://www.w3.org/2000/svg";

  // ---------------------------------------------------------------
  // Primitivas
  // ---------------------------------------------------------------
  const el = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  };
  // Texto; "v_{aO}" e "S_a" viram subscritos
  function txt(p, s, x, y, o = {}) {
    const t = el("text", { x, y, "text-anchor": o.anchor || "middle", fill: o.color || C.ink,
      "font-family": o.family || SANS, "font-size": o.size || 20, "font-style": o.italic ? "italic" : "normal",
      "font-weight": o.weight || 400, class: "fade" }, p);
    let down = false;
    String(s).split(/(_\{[^}]*\}|_[\w+−-]+)/).forEach((part) => {
      if (!part) return;
      const sub = part.match(/^_\{?([^}]*)\}?$/);
      const ts = el("tspan", sub ? { dy: "0.3em", "font-size": "72%" } : down ? { dy: "-0.3em" } : {}, t);
      ts.textContent = sub ? sub[1] : part;
      down = !!sub;
    });
    return t;
  }
  const math = (p, s, x, y, o = {}) => txt(p, s, x, y, { family: SERIF, italic: true, size: 28, ...o });
  const note = (p, s, x, y, o = {}) => txt(p, s, x, y, { family: SERIF, italic: true, size: 24, color: C.rose, ...o });
  const cap = (p, s, x, y, o = {}) => txt(p, s, x, y, { size: 18, color: C.grey, ...o });

  const ink = (p, d, color = C.ink, w = 3) => el("path", { d, fill: "none", stroke: color, "stroke-width": w,
    "stroke-linecap": "round", "stroke-linejoin": "round", pathLength: 1, class: "ink" }, p);
  const poly = (pts) => "M" + pts.map((q) => q.join(",")).join(" L");
  const wire = (p, pts, color = C.ink, w = 3) => ink(p, poly(pts), color, w);
  const path = (p, d, o = {}) => el("path", { d, fill: o.fill || "none", stroke: o.color || C.ink,
    "stroke-width": o.w || 2.5, "stroke-linecap": "round", "stroke-linejoin": "round",
    ...(o.dash ? { "stroke-dasharray": o.dash } : {}), class: "fade" }, p);
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
  const dot = (p, x, y, r = 6, color = C.ink) => el("circle", { cx: x, cy: y, r, fill: color, class: "fade" }, p);
  const rect = (p, x, y, w, h, o = {}) => el("rect", { x, y, width: w, height: h, rx: o.rx ?? 0,
    fill: o.fill || "none", stroke: o.stroke || "none", "stroke-width": o.sw || 0, class: "fade" }, p);

  // caixa: 1ª linha em serifa (título), demais em sans cinza
  function box(p, x, y, w, h, lines, o = {}) {
    const col = o.color || C.navy;
    el("rect", { x, y, width: w, height: h, rx: 10, fill: o.fill || "rgba(27,54,93,0.06)", stroke: col,
      "stroke-width": o.sw || 2.5, class: "fade" }, p);
    const L = [].concat(lines), gap = o.gap || 30;
    const y0 = y + h / 2 - ((L.length - 1) * gap) / 2 + 8;
    L.forEach((s, i) => {
      if (i === 0) txt(p, s, x + w / 2, y0, { family: SERIF, size: o.size || 26, color: col, weight: o.weight || 600 });
      else txt(p, s, x + w / 2, y0 + i * gap, { size: o.sub || 18, color: C.grey });
    });
  }

  // chave ideal vertical entre (x, y1) e (x, y2), lâmina aberta
  function chave(p, x, y1, y2, label) {
    const a = y1 + (y2 - y1) * 0.32, b = y1 + (y2 - y1) * 0.68;
    wire(p, [[x, y1], [x, a]]);
    wire(p, [[x, a], [x + 26, b - 6]]);
    wire(p, [[x, b], [x, y2]]);
    dot(p, x, a, 4); dot(p, x, b, 4);
    if (label) math(p, label, x - 18, (y1 + y2) / 2 + 8, { anchor: "end", size: 24 });
  }
  // fonte CC vertical centrada em (x, y): placas longa (+) e curta
  function fonte(p, x, y, label) {
    wire(p, [[x, y - 60], [x, y - 10]]);
    path(p, `M${x - 30},${y - 10} H${x + 30}`, { w: 3.5 });
    path(p, `M${x - 16},${y + 6} H${x + 16}`, { w: 6 });
    wire(p, [[x, y + 6], [x, y + 60]]);
    txt(p, "+", x + 42, y - 14, { size: 22 });
    if (label) math(p, label, x - 44, y + 8, { anchor: "end", size: 24 });
  }
  // resistor horizontal (zigue-zague) de x0 a x0+L
  function resistor(p, x0, y, L = 90) {
    const n = 6, s = L / n, pts = [[x0, y]];
    for (let i = 0; i < n; i++) pts.push([x0 + s * (i + 0.5), y + (i % 2 ? 12 : -12)]);
    pts.push([x0 + L, y]);
    wire(p, pts, C.ink, 2.6);
  }
  // indutor horizontal (4 espiras) de x0 a x0+L
  function indutor(p, x0, y, L = 100) {
    const r = L / 8;
    let d = `M${x0},${y}`;
    for (let i = 0; i < 4; i++) d += ` a${r},${r} 0 0 1 ${2 * r},0`;
    ink(p, d, C.ink, 2.6);
  }
  // forma de onda digital: lista de [x, nível], nível 0/1, entre yLo e yHi
  function digital(p, segs, yLo, yHi, color = C.ink, w = 3) {
    const pts = [];
    segs.forEach(([x, lv], i) => {
      const y = lv ? yHi : yLo;
      if (i > 0) pts.push([x, pts[pts.length - 1][1]]);
      pts.push([x, y]);
    });
    wire(p, pts, color, w);
  }

  // ---------------------------------------------------------------
  // Diagramas
  // ---------------------------------------------------------------
  const DIAGRAMS = {
    // ---------------- a bancada ----------------
    bancada(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 560");
      let G = g(1);
      box(G, 20, 70, 190, 110, ["PC", "Code Composer", "Studio · USB"], { size: 26, gap: 26 });
      arrow(G, [[210, 125], [288, 125]], C.navy);
      box(G, 290, 30, 400, 320, ["LAUNCHXL-F28379D", "C28x 200 MHz · FPU · TMU", "ePWM 1–3 (relógio de 100 MHz)",
        "4 ADC de 12 bits", "CMPSS · trip zone · CLA"], { size: 27, gap: 46 });
      G = g(2);
      box(G, 830, 30, 400, 320, ["BOOSTXL-3PHGANINV", "3 × LMG5200 (GaN 80 V / 10 A)", "shunt 5 mΩ + INA240 (× 20)",
        "divisores (81,5 V) + RC 1,1 kHz", "/EN ativo baixo · OCP 12 A"], { size: 27, gap: 46 });
      arrow(G, [[690, 130], [828, 130]], C.navy, 3.5);
      cap(G, "6 PWM", 760, 116, { color: C.navy, weight: 600 });
      arrow(G, [[690, 180], [828, 180]], C.rose, 2.5);
      cap(G, "/EN (GPIO124)", 760, 168, { color: C.rose, size: 16 });
      box(G, 880, 440, 300, 90, ["fonte CC", "V_{cc} = 40 V"], { size: 26, color: C.ink, fill: "rgba(29,28,26,0.04)" });
      arrow(G, [[1030, 440], [1030, 352]], C.ink, 3);
      G = g(3);
      [120, 190, 260].forEach((y, i) => {
        wire(G, [[1230, y], [1300, y]], C.ink, 3);
        cap(G, "abc"[i], 1265, y - 10, { size: 17 });
      });
      box(G, 1300, 70, 185, 240, ["carga RL", "em Y", "R = 10 Ω", "L = 5 mH"], { size: 26, color: C.ink,
        fill: "rgba(29,28,26,0.04)", gap: 34 });
      G = g(4);
      darrow(G, [[828, 290], [692, 290]], C.green, 2.6);
      cap(G, "I_A, I_B, I_C · V_A, V_B, V_C · V_{DC} → ADC", 490, 390, { color: C.green, size: 19, weight: 600 });
      note(G, "amostradas no início de cada período de PWM", 490, 424, { color: C.green, size: 22 });
    },

    // ---------------- circuito do VSI de dois níveis ----------------
    "vsi-circuito"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 560");
      const P = 70, O = 280, N = 490, xs = [380, 600, 820];
      let G = g(1);
      fonte(G, 130, (P + O) / 2, "V_{cc}/2");
      fonte(G, 130, (O + N) / 2, "V_{cc}/2");
      wire(G, [[130, P], [130, P + 45]]); wire(G, [[130, O - 45], [130, O + 45]]); wire(G, [[130, N - 45], [130, N]]);
      wire(G, [[130, P], [900, P]], C.navy, 4);
      wire(G, [[130, N], [900, N]], C.navy, 4);
      dot(G, 130, O, 7);
      txt(G, "O", 108, O + 8, { family: SERIF, size: 26, weight: 600, anchor: "end" });
      cap(G, "P", 912, P + 6, { anchor: "start", weight: 600, color: C.navy });
      cap(G, "N", 912, N + 6, { anchor: "start", weight: 600, color: C.navy });
      xs.forEach((x, i) => {
        const f = "abc"[i];
        dot(G, x, P, 5); dot(G, x, N, 5);
        chave(G, x, P, O, `S_{${f}+}`);
        chave(G, x, O, N, `S_{${f}−}`);
        dot(G, x, O, 7);
        wire(G, [[x, O], [x + 60, O]]);
        el("circle", { cx: x + 68, cy: O, r: 8, fill: C.paper, stroke: C.ink, "stroke-width": 2.5, class: "fade" }, G);
        math(G, f, x + 68, O - 18, { size: 26, color: C.navy });
      });
      G = g(2);
      const yl = [170, 280, 390], xn = 1420;
      yl.forEach((y, i) => {
        const f = "abc"[i];
        el("circle", { cx: 1010, cy: y, r: 8, fill: C.paper, stroke: C.ink, "stroke-width": 2.5, class: "fade" }, G);
        math(G, f, 990, y + 8, { anchor: "end", size: 26, color: C.navy });
        wire(G, [[1018, y], [1050, y]], C.ink, 2.6);
        resistor(G, 1050, y, 90);
        wire(G, [[1140, y], [1160, y]], C.ink, 2.6);
        indutor(G, 1160, y, 100);
        wire(G, [[1260, y], [1330, y], [xn, 280]], C.ink, 2.6);
      });
      dot(G, xn, 280, 7);
      math(G, "n", xn + 18, 288, { anchor: "start", size: 26 });
      cap(G, "R = 10 Ω", 1095, 120, { size: 17 });
      cap(G, "L = 5 mH", 1210, 120, { size: 17 });
      arrow(G, [[1290, 150], [1325, 150]], C.rose, 2.4);
      math(G, "i_a", 1308, 138, { size: 22, color: C.rose });
      G = g(3);
      note(G, "v_{aO}: perna a em relação ao ponto médio O do barramento", 1180, 470, { size: 23 });
      note(G, "v_{an} = v_{aO} − v_{nO}: tensão na fase a da carga", 1180, 510, { size: 23 });
    },

    // ---------------- amostragem no início do período ----------------
    amostragem(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 560");
      const x0 = 120, T = 620, y0 = 250, yP = 60, d = 0.3;
      const cy = (v) => y0 - (y0 - yP) * v;      // v = CTR/TBPRD
      let G = g(1);
      path(G, `M${x0 - 20},${y0} H${x0 + 2 * T + 30}`, { color: C.rule, w: 2 });
      wire(G, [[x0, y0], [x0 + T / 2, yP], [x0 + T, y0], [x0 + 1.5 * T, yP], [x0 + 2 * T, y0]], C.navy, 3);
      path(G, `M${x0 - 20},${cy(d)} H${x0 + 2 * T + 30}`, { color: C.rose, w: 2.2, dash: "8 6" });
      cap(G, "CMPA", x0 + 2 * T + 40, cy(d) + 6, { anchor: "start", color: C.rose, weight: 600 });
      cap(G, "TBCTR (sobe e desce)", x0 + T / 2, yP - 16, { color: C.navy, weight: 600 });
      G = g(2);
      const yLo = 380, yHi = 320, h = d * T / 2;
      digital(G, [[x0, 1], [x0 + h, 0], [x0 + T - h, 1], [x0 + T + h, 0], [x0 + 2 * T - h, 1], [x0 + 2 * T, 1]], yLo, yHi, C.ink, 3);
      cap(G, "EPWMxA", x0 - 20, (yLo + yHi) / 2 + 6, { anchor: "end", weight: 600, color: C.ink });
      cap(G, "chave de cima ligada enquanto TBCTR < CMPA", x0 + T, yLo + 34, { size: 17 });
      G = g(3);
      [x0, x0 + T, x0 + 2 * T].forEach((x) => {
        path(G, `M${x},${yP - 10} V${yLo + 50}`, { color: C.green, w: 2, dash: "4 5" });
        dot(G, x, y0, 8, C.green);
      });
      cap(G, "CTR = 0: ADC + ISR", x0 + T, yLo + 76, { color: C.green, weight: 600 });
      G = g(4);
      const xs = x0 + T, xe = x0 + T + h;
      path(G, `M${xs},${yHi - 30} H${xe}`, { color: C.rose, w: 2.4 });
      path(G, `M${xs},${yHi - 40} V${yHi - 20} M${xe},${yHi - 40} V${yHi - 20}`, { color: C.rose, w: 2.4 });
      math(G, "d T_s/2", (xs + xe) / 2, yHi - 44, { size: 22, color: C.rose });
      rect(G, xe, yHi, 0.04 * T, yLo - yHi, { fill: "rgba(166,61,74,0.18)" });
      note(G, "o INA240 precisa de ~2 µs após cada comutação:", 1000, 500, { size: 23, anchor: "middle" });
      note(G, "d T_s/2 ≥ 2 µs ⇒ d ≥ 0,08 a 20 kHz (0,16 a 40 kHz)", 1000, 536, { size: 23, anchor: "middle" });
    },

    // ---------------- atraso de implementação ----------------
    atraso(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 400");
      const ya = 250, xk = [200, 700, 1200];
      let G = g(1);
      arrow(G, [[100, ya], [1440, ya]], C.ink, 2.4);
      ["kT_s", "(k+1)T_s", "(k+2)T_s"].forEach((s, i) => {
        path(G, `M${xk[i]},${ya - 12} V${ya + 12}`, { w: 2.4 });
        math(G, s, xk[i], ya + 46, { size: 24 });
      });
      G = g(2);
      box(G, xk[0] - 10, 70, 260, 90, ["ISR k", "lê, calcula d_k, escreve CMPA"], { size: 24, sub: 16 });
      G = g(3);
      darrow(G, [[xk[0] + 250, 115], [xk[1], 115], [xk[1], ya - 16]], C.rose);
      cap(G, "sombra carregada no próximo CTR = 0", xk[0] + 270, 100, { color: C.rose, size: 17, anchor: "start" });
      G = g(4);
      rect(G, xk[1], ya - 70, xk[2] - xk[1], 56, { fill: "rgba(46,156,107,0.16)", stroke: C.green, sw: 2, rx: 6 });
      txt(G, "d_k aplicado em todo o período", (xk[1] + xk[2]) / 2, ya - 34, { size: 19, color: C.green, weight: 600 });
      dot(G, (xk[1] + xk[2]) / 2, ya, 8, C.green);
      math(G, "(k+1,5)T_s", (xk[1] + xk[2]) / 2, ya + 84, { size: 24, color: C.green });
      note(G, "atraso de 1,5 T_s = 75 µs: 1,6° a 60 Hz, 27° a 1 kHz", 750, 384, { size: 23 });
    },

    // ---------------- tempo morto ----------------
    "tempo-morto"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 580");
      const xu = 420, xd = 1000, td = 70, x0 = 260, x1 = 1380;
      const row = (G, label, y, segs, color = C.ink) => {
        digital(G, segs, y + 40, y, color, 3);
        txt(G, label, x0 - 24, y + 28, { anchor: "end", family: SERIF, italic: true, size: 24, color });
      };
      let G = g(1);
      row(G, "comando A", 30, [[x0, 0], [xu, 1], [xd, 0], [x1, 0]], C.grey);
      G = g(2);
      row(G, "S_{a+}", 120, [[x0, 0], [xu + td, 1], [xd, 0], [x1, 0]]);
      row(G, "S_{a−}", 210, [[x0, 1], [xu, 0], [xd + td, 1], [x1, 1]]);
      rect(G, xu, 110, td, 150, { fill: "rgba(166,61,74,0.10)" });
      rect(G, xd, 110, td, 150, { fill: "rgba(166,61,74,0.10)" });
      math(G, "t_m", xu + td / 2, 106, { size: 22, color: C.rose });
      math(G, "t_m", xd + td / 2, 106, { size: 22, color: C.rose });
      G = g(3);
      row(G, "v_{aO}, i > 0", 330, [[x0, 0], [xu + td, 1], [xd, 0], [x1, 0]], C.navy);
      rect(G, xu, 330, td, 40, { fill: "rgba(166,61,74,0.35)" });
      cap(G, "diodo de baixo conduz: perde t_m V_{cc}", xu + td + 20, 400, { anchor: "start", color: C.rose });
      G = g(4);
      row(G, "v_{aO}, i < 0", 440, [[x0, 0], [xu, 1], [xd + td, 0], [x1, 0]], C.navy);
      rect(G, xd, 440, td, 40, { fill: "rgba(46,156,107,0.35)" });
      cap(G, "diodo de cima conduz: ganha t_m V_{cc}", xd + td + 20, 510, { anchor: "start", color: C.green });
      note(G, "erro médio por período: −sinal(i) · t_m f_{PWM} V_{cc}", 750, 566, { size: 24 });
    },

    // ---------------- modelo fiel ao firmware ----------------
    "modelo-firmware"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 420");
      const y = 90, h = 130, w = 210, gap = 40, x = (i) => 10 + i * (w + gap);
      const blocos = [["LacoPWM", "ISR a cada T_s", "float de 32 bits"], ["Sombra", "atraso 1/z", "CMPA em CTR = 0"],
        ["ePWM", "contador · banda morta", "passo de 20 ns"], ["Inversor", "Two-Level", "Converter"],
        ["Medidor", "V-I trifásico", "i_{abc}, v_{xO}"], ["Carga", "RL em Y", "neutro isolado"]];
      let G = g(1);
      blocos.slice(0, 3).forEach((b, i) => box(G, x(i), y, w, h, b, { size: 25, gap: 30 }));
      [0, 1].forEach((i) => arrow(G, [[x(i) + w, y + h / 2], [x(i + 1) - 2, y + h / 2]], C.navy));
      cap(G, "espelho do código C (senoides.c, PWM2v)", x(1) + w / 2, y - 22, { color: C.navy, weight: 600 });
      G = g(2);
      blocos.slice(3).forEach((b, i) => box(G, x(i + 3), y, w, h, b, { size: 25, gap: 30, color: C.ink,
        fill: "rgba(29,28,26,0.04)" }));
      arrow(G, [[x(2) + w, y + h / 2], [x(3) - 2, y + h / 2]], C.navy);
      [3, 4].forEach((i) => wire(G, [[x(i) + w, y + h / 2], [x(i + 1), y + h / 2]], C.ink, 4));
      cap(G, "Specialized Power Systems", x(4) + w / 2, y - 22, { weight: 600 });
      G = g(3);
      box(G, x(3), 300, 2 * w + gap, 90, ["FiltroRC + ADC", "12 bits, amostra em CTR = 0"], { size: 24, color: C.green,
        fill: "rgba(46,156,107,0.06)" });
      arrow(G, [[x(4) + w / 2, y + h], [x(4) + w / 2, 298]], C.green);
      darrow(G, [[x(3), 345], [x(0) + w / 2, 345], [x(0) + w / 2, y + h + 2]], C.green);
      cap(G, "códigos do ADC: comparar com a placa (e realimentar no VSI02)", x(1) + w / 2 + 20, 372, { color: C.green });
    },

    // ---------------- modelo simples ----------------
    "modelo-simples"(svg, g) {
      svg.setAttribute("viewBox", "0 0 1500 320");
      const y = 90, h = 130, w = 210, gap = 40, x = (i) => 10 + i * (w + gap);
      const blocos = [["Referências", "V_p sen(ωt)", "três fases"], ["Normaliza", "ganho 2/V_{cc}", "u ∈ [−1, 1]"],
        ["PWM", "portadora 20 kHz", "amostragem natural"], ["Inversor", "Two-Level", "Converter"],
        ["Medidor", "V-I trifásico", "i_{abc}, v_{xO}"], ["Carga", "RL em Y", "neutro isolado"]];
      let G = g(1);
      blocos.slice(0, 3).forEach((b, i) => box(G, x(i), y, w, h, b, { size: 25, gap: 30 }));
      [0, 1, 2].forEach((i) => arrow(G, [[x(i) + w, y + h / 2], [x(i + 1) - 2, y + h / 2]], C.navy));
      blocos.slice(3).forEach((b, i) => box(G, x(i + 3), y, w, h, b, { size: 25, gap: 30, color: C.ink,
        fill: "rgba(29,28,26,0.04)" }));
      [3, 4].forEach((i) => wire(G, [[x(i) + w, y + h / 2], [x(i + 1), y + h / 2]], C.ink, 4));
      G = g(2);
      note(G, "sem tempo morto, sem atraso, sem ADC: o comportamento ideal do PWM senoidal", 750, 290, { size: 24 });
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
