"""Fingerprint every gold mart (row count, a hash of the sorted non-float columns, sums of float columns), optionally comparing with an earlier one.

Usage: python analysis/fingerprint.py --db warehouse/workforce.duckdb --out fp.json [--compare earlier.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import duckdb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--compare")
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    marts = [r[0] for r in con.execute("select table_name from information_schema.tables where table_schema = 'gold' order by 1").fetchall()]
    fp = {}
    for m in marts:
        cur = con.execute(f"select * from gold.{m}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        isf = [any(isinstance(r[i], float) for r in rows) for i in range(len(cols))]
        keys = sorted(repr(tuple(v for v, f in zip(r, isf) if not f)) for r in rows)
        sums = {c: sum(r[i] for r in rows if r[i] is not None) for i, c in enumerate(cols) if isf[i]}
        fp[m] = {"rows": len(rows), "keys_sha1": hashlib.sha1("|".join(keys).encode()).hexdigest(), "sums": sums}
    con.close()
    Path(a.out).write_text(json.dumps(fp, indent=1), encoding="utf-8")
    print(f"fingerprinted {len(fp)} marts")
    if a.compare:
        old = json.loads(Path(a.compare).read_text(encoding="utf-8"))

        def same(x, y):  # parallel float sums differ in the last bits, so compare sums with a relative tolerance
            return (x["rows"] == y["rows"] and x["keys_sha1"] == y["keys_sha1"] and x["sums"].keys() == y["sums"].keys()
                    and all(abs(x["sums"][k] - y["sums"][k]) <= 1e-9 * max(1.0, abs(y["sums"][k])) for k in x["sums"]))
        diff = [m for m in fp if m not in old or not same(fp[m], old[m])]
        if diff:
            print("rebuild changed:", diff)
            sys.exit(1)
        print("rebuild identical")


if __name__ == "__main__":
    main()
