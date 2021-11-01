
from airflow.decorators import task, dag
from airflow.providers.docker.operators.docker import DockerOperator
# 첫 번째로 airflow documentation 에서 apache-airflow-providers-docker를 설치한다.
# pip install apache-airflow-providers-docker

from datetime import datetime



@dag(start_date=datetime(2021, 1 ,1), schedule_interval='@daily', catchup=False)
def docker_dag():

    @task() # task를 어노테이션을 이용해서 만들 수도 있다.
    def t1():
        pass

    t2 = DockerOperator(
        task_id='t2',
        image='python:3.8-slim-buster',
        command='echo "command running in the docker container"',
        docker_url='unix://var/run/docker.sock',
        network_mode='bridge' # docker container 와 같은 네트워크를 사용한다면 host 사용.
    )
    t1() >> t2

dag = docker_dag()
