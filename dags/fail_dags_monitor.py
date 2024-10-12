from io import StringIO
import pandas as pd
from pandas import json_normalize
import pendulum
import psycopg2
from datetime import timedelta
import time
from airflow.models import DAG
from airflow.models.dagbag import DagBag
from airflow.models.dagrun import DagRun
from airflow.operators.python import PythonOperator
import json


LOCAL_TIMEZONE = pendulum.timezone("Asia/Ho_Chi_Minh")
LAST_INTERVAL = DagRun.get_latest_runs
DEFAULT_ARGS = {
    'owner': 'congminh.nguyen@onpoint.vn',
    'retries': 2,
    'retry_delay': timedelta(seconds=5) 
}

with DAG(
    dag_id = 'Fail_Dags_Monitor',
    default_args = DEFAULT_ARGS,
    schedule = '15 * * * *',
    start_date = pendulum.datetime(2021, 1, 1, tz = LOCAL_TIMEZONE),
    catchup = False,
    tags = ['monitor', 'airflow', 'failed', 'dags']
) as dag:
    pass


    def get_failed_dag(state,**kwargs):
        dag_ids = DagBag(include_examples=False).dag_ids
        dag_runs = list()
        for id in dag_ids: 
            state = state.lower() if state else None
            for run in DagRun.find(id, state=state):
                if run.end_date:
                    dag_runs.append({
                    'id': run.id,
                    'run_id': run.run_id,
                    'state': run.state,
                    'dag_id': run.dag_id,
                    'run_type': run.run_type,
                    'execution_date': run.execution_date.isoformat(),
                    'start_date': ((run.start_date or '') and
                            run.start_date.isoformat()),
                    'end_date': ((run.end_date or '') and
                            run.end_date.isoformat())
            })
        return list(dag_runs)
    
    def get_log(state):
        log = get_failed_dag(state)
        log_file = json.dumps(log)
        return log_file
        
    # def load(state): 
    #     log_file = json.loads(get_log(state))
    #     df_final = pd.DataFrame(log_file)
    #     conn = psycopg2.connect(database=DB_NAME,
    #                     user=DB_USER,
    #                     password=DB_PASS,
    #                     host=DB_HOST,
    #                     port=DB_PORT)

    #     print('Successfully connect to database!')

    #     start_time = time.time()
    #     sio = StringIO()
    #     df_final.to_csv(sio, index=None, header=None)
    #     sio.seek(0)
    #     with conn.cursor() as c:
    #         c.copy_expert(
    #             sql="""
    #             DELETE FROM athena_warehouse.dag_monitor_stat;

    #             COPY athena_warehouse.dag_monitor_stat (
    #                 id,
    #                 run_id,
    #                 state,
    #                 dag_id,
    #                 run_type,
    #                 execution_date,
    #                 start_date,
    #                 end_date
    #                 ) FROM STDIN WITH CSV""",
    #             file=sio
    #         )
    #         conn.commit()

    #     end_time = time.time()
    #     total_time = end_time - start_time
    #     print(f"Insert time: {total_time} seconds")


    failed_dag = PythonOperator(
        task_id="get_failed_dag",
        python_callable=get_failed_dag,
        op_kwargs={'state': 'FAILED'},
        dag=dag
    )
    
    save_log = PythonOperator(
        task_id="get_log",
        python_callable=get_log,
        op_kwargs={'state': 'FAILED'},
        dag=dag
    )
    
    # write = PythonOperator(
    #     task_id="load",
    #     python_callable=load,
    #     op_kwargs={'state': 'FAILED'},
    #     dag=dag
    # )

failed_dag >> save_log