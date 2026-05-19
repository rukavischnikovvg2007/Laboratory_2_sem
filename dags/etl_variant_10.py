from airflow import DAG
from airflow.operators.bash import BashOperator
import pendulum

PROJECT_DIR = "/opt/airflow"
CONFIG = f"{PROJECT_DIR}/configs/variant_10.yml"

default_args = {
    "owner": "student",
    "retries": 1,
    "retry_delay": 5,
}

with DAG(
    dag_id="etl_variant_10",
    start_date=pendulum.datetime(2026, 5, 19, tz="UTC"),
    schedule="*/5 * * * *",
    catchup=False,
    default_args=default_args,
    tags=["semester2", "etl", "week12"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command=f"""
        python {PROJECT_DIR}/src/extract.py \
        --config {CONFIG} \
        --run_date {{{{ ds }}}} \
        --start "{{{{ data_interval_start }}}}" \
        --end "{{{{ data_interval_end }}}}"
        """,
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=f"""
        python {PROJECT_DIR}/src/transform.py \
        --config {CONFIG} \
        --run_date {{{{ ds }}}} \
        --start "{{{{ data_interval_start }}}}" \
        --end "{{{{ data_interval_end }}}}"
        """,
    )

    dq = BashOperator(
        task_id="dq",
        bash_command=f"""
        python {PROJECT_DIR}/src/dq.py \
        --config {CONFIG} \
        --run_date {{{{ ds }}}} \
        --start "{{{{ data_interval_start }}}}" \
        --end "{{{{ data_interval_end }}}}"
        """,
    )

    load = BashOperator(
        task_id="load",
        bash_command=f"""
        python {PROJECT_DIR}/src/load_to_postgres.py \
        --config {CONFIG} \
        --run_date {{{{ ds }}}} \
        --start "{{{{ data_interval_start }}}}" \
        --end "{{{{ data_interval_end }}}}"
        """,
    )

    extract >> transform >> dq >> load
