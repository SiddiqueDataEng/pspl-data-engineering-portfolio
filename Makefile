.PHONY: all ingest spark-transform dbt-run dbt-test dbt-docs sql-kpis test clean airflow-install airflow-standalone docker-airflow-up datagenerator dashboard

all: ingest spark-transform dbt-run dbt-test sql-kpis

datagenerator:
	python datagenerator.py

ingest:
	python ingest/ingest.py

spark-transform:
	python -m jupyter nbconvert --to notebook --execute notebooks/delta_lake_operations.ipynb \
	    --output-dir notebooks --output delta_lake_operations_executed.ipynb

dbt-run:
	cd dbt && DELTA_LAKE_PATH="$(PWD)/delta_lake" dbt run

dbt-test:
	cd dbt && DELTA_LAKE_PATH="$(PWD)/delta_lake" dbt test

dbt-docs:
	cd dbt && DELTA_LAKE_PATH="$(PWD)/delta_lake" dbt docs generate && DELTA_LAKE_PATH="$(PWD)/delta_lake" dbt docs serve

sql-kpis:
	for f in sql/*.sql; do echo "Running $$f"; duckdb pspl.duckdb < $$f; done

test:
	pytest tests/ -v

clean:
	rm -rf delta_lake/ pspl.duckdb dbt/target/ dbt/dbt_packages/

airflow-install:
	./scripts/install-airflow.sh

airflow-standalone:
	export AIRFLOW_HOME="$(PWD)/airflow/airflow_home" && \
	export AIRFLOW__CORE__DAGS_FOLDER="$(PWD)/airflow/dags" && \
	export AIRFLOW__CORE__LOAD_EXAMPLES=False && \
	mkdir -p "$(PWD)/airflow/airflow_home" && \
	.venv/bin/airflow standalone

docker-airflow-up:
	docker compose -f docker-compose.airflow.yml up

dashboard:
	streamlit run dashboard/streamlit_app.py
