#sensor는 무엇인가가 벌어졌는지 (조건이 true인지 false 인지) 판단하고 벌어졌다면 실행한다.
# * 특정 위치에 파일이 들어갔는가? : FileSensor
# * s3 key가 s3 bucker에 들어갔는가? : S3KeySensor = Amazon AWS 관련..
# * sql record가 table 안에 들어갔는가? : SqlSensor
# * 다른 DAG가 실행이 완료될 때까지 기다리고 싶은가? : ExternalTaskSensor

# AIRFLOW에는 이 외에도 더 많은 SENSOR들이 존재한다.
from airflow.models import DAG

from datetime import datetime
from airflow.sensors.filesystem import FileSensor

with DAG('dag_sensor', schedule_interval='@daily', start_date=datetime, default_args = default_args, catchup=False) as dag:
    default_args = {}
    waiting_for_file = FileSensor(

        # 1. poke_interval : 파일이 있는지 판단하는 연산의 주기
        task_id='waiting_for_file',
        poke_interval=30, # 30초 마다 파일이 있는지 확인한다. 
        # 시간은 경우에 따라 다르지만 짧게 줄수록 많은 연산량이 필요하다.
        # SqlSensor의 경우 시간이 한 텀 지날 때마다 데이터베이스에 접근을 해야됨.
        # 일주일을 켜놓는다면 일주일마다 30초 지날때마다 연산이 필요하고 이는 매우 크다. => 또한 Worker가 지속적으로 메모리에 상주하게 됨.
        timeout = 60 * 5, # 파일이 있는지 확인하는 최대 시간을 설정하면 해결할 수 있음.
        # timeout은 poke_interval값 보다는 큰 값을 주어야 한다. 

        # timeout을 설정해주지 않는다면 sensor가 실행 시마다 쌓여 deadlock이 발생한다.

        #mode ='poke' # 기본값은 poke
        mode='reschedule', # 다른 interval 시간 중에 worker slot은 센서에 의해 점유되고 다른 센서가 켜질수 있게 release 된다.
        soft_fail=False # defalut = false / time_out 시간 동안 아무일도 없으면 센서를 스킵한다. True | execution timeout
    )
