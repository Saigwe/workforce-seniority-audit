"""The export runs on the warehouse, every page renders from it, and no row-level worker data is published."""
import json
import subprocess
import sys

from conftest import DB, ROOT


def test_export_and_build(con, tmp_path):
    site = tmp_path / "site"
    (site / "assets").mkdir(parents=True)
    for f in ("style.css", "charts.js", "pages.js"):
        (site / "assets" / f).write_bytes((ROOT / "dashboards" / "site" / "assets" / f).read_bytes())
    data = site / "data.json"
    subprocess.run([sys.executable, str(ROOT / "dashboards" / "export.py"), "--db", str(DB), "--out", str(data)], check=True)
    text = data.read_text(encoding="utf-8")
    d = json.loads(text)
    for key in ("bridge", "monthly", "asof", "bands", "quality", "by_source", "formats", "fixtures", "recon", "extracts", "naive_emp"):
        assert d[key], key
    assert "worker_key" not in text and "worker_id" not in text and "record_id" not in text
    assert all(r["workers"] is None or r["workers"] >= 5 for r in d["cells"])
    subprocess.run([sys.executable, str(ROOT / "dashboards" / "build.py"), "--data", str(data), "--site", str(site)], check=True)
    assert sorted(p.name for p in site.glob("*.html")) == ["checks.html", "headcount.html", "index.html", "quality.html", "tenure.html"]
