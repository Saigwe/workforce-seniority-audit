PY ?= python
DB ?= warehouse/workforce.duckdb

.PHONY: all ci data dbt rebuild test dashboards serve clean

all: data dbt dashboards                                  ## everything, under a minute
ci: data dbt rebuild test                                 ## what GitHub Actions runs

data:
	$(PY) generator/simulate.py --out data/raw

dbt:
	mkdir -p warehouse
	cd dbt && DUCKDB_PATH=../$(DB) dbt build --profiles-dir .

# Rebuild consistency: regenerate from the same seed and rebuild; the fingerprint of every gold mart must not change.
rebuild:
	$(PY) analysis/fingerprint.py --db $(DB) --out warehouse/fingerprint_1.json
	$(PY) generator/simulate.py --out data/raw
	cd dbt && DUCKDB_PATH=../$(DB) dbt build --profiles-dir . --full-refresh
	$(PY) analysis/fingerprint.py --db $(DB) --out warehouse/fingerprint_2.json --compare warehouse/fingerprint_1.json

test:
	WF_DB=$(DB) $(PY) -m pytest -q

dashboards:
	$(PY) dashboards/export.py --db $(DB) --out dashboards/site/data.json
	$(PY) dashboards/build.py
	$(PY) analysis/audit_report.py --db $(DB) --out analysis/audit_report.md

serve:
	$(PY) -m http.server 8000 --directory dashboards/site

clean:
	rm -rf warehouse data/raw dbt/target dbt/logs dashboards/site/data.json dashboards/site/data.js dashboards/site/*.html
