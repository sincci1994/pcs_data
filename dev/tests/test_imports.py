"""임포트 스모크 테스트 — 재구성 후 모듈 경로가 유효한지 검증.

Airflow 미설치 환경(로컬)에서도 돌도록, airflow 를 모듈 레벨에서 import 하는
extract.dagfactory / dags 는 제외한다(컨테이너 DAG 파싱 검증으로 커버).
"""
import importlib

import pytest

# airflow/oracledb 없이 import 가능한 모듈들 (지연 import 설계)
AIRFLOW_FREE_MODULES = [
    "common.connectors.base",
    "common.connectors.oracle",
    "common.control.ctl",
    "extract.modules.collectors.base_collector",
    "extract.projects.scada.scada_base",
    "extract.projects.scada.masters",
    "extract.projects.scada.trace",
    "extract.projects.scada.control",
]


@pytest.mark.parametrize("mod", AIRFLOW_FREE_MODULES)
def test_module_imports(mod):
    importlib.import_module(mod)


def test_scada_callables_exist():
    from extract.projects.scada.control import ctl_end, ctl_start
    from extract.projects.scada.masters import extract_masters
    from extract.projects.scada.trace import extract_trace

    for fn in (ctl_start, ctl_end, extract_masters, extract_trace):
        assert callable(fn)
