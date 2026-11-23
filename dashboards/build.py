"""Write the five dashboard pages and data.js. Run export.py first.

Usage: python dashboards/build.py [--data dashboards/site/data.json] [--site dashboards/site]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ECHARTS = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"
REPO = "https://github.com/Saigwe/workforce-seniority-audit"

PAGES = [
    ("index.html", "overview", "Overview"),
    ("headcount.html", "headcount", "Headcount"),
    ("tenure.html", "tenure", "Seniority"),
    ("quality.html", "quality", "Data quality"),
    ("checks.html", "checks", "Checks"),
]


def card(cid: str, title: str, sub: str, src: str = "", wide: bool = False, tall: bool = False, chart: bool = True, extra: str = "") -> str:
    return f'''
    <section class="card{' wide' if wide else ''}" id="{cid}">
      <header><div><h2>{title}</h2><p class="sub">{sub}</p></div>{'<button class="tbl-btn" type="button" aria-pressed="false">Table</button>' if chart else ''}</header>
      {extra}{f'<div class="chart{" tall" if tall else ""}" role="img" aria-label="{title}"></div>' if chart else ''}
      <div class="table-view" hidden></div>
      <p class="src">{src or "Source: dbt gold marts on DuckDB"}</p>
    </section>'''


def scope(text: str) -> str:
    return f'\n  <div class="filters"><span class="scope">{text}</span></div>'


GRID_OPEN, GRID_CLOSE = '\n  <div class="tiles" id="tiles"></div>\n  <div class="grid">', '\n  </div>'
SCOPE = ("Meridian Workforce Services (fictional): ten client employers, two payroll systems. As of 31 October 2026. "
         "Counts only; no worker rows are published. Cells under five workers are suppressed. Synthetic data.")

BODIES = {
    "overview": ("One headcount question, answered twice",
                 "How many workers did we have on 31 October 2026, and how long have they served? Counting open rows gives one answer; effective dates and explicit rejections give another.",
                 scope(SCOPE) + GRID_OPEN +
                 card("ov-stories", "What changes the answer", "Each links to the page with the evidence.", "Computed from every page", wide=True, chart=False,
                      extra='<ul class="insights" id="insights"></ul>') +
                 card("ov-bridge", "From open rows to as-of headcount", "Count after each rule is applied, in order", wide=True) +
                 card("ov-emp", "Naive against as-of, by employer", "Open history rows against workers placed on 31 October") +
                 card("ov-bands", "Seniority bands on 31 October", "Continuous service with the current employer") +
                 GRID_CLOSE),
    "headcount": ("Headcount",
                  "Workers holding a valid placement on each month-end, by employer, branch region and contract.",
                  scope("Effective-dated: a placement counts on a month-end if it started on or before that day and ends on or after it. "
                        "Branch regions are the ones in effect that month.") + GRID_OPEN +
                  card("hc-trend", "Headcount at each month-end", "All employers, January 2023 to October 2026", wide=True) +
                  card("hc-emp", "By employer, 31 October 2026", "Workers placed") +
                  card("hc-region", "By branch region, 31 October 2026", "Unassigned: placements with no branch recorded") +
                  card("hc-recon", "The total under every filter", "Eligible headcount must not change with the cut", chart=False, extra='<div id="recon" class="table-view"></div>') +
                  card("hc-missing", "Missing branch assignments", "Workers on 31 October whose placement has no branch") +
                  GRID_CLOSE),
    "tenure": ("Seniority",
               "Completed months of continuous service with the current employer, and the workers we cannot calculate it for.",
               scope("Continuous service: consecutive placements with the same employer, bridged across gaps of up to 31 days. "
                     "A longer gap or a move to another employer restarts it. A worker with any rejected history row has insufficient evidence.") + GRID_OPEN +
               card("tn-bands", "Tenure bands, 31 October 2026", "Share of workers", ) +
               card("tn-matrix", "Tenure band by employer", "Workers; cells under five suppressed", wide=True) +
               card("tn-fixtures", "The tenure rule on edge cases", "Month ends, leap days, future starts (dbt/seeds/tenure_fixtures.csv)", wide=True, chart=False,
                    extra='<div id="fixtures" class="table-view"></div>') +
               GRID_CLOSE),
    "quality": ("Data quality",
                "What the extracts contain, what was rejected and why, and what was only flagged.",
                scope("Each history row is valid or rejected for exactly one reason, checked in a fixed order. Flags do not reject a row.") + GRID_OPEN +
                card("dq-reasons", "Rejections and flags by rule", "Rows or workers affected", wide=True) +
                card("dq-source", "Rejection rate by payroll system", "Rejected rows over each system's deduplicated rows, by reason") +
                card("dq-formats", "How each system writes dates", "Format of the start date, all history rows") +
                card("dq-extracts", "Are the two master extracts the same?", "Same header and row count; compared field by field", chart=False, extra='<div id="extracts"></div>') +
                card("dq-audit", "Audit summary", "Every rule with its count and rate", wide=True, chart=False, extra='<div id="audit" class="table-view"></div>') +
                GRID_CLOSE),
    "checks": ("Checks",
               "The rules this warehouse enforces on every build, and where each is tested.",
               scope("dbt tests, source contracts and pytest run on every push; CI regenerates the data and checks the rebuild is identical.") + GRID_OPEN +
               card("ck-rules", "Rules", "Where each is tested", wide=True, chart=False, extra='<div id="rules"></div>') +
               GRID_CLOSE),
}


def ver(site: Path) -> str:
    h = hashlib.sha1()
    for f in ("assets/style.css", "assets/charts.js", "assets/pages.js", "data.js"):
        h.update((site / f).read_bytes())
    return h.hexdigest()[:10]


def page(key: str, v: str = "") -> str:
    title, lede, body = BODIES[key]
    nav = "".join(f'<a href="{f}"{" aria-current=page" if k == key else ""}>{label}</a>' for f, k, label in PAGES)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Workforce seniority audit</title>
<meta name="description" content="Effective-dated headcount, seniority and a data-quality audit of messy payroll extracts, on synthetic data.">
<link rel="stylesheet" href="assets/style.css?v={v}">
<script src="{ECHARTS}" defer></script>
<script src="assets/charts.js?v={v}" defer></script>
<script src="data.js?v={v}" defer></script>
<script src="assets/pages.js?v={v}" defer></script>
</head>
<body class="viz-root" data-page="{key}">
<div class="top"><div class="wrap">
  <div class="brand">Meridian Workforce Services <span>· seniority and data-quality audit · synthetic data</span></div>
  <nav class="tabs" aria-label="Dashboards">{nav}</nav>
  <button class="theme-btn" type="button">Dark mode</button>
</div></div>
<main class="wrap">
  <div class="page-head"><h1>{title}</h1><p>{lede}</p></div>
{body}
  <p class="footnote">Meridian Workforce Services, its client employers, branches, workers and every number here are invented. There are no names,
  birth dates or identifiers in this project. Demo results, not any company's figures. Built from dbt marts on DuckDB, rebuilt by CI on every change.
  Code: <a href="{REPO}">workforce-seniority-audit</a>. Built by <a href="https://saigwe.github.io">Stanley Igwe</a>.</p>
</main>
</body>
</html>
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "site" / "data.json"))
    ap.add_argument("--site", default=str(HERE / "site"))
    a = ap.parse_args()
    site = Path(a.site)
    data = json.loads(Path(a.data).read_text(encoding="utf-8"))
    (site / "data.js").write_text("window.DASH = " + json.dumps(data, separators=(",", ":")) + ";\n", encoding="utf-8")
    v = ver(site)
    for fname, key, _ in PAGES:
        (site / fname).write_text(page(key, v), encoding="utf-8", newline="\n")
    print(f"wrote {len(PAGES)} pages to {site}")


if __name__ == "__main__":
    main()
