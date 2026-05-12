from airflow import DAG
from datetime import datetime

with DAG(
    dag_id="demo_broken",
    start_date=datetime.now(),
    schedule="@daily",
    catchup=True,
):
    pass