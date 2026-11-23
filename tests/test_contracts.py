"""Every raw file meets its source contract: columns, all text, grain."""
import duckdb
import pyarrow.parquet as pq
import pytest
import yaml

from conftest import RAW, ROOT

CONTRACTS = yaml.safe_load((ROOT / "contracts" / "sources.yml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("table", sorted(CONTRACTS))
def test_contract(table):
    f = RAW / f"{table}.parquet"
    if not f.exists():
        pytest.skip("run `make data` first")
    spec = CONTRACTS[table]
    schema = pq.read_schema(f)
    assert list(schema.names) == spec["columns"]
    for c in spec["columns"]:
        assert str(schema.field(c).type) in ("string", "large_string"), f"{table}.{c} must arrive as text"
    p = f.as_posix()
    assert duckdb.sql(f"select count(*) from (select {', '.join(spec['grain'])} from '{p}' group by all having count(*) > 1)").fetchone()[0] == 0
