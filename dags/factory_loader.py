"""configs/ 의 모든 YAML 을 DAG 으로 자동 로드 (단 3줄).

(주의) Airflow DAG 파일로 인식되려면 파일 내에 'airflow' 와 'dag' 문자열이 모두 있어야 한다
(DagBag safe_mode). 이 docstring 이 그 조건을 만족시킨다.
"""
import os

from dagfactory import load_yaml_dags

load_yaml_dags(globals(), os.path.join(os.path.dirname(__file__), "configs"))
