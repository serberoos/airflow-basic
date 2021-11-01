# BranchPythonOperator
# accurate 와 inaccurate 둘중에 한 분기를 선택해 실행하고 싶을 경우 BranchPythonOperator를 이용한다.

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import BranchPythonOperator
from datetime import datetime

default_args = {
    'start_date': datetime(2020, 1, 1)
}

def _choose_best_model(ti): # task id를 이용해 분기중 하나를 선택한다.
    accuracy = 6 # 임의의 accuracy 값을 6으로 준다.
    if accuracy > 5:
        return 'accurate'
    elif accuracy <= 5:
        return 'inaccurate' 
# 이 경우 XCOM은 두개가 푸쉬된다. accuracy 값이 6 이므로 
# * 'accurate'는 inaccutate가 PythonBranchOperator에 의해서 스킵되어 [Key : skipmixin_key Value : {'followed':['accurate']...}] XCOM 이 푸쉬되고
# * 'inaccurate'는 python_callable function에서 리턴 되어 [Key : return_value : accurate .........]이 푸쉬 된다.

# 이때 문제가 있는데 : xcom은 자동으로 제거 되지 않는다. 따로 제거 해주지 않으면 BranchPythonOperator가 실행되고 끝날 때마다 필요없는 xcom이 계속 쌓일 것이다.
# => Operator 기본 push를 막는 방법은 해당 Operator 내부에 do_xcom_push=False 옵션을 주어 해결할 수 있다.

with DAG('branching', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    choose_best_model = BranchPythonOperator( # BranchPythonOperator를 쓰면 리스트(맨아래 의존성 설정에 보면 알 수 있음)로 여러 task_id를 리턴할 수 있다.
        task_id='choose_best_model',
        python_callable=_choose_best_model,
        do_xcom_push=False
    )

    accurate = DummyOperator(
        task_id='accurate'
    )

    inaccurate = DummyOperator(
        task_id='inaccurate'
    )
    # 해당 stroing task와 연결된 이전 task 중 하나라도 skip될 경우 함께 연결된 storing도 스킵된다. (이 경우 'accurate'와 'inaccurate' 둘중에 한개는 스킵되므로 storing은 무조건 스킵된다.)
    # => storing task의 trigger rule을 변경하면 해결 할 수 있다.

    storing = DummyOperator(   
        task_id='storing',
        trigger_rule="none_failed_or_skipped" # 모든 부모 task가 전부 성공해야(의존성에 의해서) 자식 task가 실행되는 기본 trigger_rule을 변경한다. 
        # => 부모 task가 하나라도 성공하면 storing task는 실행될 수 있다.
    )

    choose_best_model >> [accurate, inaccurate] >> storing # 의존성 설정.