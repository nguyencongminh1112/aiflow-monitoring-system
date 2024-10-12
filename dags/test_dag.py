from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    'owner': 'congminh.nguyen@onpoint.vn',
    'retries': 1,
    'retry_delay': timedelta(seconds=5),
    'email':  ['congminh.nguyen@onpoint.vn'],
    'email_on_failure': True,
    'email_on_retry': True
}

with DAG(
    dag_id = 'Email_test_dag',
    schedule = '* * * * *',
    start_date = datetime(2024, 7, 2),
    default_args = DEFAULT_ARGS,
    tags = ['airflow', 'failed', 'dags'],
    catchup = False
) as dag:
    
    task = BashOperator(
        task_id = 'fail_task',
        bash_command = 'cd non_exist_folder'
    )
    
    task
