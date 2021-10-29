# accuracy를 다른 모델에서 받을 수 있게 하려면?

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from random import uniform
from datetime import datetime

default_args = {
    'start_date': datetime(2020, 1, 1)
}

def _training_model(ti): # task instance object : ti
    accuracy = uniform(0.1, 10.0) # accuracy 임의 랜덤 설정
    print(f'model\'s accuracy: {accuracy}')

    #return accuracy # Python Operator function에서 return을 하게 되면 자동으로 값이 XCOM에 Push 된다.
    # 단, 단순 retrun push를 하게 될 경우는 XCOM key 값이 return_value로 들어가게 되는데 키값을 넣으려면 다음을 수행한다.
    ti.xcom_push(key='model_accuracy', value=accuracy)
    # => XCOM을 push하는 방법은 return 키워드를 사용하거나 직접 task instance object의 xcom_push()를 통해 push 해주는 방법이 있다.

    # $ 참고할 점
    # 1. 여러 task는 한개의 XCOM key를 돌려쓸 수 있다.
    # 2. 같은 key를 같은 task id로 푸쉬할경우 값은 덮어씌워진다.

    # 정의 해주지 않았다고 하더라도 기본적으로 모든 Operator는 XCOM을 자동으로 푸시할 수 있다.
    # => 예를 들면 BashOperator의 경우 command가 실행되면 XCOM으로 신호를 준다.
    # => 자동 푸시를 하지 않도록 하려면 해당 Operator 내부에 do_xcom_push=False 를 설정한다. 

def _choose_best_model(ti): # task instance object : ti 
    print('choose best model')
    accuracies = ti.xcom_pull(key='model_accuracy', task_ids=['training_model_A', 'training_model_B', 'training_model_C']) 
    # key는 pull을 수행할 대상 XCOM의 key
    # 위의 경우 task 'training_model_A', 'training_model_B', 'training_model_C' 의 'model_accuracy'를 의미한다. 
    print(accuracies)
    return max(accuracies)


with DAG('xcom_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    downloading_data = BashOperator( # 3초 sleep을 데이터를 다운로드 하는 과정으로 친다.
        task_id='downloading_data',
        bash_command='sleep 3',
        do_xcom_push=False # 기본 push 되는 XCOM 신호 false
    )

    training_model_task = [ # trainning 모델 3개(A, B, C) task

        PythonOperator(
            task_id=f'training_model_{task}',
            python_callable=_training_model
        ) for task in ['A', 'B', 'C']] # 파이썬 Operator를 이용해 동적으로 테스크를 생성

    choose_model = PythonOperator(
        task_id='choose_model',
        python_callable=_choose_best_model
    )

    downloading_data >> training_model_task >> choose_model

# $ other tip

# 에어플로우는 spark 같은 data processing framework가 아니다. 데이터 전송이 많아지면 memory overflow error 가 출력될 것. 
# XCOM은 database에 따라 전송 용량이 제한된다. 
# 예를 들어 
# sql lite DB를 이용할 경우 2 GB로 제한.
# postgres를 이용할 경우 1 GB로 제한. 
# mysql을 사용할 경우 64 KB로 제한.
