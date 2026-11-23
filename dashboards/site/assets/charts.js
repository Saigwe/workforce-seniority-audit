/* Small chart layer over ECharts: palette roles from CSS, thin marks, crosshair tooltips, table views. */
(function () {
  "use strict";
  const charts = [];
  const css = (name) => getComputedStyle(document.body).getPropertyValue(name).trim();
  const T = () => ({
    surface: css("--surface-1"), text: css("--text-primary"), text2: css("--text-secondary"), muted: css("--text-muted"),
    grid: css("--grid"), axis: css("--axis"), border: css("--border"),
    s: [css("--s1"), css("--s2"), css("--s3"), css("--s4")],
    seq: [css("--seq-100"), css("--seq-250"), css("--seq-450"), css("--seq-700")],
    divMid: css("--div-mid"), divNeg: css("--div-neg"),
    good: css("--good"), warning: css("--warning"), serious: css("--serious"), critical: css("--critical"),
  });

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = {
    int: (v) => v == null ? "–" : Math.round(v).toLocaleString("en-GB"),
    num: (d) => (v) => v == null ? "–" : Number(v).toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d }),
    usd: (d = 0) => (v) => v == null ? "–" : "$" + Number(v).toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d }),
    pct: (d = 1) => (v) => v == null ? "–" : (100 * v).toFixed(d) + "%",
    pts: (d = 1) => (v) => v == null ? "–" : (v >= 0 ? "+" : "") + (100 * v).toFixed(d) + " pts",
    rel: (d = 1) => (v) => v == null ? "–" : (v >= 0 ? "+" : "") + (100 * v).toFixed(d) + "%",
    compact: (v) => v == null ? "–" : Math.abs(v) >= 1e6 ? (v / 1e6).toFixed(1) + "M" : Math.abs(v) >= 1e3 ? (v / 1e3).toFixed(1) + "k" : String(Math.round(v)),
    date: (s) => { const d = new Date(s + "T00:00:00"); return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" }); },
  };

  function tooltipBase(t) {
    return {
      backgroundColor: t.surface, borderColor: t.border, borderWidth: 1, padding: [8, 10],
      textStyle: { color: t.text, fontSize: 12 }, extraCssText: "box-shadow: 0 4px 16px rgba(0,0,0,.12); border-radius: 8px;",
    };
  }
  function axisTooltip(t, yFmt, xFmt) {
    return Object.assign(tooltipBase(t), {
      trigger: "axis", axisPointer: { type: "line", lineStyle: { color: t.axis, width: 1 } },
      formatter: (ps) => {
        const head = `<div style="color:${t.text2};margin-bottom:4px">${esc(xFmt ? xFmt(ps[0].axisValue) : ps[0].axisValue)}</div>`;
        return head + ps.filter((p) => p.value != null && p.value !== "-").map((p) => {
          const v = Array.isArray(p.value) ? p.value[1] : p.value;
          return `<div style="display:flex;align-items:center;gap:8px"><span style="display:inline-block;width:12px;height:2px;background:${p.color}"></span><b>${esc(yFmt(v))}</b><span style="color:${t.text2}">${esc(p.seriesName)}</span></div>`;
        }).join("");
      },
    });
  }
  function axes(t, opts) {
    const cat = {
      type: "category", data: opts.x, boundaryGap: opts.boundaryGap ?? false,
      axisLine: { lineStyle: { color: t.axis } }, axisTick: { show: false },
      axisLabel: { color: t.muted, fontSize: 11, formatter: opts.xFmt || ((v) => v), hideOverlap: true },
    };
    const val = {
      type: "value", min: opts.yMin, max: opts.yMax, splitNumber: 4,
      axisLabel: { color: t.muted, fontSize: 11, formatter: opts.yAxisFmt || opts.yFmt },
      splitLine: { lineStyle: { color: t.grid, width: 1 } }, axisLine: { show: false },
      name: opts.yName, nameTextStyle: { color: t.muted, fontSize: 11, align: "left" },
    };
    return opts.horizontal ? { xAxis: val, yAxis: Object.assign(cat, { inverse: true, boundaryGap: true }) } : { xAxis: cat, yAxis: val };
  }
  function legend(t, n, kind) {
    if (n < 2) return { show: false };
    return {
      top: 0, left: 0, itemWidth: 16, itemHeight: kind === "line" ? 4 : 10, itemGap: 14,
      icon: kind === "line" ? "rect" : "roundRect", itemStyle: { borderWidth: 0 }, textStyle: { color: t.text2, fontSize: 12 },
    };
  }

  function mount(el, build) {
    const chart = echarts.init(el, null, { renderer: "svg" });
    const entry = { chart, build, el };
    charts.push(entry);
    chart.setOption(build(T()), true);
    return chart;
  }
  function rerender() { charts.forEach((c) => { c.chart.setOption(c.build(T()), true); }); }
  window.addEventListener("resize", () => charts.forEach((c) => c.chart.resize()));
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", rerender);

  /* series: [{name, data, color (slot index 0-3 or css colour), dashed?}] */
  function line(el, o) {
    return mount(el, (t) => {
      const n = o.series.length;
      return Object.assign({
        animation: false, textStyle: { fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif" },
        grid: { left: 8, right: o.endLabels === false || n < 2 ? 16 : 118, top: n > 1 ? 34 : 14, bottom: 6, containLabel: true },
        legend: legend(t, n, "line"),
        tooltip: axisTooltip(t, o.yFmt, o.xFmt),
        series: o.series.map((s) => ({
          name: s.name, type: "line", data: s.data, showSymbol: false, symbolSize: 8, connectNulls: false,
          lineStyle: { width: 2, color: colour(t, s.color), type: s.dashed ? "dashed" : "solid" },
          itemStyle: { color: colour(t, s.color), borderColor: t.surface, borderWidth: 2 },
          emphasis: { focus: "none", scale: false },
          endLabel: { show: n > 1 && n <= 4 && o.endLabels !== false, formatter: (p) => p.seriesName, color: t.text2, fontSize: 11, distance: 6 },
          markLine: s.markLine ? {
            symbol: "none", silent: true, lineStyle: { color: t.muted, width: 1, type: "solid" },
            label: { color: t.muted, fontSize: 11, formatter: s.markLine.label, position: "insideEndTop" },
            data: [{ yAxis: s.markLine.y }],
          } : undefined,
          markArea: s.markArea ? {
            silent: true, itemStyle: { color: t.critical, opacity: 0.08 },
            label: { color: t.text2, fontSize: 11, position: "insideTop" },
            data: [[{ xAxis: s.markArea.from, name: s.markArea.label }, { xAxis: s.markArea.to }]],
          } : undefined,
        })),
      }, axes(t, o));
    });
  }

  function bar(el, o) {
    return mount(el, (t) => {
      const n = o.series.length;
      const last = n - 1;
      return Object.assign({
        animation: false, textStyle: { fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif" },
        grid: { left: 8, right: o.horizontal && o.series.some((s) => s.labels) ? 48 : 16, top: n > 1 ? 34 : 14, bottom: 6, containLabel: true },
        legend: legend(t, n, "bar"),
        tooltip: Object.assign(axisTooltip(t, o.yFmt, o.xFmt), { axisPointer: { type: "shadow", shadowStyle: { color: "rgba(127,127,127,0.08)" } } }),
        series: o.series.map((s, i) => ({
          name: s.name, type: "bar", data: s.data.map((v, j) => s.colors ? { value: v, itemStyle: { color: colour(t, s.colors[j]) } } : v),
          stack: o.stack ? "all" : undefined, barMaxWidth: o.barMax || 28, barCategoryGap: o.gap || "30%",
          itemStyle: {
            color: colour(t, s.color), borderColor: t.surface, borderWidth: o.stack ? 1 : 0,
            borderRadius: !o.stack || i === last ? (o.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]) : 0,
          },
          label: s.labels ? { show: true, position: o.horizontal ? "right" : "top", color: t.text2, fontSize: 11, formatter: (p) => o.yFmt(p.value) } : undefined,
          emphasis: { itemStyle: { opacity: 0.85 } },
        })),
      }, axes(t, Object.assign({ boundaryGap: true }, o)));
    });
  }

  function heatmap(el, o) {
    /* o: {x: [...], y: [...], cells: [[xi, yi, v]], fmt, min, max} */
    return mount(el, (t) => ({
      animation: false, textStyle: { fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif" },
      grid: { left: 8, right: 16, top: 8, bottom: 52, containLabel: true },
      tooltip: Object.assign(tooltipBase(t), {
        formatter: (p) => `<b>${esc(o.fmt(p.value[2]))}</b> <span style="color:${t.text2}">${esc(o.yLabel(o.y[p.value[1]]))}, ${esc(o.xLabel(o.x[p.value[0]]))}</span>`,
      }),
      xAxis: { type: "category", data: o.x, axisLabel: { color: t.muted, fontSize: 11, formatter: o.xLabel }, axisLine: { lineStyle: { color: t.axis } }, axisTick: { show: false }, splitArea: { show: false }, name: o.xName, nameLocation: "middle", nameGap: 24, nameTextStyle: { color: t.muted, fontSize: 11 } },
      yAxis: { type: "category", data: o.y, inverse: true, axisLabel: { color: t.muted, fontSize: 11, formatter: o.yLabel }, axisLine: { show: false }, axisTick: { show: false } },
      visualMap: {
        min: o.min, max: o.max, calculable: false, text: [o.fmt(o.max), o.fmt(o.min)], orient: "horizontal", left: "center", bottom: 0, itemHeight: 140, itemWidth: 10,
        inRange: { color: t.seq }, textStyle: { color: t.muted, fontSize: 11 }, formatter: (v) => o.fmt(v),
      },
      series: [{ type: "heatmap", data: o.cells, itemStyle: { borderColor: t.surface, borderWidth: 2, borderRadius: 2 }, emphasis: { itemStyle: { borderColor: t.text, borderWidth: 1 } } }],
    }));
  }

  /* Interval chart: one row per metric, a dot at the estimate, a line for the 95% interval, zero line. */
  function forest(el, o) {
    return mount(el, (t) => {
      const rows = o.rows;
      return {
        animation: false, textStyle: { fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif" },
        grid: { left: 8, right: 24, top: 24, bottom: 6, containLabel: true },
        tooltip: Object.assign(tooltipBase(t), {
          formatter: (p) => { const r = rows[p.dataIndex]; return `<b>${esc(r.fmt(r.est))}</b> <span style="color:${t.text2}">${esc(r.name)}</span><br><span style="color:${t.text2}">95% interval ${esc(r.fmt(r.low))} to ${esc(r.fmt(r.high))}</span>`; },
        }),
        xAxis: { type: "value", axisLabel: { color: t.muted, fontSize: 11, formatter: (v) => (v > 0 ? "+" : "") + Math.round(v * 100) + "%" }, splitLine: { lineStyle: { color: t.grid } } },
        yAxis: { type: "category", data: rows.map((r) => r.name), inverse: true, axisLabel: { color: t.text2, fontSize: 12 }, axisLine: { show: false }, axisTick: { show: false } },
        series: [{
          type: "custom", data: rows.map((r, i) => [r.low, r.high, i, r.est]),
          renderItem: (params, api) => {
            const a = api.coord([api.value(0), api.value(2)]), b = api.coord([api.value(1), api.value(2)]), c = api.coord([api.value(3), api.value(2)]);
            const col = colour(t, rows[params.dataIndex].color);
            return { type: "group", children: [
              { type: "rect", shape: { x: a[0] - 6, y: a[1] - 14, width: b[0] - a[0] + 12, height: 28 }, style: { fill: "transparent" } },
              { type: "line", shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, style: { stroke: col, lineWidth: 2 } },
              { type: "circle", shape: { cx: c[0], cy: c[1], r: 5 }, style: { fill: col, stroke: t.surface, lineWidth: 2 } },
            ] };
          },
          markLine: { symbol: "none", silent: true, lineStyle: { color: t.axis, width: 1, type: "solid" }, label: { show: false }, data: [{ xAxis: 0 }].concat(o.guardrail != null ? [{ xAxis: o.guardrail, lineStyle: { color: t.critical }, label: { show: true, formatter: "guardrail " + Math.round(o.guardrail * 100) + "%", color: t.text2, fontSize: 11, position: "start" } }] : []) },
        }],
      };
    });
  }

  function colour(t, c) {
    if (typeof c === "number") return t.s[c];
    if (c && c.startsWith("--")) return css(c);
    return c || t.s[0];
  }

  function table(target, cols, rows) {
    const tbl = document.createElement("table");
    const thead = tbl.createTHead().insertRow();
    cols.forEach((c) => { const th = document.createElement("th"); th.textContent = c.label; thead.appendChild(th); });
    const body = tbl.createTBody();
    rows.forEach((r) => {
      const tr = body.insertRow();
      cols.forEach((c) => { const td = tr.insertCell(); const v = r[c.key]; td.textContent = c.fmt ? c.fmt(v) : (v ?? "–"); });
    });
    target.replaceChildren(tbl);
  }

  /* Wire a card: <section class="card" id=...> with .chart, .table-view and .tbl-btn. */
  function card(id, render, tableSpec) {
    const sec = document.getElementById(id);
    if (!sec) return;
    const el = sec.querySelector(".chart");
    const tv = sec.querySelector(".table-view");
    const btn = sec.querySelector(".tbl-btn");
    if (el) render(el);
    if (tv && tableSpec) {
      table(tv, tableSpec.cols, tableSpec.rows);
      tv.hidden = true;
      btn.addEventListener("click", () => {
        const showing = !tv.hidden;
        tv.hidden = showing; if (el) el.hidden = !showing;
        btn.textContent = showing ? "Table" : "Chart";
        btn.setAttribute("aria-pressed", String(!showing));
        if (showing && el) charts.forEach((c) => c.chart.resize());
      });
    } else if (btn) btn.remove();
  }

  function clear() { charts.splice(0).forEach((c) => c.chart.dispose()); }

  window.Viz = { line, bar, heatmap, forest, card, table, fmt, esc, rerender, clear, css };

  /* Theme toggle shared by every page. */
  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.querySelector(".theme-btn");
    const saved = localStorage.getItem("theme");
    if (saved) document.documentElement.dataset.theme = saved;
    const label = () => { const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches; btn.textContent = dark ? "Light mode" : "Dark mode"; };
    if (btn) {
      label();
      btn.addEventListener("click", () => {
        const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
        document.documentElement.dataset.theme = dark ? "light" : "dark";
        localStorage.setItem("theme", document.documentElement.dataset.theme);
        label(); rerender();
      });
    }
  });
})();
