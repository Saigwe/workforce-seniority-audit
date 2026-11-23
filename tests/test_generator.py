"""Same seed, same data."""
import hashlib
import subprocess
import sys

import pandas as pd

from conftest import ROOT


def digest(d):
    h = hashlib.sha1()
    for name in ("placement_history", "worker_master", "branches"):
        h.update(pd.util.hash_pandas_object(pd.read_parquet(d / f"{name}.parquet"), index=False).values.tobytes())
    return h.hexdigest()


def test_same_seed_same_data(tmp_path):
    for run in ("a", "b"):
        subprocess.run([sys.executable, str(ROOT / "generator" / "simulate.py"), "--out", str(tmp_path / run)], check=True)
    assert digest(tmp_path / "a") == digest(tmp_path / "b")


def test_no_personal_fields(tmp_path):
    subprocess.run([sys.executable, str(ROOT / "generator" / "simulate.py"), "--out", str(tmp_path)], check=True)
    for f in tmp_path.glob("*.parquet"):
        cols = {c.lower() for c in pd.read_parquet(f).columns}
        assert not cols & {"name", "first_name", "last_name", "birth_date", "date_of_birth", "national_id", "email", "address"}
