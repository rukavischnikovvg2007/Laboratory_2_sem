import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow"
CONFIG = f"{PROJECT_DIR}/configs/variant_10.yml"

default_args = {
    "owner": "student",
    "retries": 1,
    "retry_delay": 5,
}

with DAG(
    dag_id="etl_variant_10",
    start_date=pendulum.today('UTC').add(days=-1),
    schedule="*/5 * * * *",
    catchup=False,
    default_args=default_args,
    tags=["semester2", "etl", "week11"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command=f"cd {PROJECT_DIR} && python {PROJECT_DIR}/src/extract.py {CONFIG}",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=f"cd {PROJECT_DIR} && python {PROJECT_DIR}/src/transform.py {CONFIG}",
    )

    load = BashOperator(
        task_id="load",
        bash_command=f"cd {PROJECT_DIR} && python {PROJECT_DIR}/src/load_to_postgres.py {CONFIG}",
)

    dq = BashOperator(
        task_id="dq",
        bash_command=f"cd {PROJECT_DIR} && python {PROJECT_DIR}/src/dq.py {CONFIG}",
    )

    extract >> transform >> load >> dq
