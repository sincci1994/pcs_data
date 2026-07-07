"""수집기 ABC — 모든 적재 패턴이 공유하는 고정 run() 템플릿.

레퍼런스(coldchainservice_airflow)의 APICollector 패턴을 PCS 로 이식.
서브클래스는 추상 메서드만 오버라이드하고, run() 흐름은 고정한다:

    fetch → pre_validate → preprocess → post_validate → load

이 클래스 자체는 엔진/소스 중립이며 결정론적이다(LLM 개입 없음).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class CollectResult:
    target: str
    row_count: int
    meta: Mapping[str, Any] = field(default_factory=dict)


class Collector(ABC):
    """단일 소스 객체(테이블/파일/엔드포인트) 1개를 적재하는 재사용 단위."""

    #: 적재 대상(스테이징/LND) 식별자. 서브클래스에서 지정.
    target: str = ""

    @abstractmethod
    def fetch(self, **context) -> Any:
        """원천에서 원시 payload 를 가져온다."""

    def pre_validate(self, payload: Any) -> Any:
        return payload

    def preprocess(self, payload: Any) -> Any:
        return payload

    def post_validate(self, payload: Any) -> Any:
        return payload

    @abstractmethod
    def load(self, payload: Any, **context) -> CollectResult:
        """가공된 payload 를 대상 스토리지에 적재."""

    def run(self, **context) -> CollectResult:
        payload = self.fetch(**context)
        payload = self.pre_validate(payload)
        payload = self.preprocess(payload)
        payload = self.post_validate(payload)
        return self.load(payload, **context)
