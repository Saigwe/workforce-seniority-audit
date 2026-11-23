/* Page renderers. Data: window.DASH (data.js). Aggregates only. */
(function () {
  "use strict";
  const D = window.DASH;
  const { line, bar, heatmap, card, table, fmt, esc } = window.Viz;
  const uniq = (a) => [...new Set(a)];
  const mon = (s) => new Date(s.slice(0, 10) + "T00:00:00").toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
  const EN = Object.fromEntries(D.naive_emp.filter((r) => r.employer_name).map((r) => [r.employer_code, r.employer_name]));
  const band = (b) => b.slice(3);
  const Q = Object.fromEntries(D.quality.map((r) => [r.reason_code, r]));
  const total = D.bridge.find((r) => r.step_no === 7).running_total;
  const naive = D.bridge.find((r) => r.step_no === 1).running_total;
  const sign = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt.int(Math.abs(v));

  function tiles(list) {
    const el = document.getElementById("tiles");
    if (!el) return;
    el.replaceChildren(...list.map((t) => {
      const d = document.createElement("div"); d.className = "tile";
      const k = document.createElement("div"); k.className = "k"; k.textContent = t.k;
      const v = document.createElement("div"); v.className = "v"; v.textContent = t.v;
      d.append(k, v);
      if (t.d) { const s = document.createElement("div"); s.className = "d"; s.textContent = t.d; d.append(s); }
      return d;
    }));
  }
  const insights = (items) => {
    document.getElementById("insights").innerHTML = items.map(([cls, label, text, href, where]) =>
      `<li><span class="status ${cls}"><i aria-hidden="true">${cls === "good" ? "✓" : "!"}</i>${label}</span><span>${text} <a class="where" href="${href}">${where} →</a></span></li>`).join("");
  };
  const rejected = D.quality.filter((r) => r.severity === "reject").reduce((a, r) => a + r.affected, 0);
  const insuff = (D.bands.find((r) => r.tenure_band.startsWith("6.")) || { workers: 0 }).workers;

  function overview() {
    const step = (n) => D.bridge.find((r) => r.step_no === n).change;
    tiles([
      { k: "Naive: open history rows", v: fmt.int(naive), d: "end date blank or 9999" },
      { k: "Headcount on 31 October", v: fmt.int(total), d: `${sign(total - naive)} (${fmt.rel(1)((total - naive) / naive)}) against naive` },
      { k: "Seniority calculated", v: fmt.int(total - insuff), d: `${fmt.int(insuff)} with insufficient evidence` },
      { k: "History rows rejected", v: fmt.int(rejected), d: `${fmt.pct(1)(rejected / D.totals.deduplicated_rows)} of ${fmt.int(D.totals.deduplicated_rows)}` },
      { k: "Workers with no history", v: fmt.int(D.workers.no_history), d: "in the master, never placed" },
    ]);
    insights([
      ["critical", "The naive answer is low", `<b>Counting rows with an open end date gives ${fmt.int(naive)}; the as-of headcount is ${fmt.int(total)}.</b> ${fmt.int(step(4))} fixed-term placements end after 31 October: those workers are employed that day, but their end date is not blank. Open rows also include ${fmt.int(-step(2))} exact duplicates and ${fmt.int(-step(3))} placements that start in November or December.`, "index.html#ov-bridge", "Bridge"],
      ["warning", "Rejected, not guessed", `<b>${fmt.int(-step(5))} rows that would have counted on 31 October are rejected</b>, for conflicting assignments (a worker placed with two employers at once), unparseable or impossible dates (31/02/2024, 2023-13-01) or no matching worker in either master extract. Across the whole history ${fmt.int(rejected)} rows are rejected, each in the rejection table with a reason code.`, "quality.html", "Data quality"],
      ["warning", "Insufficient evidence", `<b>${fmt.int(insuff)} workers on 31 October have no seniority figure.</b> They hold a valid placement, but part of their history was rejected (an end before its start, an unknown employer, or two conflicting rows for one start), so continuous service cannot be established. They are shown as a band of their own, not dropped.`, "tenure.html", "Seniority"],
      ["good", "Edge cases tested", `<b>Tenure counts completed months with a month-end rule:</b> 31 January to 28 February is one month, 29 February 2024 to 28 February 2025 is twelve. ${D.fixtures.length} documented cases run on every build.`, "tenure.html#tn-fixtures", "Fixtures"],
      ["good", "Reconciles", `<b>The total is ${fmt.int(total)} under every cut:</b> employers, branches including unassigned (${fmt.int(D.missing_branch.reduce((a, r) => a + r.missing, 0))} workers have no branch recorded), regions and tenure bands.`, "headcount.html#hc-recon", "Headcount"],
    ]);
    const br = D.bridge.filter((r) => r.step_no < 7);
    card("ov-bridge", (el) => bar(el, { horizontal: true, x: br.map((r) => `${r.step_no}. ${r.step}`), yFmt: fmt.int, series: [{ name: "Count after this rule", data: br.map((r) => r.running_total), colors: br.map((r) => (r.step_no === 1 ? 1 : r.step_no === 6 ? 0 : 2)), labels: true }] }),
      { cols: [{ key: "step_no", label: "#" }, { key: "step", label: "Rule" }, { key: "change", label: "Change", fmt: sign }, { key: "running_total", label: "Count", fmt: fmt.int }], rows: D.bridge });
    const ne = D.naive_emp.filter((r) => r.employer_code !== "EMP-99");
    card("ov-emp", (el) => bar(el, { x: ne.map((r) => r.employer_code), yFmt: fmt.int, series: [{ name: "Open history rows", data: ne.map((r) => r.naive_open_rows), color: 1 }, { name: "Headcount on 31 October", data: ne.map((r) => r.headcount), color: 0 }] }),
      { cols: [{ key: "employer_code", label: "Employer" }, { key: "employer_name", label: "Name" }, { key: "naive_open_rows", label: "Open rows", fmt: fmt.int }, { key: "headcount", label: "Headcount", fmt: fmt.int }], rows: D.naive_emp });
    bandsChart("ov-bands");
  }

  function bandsChart(id) {
    card(id, (el) => bar(el, { horizontal: true, x: D.bands.map((r) => band(r.tenure_band)), yFmt: fmt.pct(0), series: [{ name: "Share of workers", data: D.bands.map((r) => r.share), colors: D.bands.map((r) => (r.tenure_band.startsWith("6.") ? 1 : 0)), labels: true }] }),
      { cols: [{ key: "tenure_band", label: "Band", fmt: band }, { key: "workers", label: "Workers", fmt: fmt.int }, { key: "share", label: "Share", fmt: fmt.pct(1) }], rows: D.bands });
  }

  function headcount() {
    const months = uniq(D.monthly.map((r) => r.month_end)).sort();
    const tot = months.map((m) => D.monthly.filter((r) => r.month_end === m).reduce((a, r) => a + r.workers, 0));
    const missing = D.missing_branch.reduce((a, r) => a + r.missing, 0);
    tiles([
      { k: "Headcount, 31 October 2026", v: fmt.int(total), d: `${sign(total - tot[tot.length - 13])} on a year earlier` },
      { k: "Employers", v: String(D.asof.length), d: "client employers with workers placed" },
      { k: "No branch recorded", v: fmt.int(missing), d: fmt.pct(1)(missing / total) + " of workers" },
    ]);
    card("hc-trend", (el) => line(el, { x: months, xFmt: mon, yFmt: fmt.int, yMin: 0, series: [{ name: "Workers placed", data: tot, color: 0 }] }),
      { cols: [{ key: "m", label: "Month end" }, { key: "w", label: "Workers", fmt: fmt.int }], rows: months.map((m, i) => ({ m, w: tot[i] })) });
    card("hc-emp", (el) => bar(el, { horizontal: true, x: D.asof.map((r) => r.employer_name), yFmt: fmt.int, series: [{ name: "Workers", data: D.asof.map((r) => r.workers), color: 0, labels: true }] }),
      { cols: [{ key: "employer_code", label: "Code" }, { key: "employer_name", label: "Employer" }, { key: "workers", label: "Workers", fmt: fmt.int }], rows: D.asof });
    card("hc-region", (el) => bar(el, { x: D.region.map((r) => r.region), yFmt: fmt.int, series: [{ name: "Workers", data: D.region.map((r) => r.workers), colors: D.region.map((r) => (r.region === "Unassigned" ? 1 : 0)), labels: true }] }),
      { cols: [{ key: "region", label: "Region" }, { key: "workers", label: "Workers", fmt: fmt.int }], rows: D.region });
    table(document.getElementById("recon"), [{ key: "cut", label: "Cut" }, { key: "workers", label: "Workers", fmt: fmt.int }], D.recon);
    card("hc-missing", (el) => bar(el, { x: D.missing_branch.map((r) => r.employer_code), yFmt: fmt.int, series: [{ name: "Workers with no branch", data: D.missing_branch.map((r) => r.missing), color: 1 }] }),
      { cols: [{ key: "employer_code", label: "Employer" }, { key: "missing", label: "No branch", fmt: fmt.int }, { key: "workers", label: "Workers", fmt: fmt.int }], rows: D.missing_branch });
  }

  function tenure() {
    const calc = D.bands.filter((r) => !r.tenure_band.startsWith("6."));
    const five = (D.bands.find((r) => r.tenure_band.startsWith("5.")) || {}).workers || 0;
    tiles([
      { k: "Seniority calculated", v: fmt.int(total - insuff), d: `of ${fmt.int(total)} workers` },
      { k: "Insufficient evidence", v: fmt.int(insuff), d: "part of their history was rejected" },
      { k: "Five years or more", v: fmt.pct(0)(five / calc.reduce((a, r) => a + r.workers, 0)), d: "of calculated workers" },
      { k: "Tenure rule fixtures", v: `${D.fixtures.filter((r) => r.computed_months === r.expected_months).length} / ${D.fixtures.length}`, d: "passing" },
    ]);
    bandsChart("tn-bands");
    const emps = uniq(D.cells.map((r) => r.employer_code)).sort(), bands = uniq(D.cells.map((r) => r.tenure_band)).sort();
    const cells = [];
    D.cells.forEach((r) => { if (r.workers != null) cells.push([bands.indexOf(r.tenure_band), emps.indexOf(r.employer_code), r.workers]); });
    card("tn-matrix", (el) => heatmap(el, { x: bands, y: emps, cells, min: 0, max: Math.max(...cells.map((c) => c[2])), fmt: (v) => fmt.int(v) + " workers", xLabel: (b) => band(b).replace(" or more", "+").replace("Insufficient evidence", "Insufficient"), yLabel: (e) => EN[e] || e }),
      { cols: [{ key: "employer_code", label: "Employer", fmt: (e) => EN[e] || e }, { key: "tenure_band", label: "Band", fmt: band }, { key: "workers", label: "Workers", fmt: (v) => (v == null ? "<5" : fmt.int(v)) }], rows: D.cells });
    table(document.getElementById("fixtures"), [{ key: "case_id", label: "Case" }, { key: "start_date", label: "Start" }, { key: "as_of_date", label: "As of" },
      { key: "expected_months", label: "Expected", fmt: (v) => (v == null ? "none" : String(v)) }, { key: "computed_months", label: "Computed", fmt: (v) => (v == null ? "none" : String(v)) }, { key: "note", label: "Why" }], D.fixtures);
  }

  function quality() {
    const ex = D.extracts;
    tiles([
      { k: "History rows delivered", v: fmt.int(D.totals.raw_rows), d: `${fmt.int(D.totals.exact_duplicate_rows)} exact duplicates removed` },
      { k: "Rejected", v: fmt.int(rejected), d: fmt.pct(1)(rejected / D.totals.deduplicated_rows) + " of deduplicated rows" },
      { k: "Worker IDs reused by both systems", v: "15", d: "kept apart by source system" },
      { k: "Master extracts differ", v: fmt.int(ex.job_family_differs + ex.home_region_differs + ex.record_created_differs), d: "fields, despite same header and size" },
    ]);
    const q = D.quality.slice().sort((a, b) => b.affected - a.affected);
    card("dq-reasons", (el) => bar(el, { horizontal: true, x: q.map((r) => `${r.reason} (${r.severity})`), yFmt: fmt.int, series: [{ name: "Affected", data: q.map((r) => r.affected), colors: q.map((r) => (r.severity === "reject" ? 1 : 2)), labels: true }] }),
      { cols: [{ key: "reason_code", label: "Code" }, { key: "severity", label: "Severity" }, { key: "affected", label: "Affected", fmt: fmt.int }, { key: "unit", label: "Unit" }, { key: "rate", label: "Rate", fmt: fmt.pct(2) }], rows: q });
    const sys = uniq(D.by_source.map((r) => r.source_system)), reasons = uniq(D.by_source.map((r) => r.reason_code));
    card("dq-source", (el) => bar(el, { horizontal: true, x: reasons, yFmt: fmt.pct(2), series: sys.map((s, i) => ({ name: s, data: reasons.map((c) => (D.by_source.find((r) => r.source_system === s && r.reason_code === c) || {}).rate || 0), color: i })) }),
      { cols: [{ key: "source_system", label: "System" }, { key: "reason_code", label: "Reason" }, { key: "rows_rejected", label: "Rows" }, { key: "rate", label: "Rate", fmt: fmt.pct(2) }], rows: D.by_source });
    const fm = D.formats.filter((r) => r.field === "start");
    const fmts = uniq(fm.map((r) => r.format));
    card("dq-formats", (el) => bar(el, { x: sys, yFmt: fmt.int, stack: true, series: fmts.map((f, i) => ({ name: f, data: sys.map((s) => (fm.find((r) => r.source_system === s && r.format === f) || {}).rows_n || 0), color: f === "unrecognised" ? "--critical" : i % 4 })) }),
      { cols: [{ key: "source_system", label: "System" }, { key: "field", label: "Field" }, { key: "format", label: "Format" }, { key: "rows_n", label: "Rows", fmt: fmt.int }], rows: D.formats });
    const same = ex.rows_a === ex.rows_b;
    document.getElementById("extracts").innerHTML = `<ul class="insights">
      <li><span class="status good"><i aria-hidden="true">✓</i>Same</span><span><b>Header and row count:</b> ${fmt.int(ex.rows_a)} and ${fmt.int(ex.rows_b)} rows${same ? ", identical counts" : ""}; no worker in one and not the other.</span></li>
      <li><span class="status warning"><i aria-hidden="true">!</i>Differs</span><span><b>Job family differs for ${ex.job_family_differs} workers.</b> Home region: ${ex.home_region_differs}; record created: ${ex.record_created_differs}. The later extract is used, and the difference is reported rather than assumed away.</span></li></ul>`;
    table(document.getElementById("audit"), [{ key: "reason_code", label: "Code" }, { key: "severity", label: "Severity" }, { key: "rule", label: "Rule" }, { key: "affected", label: "Affected", fmt: fmt.int }, { key: "unit", label: "Unit" }, { key: "rate", label: "Rate", fmt: fmt.pct(2) }], D.quality);
  }

  function checks() {
    tiles([
      { k: "dbt models and tests", v: D.dbt ? `${D.dbt.passed} / ${D.dbt.nodes}` : "–", d: "passing" },
      { k: "Tenure fixtures", v: String(D.fixtures.length), d: "month ends, leap days, future starts" },
    ]);
    const rules = [
      ["Every delivered row is a valid placement, an exact duplicate, or rejected for exactly one reason", "assert_every_row_accounted_for; test_every_raw_row_is_valid_or_rejected_once"],
      ["A worker holds one valid placement at a time, and at most one open-ended one", "assert_no_overlapping_valid_placements; assert_one_open_period_per_worker"],
      ["The natural key is source system plus worker ID; reused IDs stay separate workers", "unique_combination on stg_worker_master; test_ids_reused_across_systems_stay_separate"],
      ["Blank, 9999-12-31 and 31/12/9999 all mean open-ended", "test_open_ended_spellings_all_mean_open"],
      ["Tenure follows the month-end rule on every documented edge case", "assert_tenure_fixtures_match; test_fixtures_agree_with_python_twin"],
      ["Tenure in the warehouse matches an independent Python implementation", "test_tenure_in_warehouse_matches_python_twin"],
      ["Headcount is the same total by employer, branch, region and band", "assert_headcount_reconciles"],
      ["The bridge from the naive count adds up to the as-of headcount", "assert_bridge_ends_at_headcount"],
      ["Branch region is the one in effect on the snapshot date", "test_branch_region_is_as_of"],
      ["Headcount and every continuous-service start match the generator's ground truth", "test_headcount_matches_ground_truth; test_continuous_service_start_for_every_worker"],
      ["Published marts and pages carry counts only, never worker keys, IDs or rows", "assert_no_worker_detail_in_published_marts; test_export_and_build"],
      ["Rebuilding from the same seed reproduces every mart", "make rebuild (analysis/fingerprint.py)"],
    ];
    document.getElementById("rules").innerHTML = `<ul class="insights">${rules.map(([r, w]) => `<li><span class="status good"><i aria-hidden="true">✓</i>Tested</span><span><b>${esc(r)}.</b> <code>${esc(w)}</code></span></li>`).join("")}</ul>`;
  }

  const PAGES = { overview, headcount, tenure, quality, checks };
  document.addEventListener("DOMContentLoaded", () => {
    if (!window.echarts) { document.querySelector("main").insertAdjacentHTML("afterbegin", '<p class="callout critical">Charts could not load (no network to the chart library). Tables still work.</p>'); }
    PAGES[document.body.dataset.page]();
  });
})();
