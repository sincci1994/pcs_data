"""알림 공통 모듈 — 콜백 단일 진입점 (→ design/08 §7).

모든 DAG 의 on_failure_callback 은 이 모듈만 사용한다. 개별 DAG 에서 채널 API 직접 호출 금지.
채널 어댑터: 사내 메일·메신저 API — 엔드포인트가 env 에 없으면 로그로만 남긴다(로컬 검증).
원격 배선 시 PCS_NOTIFY_MAIL_API / PCS_NOTIFY_MSGR_API 만 채우면 된다 — 호출부 수정 없음.
"""
import json
import logging
import os
import urllib.request

log = logging.getLogger("pcs.notifier")

_CHANNELS = {
    "mail": "PCS_NOTIFY_MAIL_API",
    "messenger": "PCS_NOTIFY_MSGR_API",
}


def _post(url: str, payload: dict) -> None:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10)


def send(event: str, subject: str, body: str) -> None:
    """이벤트 발송 — on_failure / freshness 위반 / 드리프트 감지 / 재동기화 갭 공용."""
    payload = {"event": event, "subject": subject, "body": body}
    delivered = False
    for channel, env_key in _CHANNELS.items():
        url = os.environ.get(env_key, "").strip()
        if not url:
            continue
        try:
            _post(url, payload)
            delivered = True
        except Exception:  # 알림 실패가 파이프라인 실패를 덮어쓰면 안 된다
            log.exception("notifier: %s 채널 발송 실패", channel)
    if not delivered:
        log.error("[PCS-NOTIFY:%s] %s | %s", event, subject, body)


def on_failure(context) -> None:
    """Airflow on_failure_callback 규약 시그니처."""
    ti = context.get("task_instance")
    send(
        event="task_failure",
        subject=f"[Airflow 실패] {getattr(ti, 'dag_id', '?')}.{getattr(ti, 'task_id', '?')}",
        body=f"run_id={context.get('run_id')} logical_date={context.get('logical_date')} "
             f"exception={context.get('exception')}",
    )
