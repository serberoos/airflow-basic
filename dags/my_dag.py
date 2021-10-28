from airflow import DAG # DAG
from datetime import datetime # 데이터 파이프라인은 스케줄링 된 시작날짜를 예측.

from airflow.operators.python import PythonOperator # 파이썬 함수 실행할 수 있는 Operator
from random import randint

from airflow.operators.python import BranchPythonOperator # task들의 branch를 설정해줄 수 있는 Operator

from airflow.operators.bash import BashOperator # Bash Command를 실행 시킬 수 있는 Operator

def _training_model(): # 임의로 accuracy를 정해서 리턴합니다.
    return randint(1, 10)
    # task 간의 통신은 xcom이 수행하며 
    # 첫째로, 위 randint 값은 자동으로 airflow meta DB에 push 된다.
    # 둘째로, DB내부의 값은 DAG 내부의 다른 테스크로 가져갈 수 있다.

def _choose_best_model(ti): # task instance object : ti | DB에서 값 가져오기.
    accuracies = ti.xcom_pull(task_ids=[ # DB에서 task값 3개 리스트 형태로 pull 받기!
        'training_model_A', 
        'training_model_B',
        'training_model_C'
    ])

    best_accuracy = max(accuracies) # 모델 3개 중 가장 높은 best_accuracy 구하기 

    if best_accuracy > 8:
        return 'accurate' # task_id 실행 
    else:
        return 'inaccurate' #task_id 실행 

with DAG("my_dag", start_date = datetime(2021, 1, 1),schedule_interval="@daily", catchup=False) as dag: 
    # parameter 1. dagId : 고유 식별자
    # parameter 2. start date : 시작 스케줄 = 2021, 1, 1 경우 해당 날짜에 실행됨.
    # parameter 3. schedule interval : dag가 trigger 될 빈도를 정의한다. (주기적 실행) = unix의 cron식
        # => 위의 DAG는 2021/1/1(start date)부터 매일(schedule_interval) 실행 되고 실행 시점은 2021/1/1 자정임.
    # parameter 4. catchup : Dag의 전체 lifetime을 확인하면서 실행되지 않은 DAG를 실행 시킨다. 
        # => true 면 2015년 부터면 2015년 부터 실행되지 않은 DAG를 전부 실행.
        # => false 면 현재 시점부터 실행.

    training_model_A = PythonOperator(
        task_id = "training_model_A",
        python_callable=_training_model
        )

    training_model_B = PythonOperator(
        task_id = "training_model_B",
        python_callable=_training_model
        )

    training_model_C = PythonOperator(
        task_id = "training_model_C",
        python_callable=_training_model
        )

    choose_best_model = BranchPythonOperator(
        task_id="choose_best_model",
        python_callable=_choose_best_model
    )

    accurate = BashOperator( # accuracy가 임계점 위일 경우
        task_id="accurate",
        bash_command="echo 'accurate'"
    )
    inaccurate = BashOperator( # accuracy가 임계점 아래일 경우 
        task_id="inaccurate",
        bash_command="echo 'inaccurate'"
    )

    # 이하는 비트 연산자를 이용해 각 테스크에 대한 순차적 의존성을 정의한다. Web에서 의존성은 화살표로 표현된다.
    # web dag페이지 좌 상단 스위치를 누르면 dag가 trigger 되어 work flow가 실행된다.

    [training_model_A,training_model_B,training_model_C] >> choose_best_model >> [accurate, inaccurate]