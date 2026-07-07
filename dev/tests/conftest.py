"""pytest 부트스트랩 — 런타임 코드 루트를 sys.path 에 주입.

폐쇄망 전략상 설치형 패키지를 쓰지 않는다(PYTHONPATH-루트, design/adr/0003).
컨테이너에서는 /opt/airflow 아래에 extract/·common/ 이 마운트되지만,
호스트 트리는 역할 기반이라 platform/ 아래에 있다 → platform/ 을 주입해
`extract.*`·`common.*` 임포트를 컨테이너와 동일하게 해석한다. (adr/0004)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "platform"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
