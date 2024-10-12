import pendulum
from datetime import timedelta
from airflow import settings
from airflow.models import clear_task_instances, DAG, TaskInstance, Variable
from airflow.operators.python import PythonOperator
from airflow.utils.state import State
from datetime import datetime
import logging

LOCAL_TIMEZONE = pendulum.timezone("Asia/Ho_Chi_Minh")
HOUR = 3600
DEFAULT_ARGS = {
    'owner': 'congminh.nguyen@ponpoint.vn',
    'retries': 2,
    'retry_delay': timedelta(seconds=5) 
}

with DAG(
    dag_id = 'Extend_Run_Dags_Monitor',
    default_args = DEFAULT_ARGS,
    schedule = '15 * * * *',
    start_date = pendulum.datetime(2021, 1, 1, tz = LOCAL_TIMEZONE),
    catchup = False,
    tags = ['monitor', 'airflow']
) as dag:
    pass

    def search_and_stop_long_tasks():

        session = settings.Session()
        max_running_time = int(Variable.get("max_running_time", default_var=0.5))
        logging.info(f'max_running_time: {max_running_time}')

        tis = []
        for task in session.query(TaskInstance) \
                .filter(TaskInstance.state == State.RUNNING) \
                .all():
            delta = datetime.now(LOCAL_TIMEZONE) - task.start_date
            if divmod(delta.total_seconds(), HOUR)[0] > max_running_time:
                logging.info(f'task_id: {task.task_id}, dag_id: {task.dag_id}, start_date: {task.start_date}, '
                            f'job_id: {task.job_id}, pid: {task.pid}, hostname: {task.hostname}, unixname: {task.unixname}')
                tis.append(task)

        if tis:
            logging.info(f'Sending this tasks to shutdown: {[t.task_id for t in tis]}')
            clear_task_instances(tis, session)
        else:
            logging.info('Nothing to clean')
    
    long_running_dag = PythonOperator(
        task_id='stop_long_running_tasks',
        python_callable=search_and_stop_long_tasks, 
        dag=dag)
    