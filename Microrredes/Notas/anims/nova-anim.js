/* =====================================================================
   NovaAnim — base comum das animações em canvas do tema Nova.

   Uma animação é registrada com
     NovaAnim.register("nome", (env) => ({ duration, hold, draw(t) }))
   e usada no slide com
     ::: {style="height: 700px"}
     <canvas class="nova-canvas" data-nova-anim="nome" data-speed="1"></canvas>
     :::
     <script src="anims/nova-anim.js"></script>
     <script src="anims/nome.js"></script>

   - draw(t) recebe o tempo da animação em segundos (0 … duration);
   - ao chegar ao fim, segura `hold` segundos e recomeça (data-loop="false"
     para parar no último quadro);
   - data-speed multiplica a velocidade (0.7 = 30 % mais lento);
   - começa ao entrar no slide, pausa ao sair; tecla R reinicia.
   ===================================================================== */
(function () {
  "use strict";
  if (window.NovaAnim) return;

  const css = getComputedStyle(document.documentElement);
  const v = (name, d) => (css.getPropertyValue(name).trim() || d);

  const C = {
    ink: "#1D1C1A", muted: "#77736A", grey: "#5F6368", rule: "#DDD7CB",
    faint: "#C9C3B6", paper: "#F7F5F0", navy: "#1B365D", rose: "#A63D4A",
    a: v("--eq-a", "#7B4FD0"), b: v("--eq-b", "#2E9C6B"), c: v("--eq-c", "#D2457E"),
    d: v("--eq-d", "#3A6EDB"), e: v("--eq-e", "#D0473B"), f: v("--eq-f", "#2795B0"),
    g: v("--eq-g", "#D27A22"), h: v("--eq-h", "#7A8A1C"),
  };

  const FONT = {
    title: '600 26px "Source Serif 4", Georgia, serif',
    serif: '24px "Source Serif 4", Georgia, serif',
    ital: 'italic 24px "Source Serif 4", Georgia, serif',
    sans: '20px "Inter", sans-serif',
    sansM: '500 22px "Inter", sans-serif',
    sansB: '600 24px "Inter", sans-serif',
  };

  // número com vírgula decimal
  const fmt = (x, d = 2) => (isFinite(x) ? x.toFixed(d).replace(".", ",") : "—");
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const ease = (x) => 1 - Math.pow(1 - clamp(x, 0, 1), 3);

  // ---------------------------------------------------------------
  // Desenho
  // ---------------------------------------------------------------
  function text(ctx, s, x, y, o = {}) {
    ctx.save();
    ctx.font = o.font || FONT.sans;
    ctx.fillStyle = o.color || C.ink;
    ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
    ctx.textAlign = o.align || "left";
    ctx.textBaseline = o.baseline || "alphabetic";
    ctx.fillText(s, x, y);
    ctx.restore();
  }

  // Mapeamento de dados → pixels numa caixa {x, y, w, h}
  function frame(box, xlim, ylim) {
    return {
      box, xlim, ylim,
      x: (u) => box.x + ((u - xlim[0]) / (xlim[1] - xlim[0])) * box.w,
      y: (u) => box.y + (1 - (u - ylim[0]) / (ylim[1] - ylim[0])) * box.h,
    };
  }

  function axes(ctx, F, o = {}) {
    const { box } = F;
    ctx.save();
    ctx.lineWidth = 1;
    ctx.strokeStyle = C.rule;
    ctx.font = FONT.sans;
    ctx.fillStyle = C.muted;
    (o.yticks || []).forEach((t) => {
      const y = F.y(t);
      ctx.beginPath(); ctx.moveTo(box.x, y); ctx.lineTo(box.x + box.w, y); ctx.stroke();
      ctx.textAlign = "right"; ctx.textBaseline = "middle";
      ctx.fillText(o.yfmt ? o.yfmt(t) : fmt(t, o.yd ?? 1), box.x - 10, y);
    });
    (o.xticks || []).forEach((t) => {
      ctx.textAlign = "center"; ctx.textBaseline = "top";
      ctx.fillText(o.xfmt ? o.xfmt(t) : fmt(t, o.xd ?? 0), F.x(t), box.y + box.h + 8);
    });
    ctx.strokeStyle = C.muted;
    ctx.beginPath();
    ctx.moveTo(box.x, box.y); ctx.lineTo(box.x, box.y + box.h); ctx.lineTo(box.x + box.w, box.y + box.h);
    ctx.stroke();
    if (o.xlabel) {
      ctx.font = FONT.ital; ctx.fillStyle = C.grey; ctx.textAlign = "right"; ctx.textBaseline = "top";
      ctx.fillText(o.xlabel, box.x + box.w, box.y + box.h + 34);
    }
    if (o.ylabel) {
      ctx.font = FONT.ital; ctx.fillStyle = C.grey; ctx.textAlign = "left"; ctx.textBaseline = "bottom";
      ctx.fillText(o.ylabel, box.x + 8, box.y - 6);
    }
    ctx.restore();
  }

  // Polilinha (xs, ys) até o índice n (exclusive); stairs = degraus (ZOH)
  function line(ctx, F, xs, ys, o = {}) {
    const n = Math.min(o.n ?? xs.length, xs.length);
    if (n < 1) return;
    ctx.save();
    ctx.beginPath();
    ctx.rect(F.box.x - 2, F.box.y - 4, F.box.w + 4, F.box.h + 6);
    ctx.clip();
    ctx.beginPath();
    for (let i = (o.from || 0); i < n; i++) {
      const px = F.x(xs[i]), py = F.y(ys[i]);
      if (i === (o.from || 0)) ctx.moveTo(px, py);
      else if (o.stairs) { ctx.lineTo(px, F.y(ys[i - 1])); ctx.lineTo(px, py); }
      else ctx.lineTo(px, py);
    }
    if (o.stairs && o.extend != null) ctx.lineTo(F.x(o.extend), F.y(ys[n - 1]));
    ctx.strokeStyle = o.color || C.ink;
    ctx.lineWidth = o.width || 2.6;
    ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
    ctx.setLineDash(o.dash || []);
    ctx.lineJoin = "round"; ctx.lineCap = "round";
    ctx.stroke();
    ctx.restore();
  }

  function dot(ctx, x, y, o = {}) {
    ctx.save();
    ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
    ctx.beginPath(); ctx.arc(x, y, o.r || 6, 0, 2 * Math.PI);
    ctx.fillStyle = o.color || C.ink; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = C.paper; ctx.stroke();
    ctx.restore();
  }

  function seg(ctx, x0, y0, x1, y1, o = {}) {
    ctx.save();
    ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
    ctx.strokeStyle = o.color || C.muted;
    ctx.lineWidth = o.width || 1.5;
    ctx.setLineDash(o.dash || []);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    if (o.arrow) {
      const a = Math.atan2(y1 - y0, x1 - x0), L = 11;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(x1, y1); ctx.lineTo(x1 - L * Math.cos(a - 0.4), y1 - L * Math.sin(a - 0.4));
      ctx.moveTo(x1, y1); ctx.lineTo(x1 - L * Math.cos(a + 0.4), y1 - L * Math.sin(a + 0.4));
      ctx.stroke();
    }
    ctx.restore();
  }

  // Legenda em linha: [{label, color, dash}]
  function legend(ctx, items, x, y, o = {}) {
    let cx = x;
    items.forEach((it) => {
      seg(ctx, cx, y, cx + 30, y, { color: it.color, width: 3.5, dash: it.dash });
      text(ctx, it.label, cx + 40, y, { baseline: "middle", font: o.font || FONT.sansM, color: C.ink });
      ctx.font = o.font || FONT.sansM;
      cx += 40 + ctx.measureText(it.label).width + (o.gap || 34);
    });
  }

  // ---------------------------------------------------------------
  // Registro e ciclo de vida
  // ---------------------------------------------------------------
  // Impressão em PDF (?print-pdf): monta tudo e desenha o quadro final
  const PRINT = /print-pdf/i.test(window.location.search);

  function mount(canvas, factory, params) {
    const S = 2, W = canvas.offsetWidth, H = canvas.offsetHeight;
    canvas.width = W * S; canvas.height = H * S;
    const ctx = canvas.getContext("2d");
    ctx.scale(S, S);
    const speed = parseFloat(canvas.dataset.speed || "1");
    const loop = canvas.dataset.loop !== "false";
    const build = () => factory({ canvas, ctx, W, H, data: canvas.dataset });
    let anim = build();
    let duration = anim.duration || 10, hold = anim.hold ?? 3;

    let t = 0, held = 0, last = null, raf = null, manual = false;
    const render = () => { ctx.clearRect(0, 0, W, H); anim.draw(Math.min(t, duration)); };
    if (PRINT) { t = duration; anim.settle && anim.settle(); render(); return; }
    function tick(ts) {
      const dt = last == null ? 0 : Math.min((ts - last) / 1000, 0.1);
      last = ts;
      if (t < duration) t += dt * speed;
      else if (loop && !manual && (held += dt) > hold) { t = 0; held = 0; anim.reset && anim.reset(); }
      render();
      raf = requestAnimationFrame(tick);
    }
    const start = () => { if (!raf) { last = null; raf = requestAnimationFrame(tick); } };
    const stop = () => { cancelAnimationFrame(raf); raf = null; };
    canvas.addEventListener("nova:start", start);
    canvas.addEventListener("nova:stop", stop);
    canvas.addEventListener("nova:restart", () => {
      manual = false; t = 0; held = 0; anim.reset && anim.reset(); start();
    });
    // Sliders: o parâmetro muda → recalcula e mostra o resultado completo
    canvas.addEventListener("nova:params", () => {
      anim = build();
      duration = anim.duration || 10; hold = anim.hold ?? 3;
      if (!anim.continuous) { manual = true; t = duration; }   // contínuas seguem rodando
      render(); start();
    });
    render();
    if (canvas.closest("section.present")) start();
  }

  // ---------------------------------------------------------------
  // Controles ao vivo: data-controls="zeta,wn" cria sliders sob o canvas
  // usando a especificação `params` passada em register().
  // ---------------------------------------------------------------
  function controls(canvas, params) {
    const keys = (canvas.dataset.controls || "").split(",").map((k) => k.trim()).filter((k) => params[k]);
    if (!keys.length || canvas.dataset.controlsBuilt) return;
    canvas.dataset.controlsBuilt = "1";
    const host = canvas.parentElement;
    host.classList.add("nova-has-controls");
    const bar = document.createElement("div");
    bar.className = "nova-controls";
    keys.forEach((k) => {
      const p = params[k];
      const val = canvas.dataset[k] ?? String(p.value);
      canvas.dataset[k] = val;
      const lab = document.createElement("label");
      lab.innerHTML = `<span class="nova-ctl-name">${p.label}</span>`;
      const inp = document.createElement("input");
      Object.assign(inp, { type: "range", min: p.min, max: p.max, step: p.step, value: val });
      const out = document.createElement("span");
      out.className = "nova-ctl-val";
      const show = () => (out.textContent = fmt(parseFloat(inp.value), p.digits ?? 2) + (p.unit ? " " + p.unit : ""));
      show();
      inp.addEventListener("input", () => {
        canvas.dataset[k] = inp.value; show();
        canvas.dispatchEvent(new CustomEvent("nova:params"));
      });
      // as setas mexem no slider, não nos slides
      inp.addEventListener("keydown", (e) => e.stopPropagation());
      lab.append(inp, out);
      bar.appendChild(lab);
    });
    const reset = document.createElement("button");
    reset.type = "button"; reset.className = "nova-ctl-replay"; reset.textContent = "▶ reproduzir";
    reset.addEventListener("click", () => canvas.dispatchEvent(new CustomEvent("nova:restart")));
    bar.appendChild(reset);
    host.appendChild(bar);
  }

  function register(name, factory, params = {}) {
    const lazy = (canvas) => {
      controls(canvas, params);
      if (canvas.offsetWidth) return mount(canvas, factory, params);
      canvas.addEventListener("nova:start", () => mount(canvas, factory, params), { once: true });
    };
    const all = () => document.querySelectorAll(`canvas[data-nova-anim="${name}"]`);
    const init = () => {
      if (PRINT) {
        all().forEach((c) => controls(c, params));
        const go = () => all().forEach((c) => {
          if (c.offsetWidth && !c.dataset.printed) { c.dataset.printed = "1"; mount(c, factory, params); }
        });
        Reveal.on("pdf-ready", go);
        setTimeout(go, 1500);
        return;
      }
      all().forEach(lazy);
    };
    if (window.Reveal && Reveal.isReady && Reveal.isReady()) init();
    else window.addEventListener("load", () => (Reveal.isReady() ? init() : Reveal.on("ready", init)));
  }

  window.NovaAnim = { C, FONT, fmt, clamp, ease, text, frame, axes, line, dot, seg, legend, register, PRINT };
})();
