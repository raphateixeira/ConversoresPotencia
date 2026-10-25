/* =====================================================================
   Animações em canvas para microrredes (base: nova-anim.js).

     "fasores"         linha indutiva: fasores E, V, jXI; P e Q exatos e
                       aproximados. Parâmetros: delta (graus), e (E/V), x (X em pu)
     "droop-partilha"  duas unidades com droop dividem um degrau de carga
                       na proporção das capacidades. Parâmetros: pl (carga
                       final, fração da capacidade total), r (P2max/P1max)
     "raizes-droop"    raízes de τs² + (1 + m_d K)s + m_p K = 0 ao variar m_p
                       (lugar das raízes) e a resposta ao degrau resultante.
                       Parâmetros: mp, md
     "secundario"      degrau de carga: o droop derruba a frequência e o
                       controle secundário a restaura deslocando a reta.
                       Parâmetro: ki (ganho integral)

   Uso:
     ::: {style="height: 600px"}
     <canvas class="nova-canvas" data-nova-anim="fasores" data-controls="delta,e"></canvas>
     :::
     <script src="anims/nova-anim.js"></script>
     <script src="anims/microrredes-anim.js"></script>
   ===================================================================== */
(function () {
  "use strict";
  const { C, FONT, fmt, ease, text, frame, axes, line, dot, seg, legend, register } = NovaAnim;

  // seta (linha grossa + ponta preenchida)
  function vec(ctx, x0, y0, x1, y1, color, o = {}) {
    const a = Math.atan2(y1 - y0, x1 - x0), L = o.head || 16;
    ctx.save();
    ctx.globalAlpha = o.alpha ?? 1;
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = o.width || 4; ctx.lineCap = "round";
    ctx.setLineDash(o.dash || []);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 - Math.cos(a) * L * 0.6, y1 - Math.sin(a) * L * 0.6); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x1 - L * Math.cos(a - 0.38), y1 - L * Math.sin(a - 0.38));
    ctx.lineTo(x1 - L * Math.cos(a + 0.38), y1 - L * Math.sin(a + 0.38));
    ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  const MATH = (px) => `italic ${px}px "Source Serif 4", Georgia, serif`;

  // -------------------------------------------------------------------
  register("fasores", ({ ctx, W, H, data }) => {
    const dmax = parseFloat(data.delta || "15") * Math.PI / 180;
    const E = parseFloat(data.e || "1.05"), V = 1, X = parseFloat(data.x || "0.5");
    const O = { x: 70, y: H * 0.78 };
    const s = Math.min((W * 0.55 - 120) / 1.25, (H * 0.78 - 50) / 0.95);
    const px = (u, v) => [O.x + u * s, O.y - v * s];

    function bar(x, y, w, val, max, color, label) {
      const zero = x + w / 2, k = (w / 2) / max;
      ctx.save();
      ctx.fillStyle = C.rule; ctx.fillRect(x, y - 1, w, 2);
      ctx.fillStyle = color; ctx.globalAlpha = 0.85;
      const v = Math.max(-max, Math.min(max, val));
      ctx.fillRect(Math.min(zero, zero + v * k), y - 14, Math.abs(v * k), 28);
      ctx.restore();
      seg(ctx, zero, y - 22, zero, y + 22, { color: C.muted, width: 1.5 });
      text(ctx, label, x - 14, y + 8, { font: MATH(30), color, align: "right" });
    }

    return {
      duration: 4.5, hold: 5,
      draw(t) {
        const d = dmax * ease(t / 3.5);
        const Ex = E * Math.cos(d), Ey = E * Math.sin(d);
        // eixos leves
        seg(ctx, O.x - 20, O.y, O.x + 1.3 * s, O.y, { color: C.rule, width: 1.5 });
        seg(ctx, O.x, O.y + 20, O.x, O.y - 0.95 * s, { color: C.rule, width: 1.5 });
        // projeções: E sen δ (∝ P) e E cos δ − V (∝ Q)
        const [ex, ey] = px(Ex, Ey), [vx, vy] = px(V, 0), [cx] = px(Ex, 0);
        seg(ctx, ex, ey, ex, O.y, { color: C.a, width: 3, dash: [6, 6] });
        text(ctx, "E sen δ", ex - 12, (ey + O.y) / 2 + 30, { font: MATH(24), color: C.a, baseline: "middle", align: "right" });
        if (Math.abs(cx - vx) > 2) {
          ctx.save(); ctx.strokeStyle = C.b; ctx.lineWidth = 7; ctx.globalAlpha = 0.7;
          ctx.beginPath(); ctx.moveTo(vx, O.y + 14); ctx.lineTo(cx, O.y + 14); ctx.stroke(); ctx.restore();
        }
        text(ctx, "E cos δ − V", (vx + cx) / 2, O.y + 46, { font: MATH(22), color: C.b, align: "center" });
        // ângulo δ
        ctx.save(); ctx.strokeStyle = C.e; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(O.x, O.y, 0.32 * s, -d, 0); ctx.stroke(); ctx.restore();
        const am = px(0.38 * Math.cos(d / 2), 0.38 * Math.sin(d / 2));
        text(ctx, "δ", am[0], am[1], { font: MATH(28), color: C.e, baseline: "middle" });
        // fasores
        vec(ctx, O.x, O.y, vx, vy, C.ink);
        text(ctx, "V", vx + 8, vy + 30, { font: MATH(30) });
        vec(ctx, O.x, O.y, ex, ey, C.c);
        text(ctx, "E", ex + 8, ey - 8, { font: MATH(30), color: C.c });
        if (Math.hypot(ex - vx, ey - vy) > 20) {
          vec(ctx, vx, vy, ex, ey, C.d, { width: 3.5 });
          text(ctx, "jXI", (vx + ex) / 2 + 14, (vy + ey) / 2 - 6, { font: MATH(26), color: C.d });
          // I = (E − V)/(jX): jXI girado de −90°
          const Ix = Ey / X, Iy = -(Ex - V) / X;
          const k = 0.5, [ix, iy] = px(Ix * k, Iy * k);
          vec(ctx, O.x, O.y, ix, iy, C.g, { width: 3, dash: [8, 6] });
          text(ctx, "I", ix + 8, iy + 8, { font: MATH(28), color: C.g });
        }
        // painel direito: valores
        const P = (E * V * Math.sin(d)) / X, Q = (E * V * Math.cos(d) - V * V) / X;
        const Pa = (E * V * d) / X, Qa = (V * (E - V)) / X;
        const x0 = W * 0.6, w = W - x0 - 30;
        text(ctx, `δ = ${fmt((d * 180) / Math.PI, 1)}°   E = ${fmt(E, 2)}   V = 1   X = ${fmt(X, 2)}  (pu)`, x0, 60,
          { font: FONT.sansM, color: C.grey });
        text(ctx, "exato", x0 + w * 0.55, 120, { font: FONT.sansB, color: C.navy, align: "center" });
        text(ctx, "aprox.", x0 + w * 0.88, 120, { font: FONT.sansB, color: C.muted, align: "center" });
        text(ctx, "P", x0, 180, { font: MATH(34), color: C.a });
        text(ctx, fmt(P, 3), x0 + w * 0.55, 180, { font: '600 34px "Inter", sans-serif', color: C.a, align: "center" });
        text(ctx, fmt(Pa, 3), x0 + w * 0.88, 180, { font: '30px "Inter", sans-serif', color: C.muted, align: "center" });
        text(ctx, "Q", x0, 240, { font: MATH(34), color: C.b });
        text(ctx, fmt(Q, 3), x0 + w * 0.55, 240, { font: '600 34px "Inter", sans-serif', color: C.b, align: "center" });
        text(ctx, fmt(Qa, 3), x0 + w * 0.88, 240, { font: '30px "Inter", sans-serif', color: C.muted, align: "center" });
        bar(x0 + 40, 320, w - 40, P, 2, C.a, "P");
        bar(x0 + 40, 390, w - 40, Q, 2, C.b, "Q");
        text(ctx, "aprox.: sen δ ≈ δ e cos δ ≈ 1", x0, H - 60, { font: FONT.ital, color: C.muted });
      },
    };
  }, {
    delta: { label: "δ", min: 0, max: 60, step: 1, value: 15, digits: 0, unit: "°" },
    e: { label: "E/V", min: 0.85, max: 1.15, step: 0.01, value: 1.05, digits: 2 },
  });

  // -------------------------------------------------------------------
  register("droop-partilha", ({ ctx, W, H, data }) => {
    const pl = parseFloat(data.pl || "0.8"), r = parseFloat(data.r || "0.5");
    const T = 10, ts = 2, tau = 0.5, f0 = 60, df = 1;
    const L0 = 0.3 * (1 + r), L1 = pl * (1 + r);
    const N = 500, tt = [], Lf = [], f = [], P1 = [], P2 = [], L = [];
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * T;
      const l = t < ts ? L0 : L1 + (L0 - L1) * Math.exp(-(t - ts) / tau);
      tt.push(t); L.push(t < ts ? L0 : L1); Lf.push(l);
      const x = l / (1 + r);                    // fração da capacidade de cada unidade
      f.push(f0 - df * x); P1.push(x); P2.push(x * r);
    }
    const gap = 110, lw = W * 0.4;
    const FL = frame({ x: 90, y: 70, w: lw - 90, h: H - 170 }, [0, 1.1], [f0 - 1.1, f0 + 0.15]);
    const rx = lw + gap, rw = W - rx - 30, hh = (H - 170 - 70) / 2;
    const FF = frame({ x: rx, y: 70, w: rw, h: hh }, [0, T], [f0 - 1.1, f0 + 0.15]);
    const FP = frame({ x: rx, y: 70 + hh + 70, w: rw, h: hh }, [0, T], [0, 1.6]);
    return {
      duration: T, hold: 4,
      draw(t) {
        const n = Math.max(1, Math.round((t / T) * N)), k = n - 1;
        axes(ctx, FL, { xticks: [0, 0.5, 1], xd: 1, yticks: [59, 59.5, 60], yd: 1, xlabel: "P (pu)", ylabel: "f (Hz)" });
        line(ctx, FL, [0, 1], [f0, f0 - df], { color: C.d, width: 3.5 });
        line(ctx, FL, [0, r], [f0, f0 - df], { color: C.g, width: 3.5 });
        seg(ctx, FL.x(0), FL.y(f[k]), FL.x(1.1), FL.y(f[k]), { color: C.rose, width: 2, dash: [7, 6] });
        dot(ctx, FL.x(P1[k]), FL.y(f[k]), { color: C.d, r: 9 });
        dot(ctx, FL.x(P2[k]), FL.y(f[k]), { color: C.g, r: 9 });
        text(ctx, "unidade 1", FL.x(0.62), FL.y(f0 - 0.62 * df) - 14, { font: FONT.sansM, color: C.d });
        text(ctx, "unidade 2", FL.x(0.55 * r) - 14, FL.y(f0 - 0.55 * df), { font: FONT.sansM, color: C.g, align: "right" });
        text(ctx, `f = ${fmt(f[k], 2)} Hz`, FL.x(1.1), FL.y(f[k]) - 12, { font: FONT.sansB, color: C.rose, align: "right" });
        axes(ctx, FF, { xticks: [], yticks: [59, 60], yd: 0, ylabel: "f (Hz)" });
        line(ctx, FF, tt, f, { n, color: C.rose, width: 3 });
        axes(ctx, FP, { xticks: [0, 2, 4, 6, 8, 10], yticks: [0, 0.5, 1, 1.5], yd: 1, xlabel: "t (s)", ylabel: "P (pu)" });
        line(ctx, FP, tt, L, { n, color: C.muted, width: 2, dash: [6, 6] });
        line(ctx, FP, tt, P1, { n, color: C.d, width: 3 });
        line(ctx, FP, tt, P2, { n, color: C.g, width: 3 });
        legend(ctx, [{ label: "carga", color: C.muted, dash: [6, 6] }, { label: "P₁", color: C.d }, { label: "P₂", color: C.g }],
          rx, H - 30);
        text(ctx, `P₁ / P₂ = ${fmt(1 / r, 2)}`, rx + rw, H - 22, { font: FONT.sansB, color: C.navy, align: "right" });
      },
    };
  }, {
    pl: { label: "carga", min: 0.4, max: 1, step: 0.05, value: 0.8, digits: 2 },
    r: { label: "P<sub>2</sub><sup>max</sup>/P<sub>1</sub><sup>max</sup>", min: 0.25, max: 1, step: 0.05, value: 0.5, digits: 2 },
  });

  // -------------------------------------------------------------------
  register("raizes-droop", ({ ctx, W, H, data }) => {
    const mp = parseFloat(data.mp || "5"), md = parseFloat(data.md || "0");
    const tau = 0.1, K = 1, b = 1 + md * K;
    const roots = (m) => {
      const disc = b * b - 4 * tau * m * K;
      if (disc >= 0) return [[(-b + Math.sqrt(disc)) / (2 * tau), 0], [(-b - Math.sqrt(disc)) / (2 * tau), 0]];
      const re = -b / (2 * tau), im = Math.sqrt(-disc) / (2 * tau);
      return [[re, im], [re, -im]];
    };
    const MMAX = 40, NS = 300;
    const mc = (b * b) / (4 * tau * K);             // ponto de quebra (raízes reais duplas)
    const sweep = Array.from({ length: NS + 1 }, (_, i) => (i / NS) * MMAX).concat([mc]).sort((u, v) => u - v);
    const r1 = sweep.map((m) => roots(m)[0]), r2 = sweep.map((m) => roots(m)[1]);
    const wn = Math.sqrt((mp * K) / tau), z = b / (2 * Math.sqrt(tau * mp * K));
    // resposta ao degrau (2ª ordem com ganho unitário), integrada numericamente
    const T = 2, dt = 0.002, ts = [], ys = [];
    let x1 = 0, x2 = 0;
    for (let t = 0; t <= T + 1e-9; t += dt) {
      ts.push(t); ys.push(x1);
      const a = wn * wn * (1 - x1) - 2 * z * wn * x2;
      x2 += a * dt; x1 += x2 * dt;
    }
    const lw = W * 0.45, gap = 110;
    const re0 = -b / tau - 2;
    const FR = frame({ x: 80, y: 60, w: lw - 80, h: H - 160 }, [re0, 2], [-22, 22]);
    const rx = lw + gap, rw = W - rx - 30;
    const FS = frame({ x: rx, y: 60, w: rw, h: H - 160 }, [0, T], [0, 1.8]);
    return {
      duration: 5, hold: 4,
      draw(t) {
        const n = Math.max(1, Math.round(Math.min(1, t / 3.5) * sweep.length));
        axes(ctx, FR, { xticks: Array.from({ length: Math.floor(-re0 / 5) + 1 }, (_, i) => -5 * i).reverse(), xd: 0, yticks: [-20, -10, 0, 10, 20], yd: 0,
          xlabel: "Re(s)", ylabel: "Im(s)" });
        seg(ctx, FR.x(0), FR.y(-22), FR.x(0), FR.y(22), { color: C.rose, width: 1.5, dash: [5, 5] });
        line(ctx, FR, r1.map((p) => p[0]), r1.map((p) => p[1]), { n, color: C.d, width: 3 });
        line(ctx, FR, r2.map((p) => p[0]), r2.map((p) => p[1]), { n, color: C.d, width: 3 });
        text(ctx, "instável →", FR.x(0) + 6, FR.y(20), { font: FONT.sans, color: C.rose });
        if (t > 3.5) {
          roots(mp).forEach(([re, im]) => {
            ctx.save(); ctx.strokeStyle = C.rose; ctx.lineWidth = 3.5;
            const X = FR.x(re), Y = FR.y(im), L = 10;
            ctx.beginPath(); ctx.moveTo(X - L, Y - L); ctx.lineTo(X + L, Y + L); ctx.moveTo(X - L, Y + L); ctx.lineTo(X + L, Y - L);
            ctx.stroke(); ctx.restore();
          });
          axes(ctx, FS, { xticks: [0, 0.5, 1, 1.5, 2], xd: 1, yticks: [0, 0.5, 1, 1.5], yd: 1, xlabel: "t (s)", ylabel: "Δδ normalizado" });
          seg(ctx, FS.x(0), FS.y(1), FS.x(T), FS.y(1), { color: C.muted, width: 1.5, dash: [6, 6] });
          const k = Math.round(Math.min(1, (t - 3.5) / 1.5) * (ts.length - 1)) + 1;
          line(ctx, FS, ts, ys, { n: k, color: C.rose, width: 3 });
          text(ctx, `ωₙ = ${fmt(wn, 1)} rad/s    ζ = ${fmt(z, 2)}`, rx, H - 40, { font: FONT.sansB, color: C.navy });
        } else {
          text(ctx, "mₚ crescendo de 0 a 40 …", rx, 120, { font: FONT.ital, color: C.muted });
        }
      },
    };
  }, {
    mp: { label: "m<sub>p</sub>", min: 0.5, max: 40, step: 0.5, value: 10, digits: 1 },
    md: { label: "m<sub>d</sub>", min: 0, max: 0.5, step: 0.05, value: 0, digits: 2 },
  });

  // -------------------------------------------------------------------
  register("secundario", ({ ctx, W, H, data }) => {
    const ki = parseFloat(data.ki || "0.6");
    const T = 14, ts = 2, tau = 0.3, f0 = 60, m = 1, dt = 0.01;
    const tt = [], f = [], fd = [], dl = [], Lf = [];
    let l = 0.4, d = m * 0.4;            // em regime: o secundário já compensava a carga inicial
    for (let t = 0; t <= T + 1e-9; t += dt) {
      const Lt = t < ts ? 0.4 : 0.8;
      l += (dt / tau) * (Lt - l);
      d += dt * ki * (m * l - d);
      tt.push(t); Lf.push(l); dl.push(d); f.push(f0 + d - m * l); fd.push(f0 - m * l);
    }
    const N = tt.length - 1;
    const lw = W * 0.4, gap = 110;
    const FL = frame({ x: 90, y: 70, w: lw - 90, h: H - 170 }, [0, 1.1], [f0 - 1.0, f0 + 0.9]);
    const rx = lw + gap, rw = W - rx - 30;
    const FT = frame({ x: rx, y: 70, w: rw, h: H - 170 }, [0, T], [f0 - 0.9, f0 + 0.3]);
    return {
      duration: T, hold: 4,
      draw(t) {
        const n = Math.max(1, Math.round((t / T) * N)), k = n - 1;
        axes(ctx, FL, { xticks: [0, 0.5, 1], xd: 1, yticks: [59.5, 60, 60.5], yd: 1, xlabel: "P (pu)", ylabel: "f (Hz)" });
        seg(ctx, FL.x(0), FL.y(f0), FL.x(1.1), FL.y(f0), { color: C.muted, width: 1.5, dash: [4, 6] });
        line(ctx, FL, [0, 1.1], [f0, f0 - 1.1 * m], { color: C.faint, width: 3, dash: [8, 6] });
        line(ctx, FL, [0, 1.1], [f0 + dl[k], f0 + dl[k] - 1.1 * m], { color: C.d, width: 3.5 });
        if (dl[k] > 0.02) {
          const xm = 0.15;
          seg(ctx, FL.x(xm), FL.y(f0 - m * xm), FL.x(xm), FL.y(f0 + dl[k] - m * xm) + 8,
            { color: C.rose, width: 2.5, arrow: true });
          text(ctx, "δω", FL.x(xm) + 10, FL.y(f0 - m * xm + dl[k] / 2), { font: MATH(26), color: C.rose, baseline: "middle" });
        }
        dot(ctx, FL.x(Lf[k]), FL.y(f[k]), { color: C.rose, r: 9 });
        text(ctx, "reta deslocada", FL.x(0.62), FL.y(f0 + dl[k] - 0.62 * m) - 18, { font: FONT.sansM, color: C.d });
        axes(ctx, FT, { xticks: [0, 2, 4, 6, 8, 10, 12, 14], yticks: [59.2, 59.6, 60], yd: 1, xlabel: "t (s)", ylabel: "f (Hz)" });
        line(ctx, FT, tt, fd, { n, color: C.muted, width: 2.5, dash: [7, 6] });
        line(ctx, FT, tt, f, { n, color: C.rose, width: 3.2 });
        legend(ctx, [{ label: "só droop", color: C.muted, dash: [7, 6] }, { label: "droop + secundário", color: C.rose }], rx, H - 30);
        text(ctx, "degrau de carga", FT.x(ts) + 8, FT.y(f0 + 0.22), { font: FONT.sans, color: C.grey });
        seg(ctx, FT.x(ts), FT.y(f0 + 0.3), FT.x(ts), FT.y(f0 - 0.9), { color: C.rule, width: 1.5 });
      },
    };
  }, {
    ki: { label: "k<sub>i</sub>", min: 0.2, max: 2, step: 0.1, value: 0.6, digits: 1 },
  });
})();
