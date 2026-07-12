#!/usr/bin/env bash
# airgap_images.sh — 폐쇄망 반입용 Docker 이미지 번들러 (레지스트리 없음, 절차 → ops/README.md)
#   프록시 서버:  ./ops/airgap_images.sh save   # 빌드 + 순차 pull → dist/pcs-images.tgz
#   (파일 전송)   scp dist/pcs-images.tgz <target>:/opt/pcs/dist/
#   타겟 서버:    ./ops/airgap_images.sh load   # docker load ← dist/pcs-images.tgz
#   어디서나:     ./ops/airgap_images.sh list   # 반입 대상 이미지 목록만 출력
set -euo pipefail
INFRA="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # compose 위치 = platform/infra
cd "$INFRA"
DIST="$INFRA/dist"; TARBALL="$DIST/pcs-images.tgz"; MANIFEST="$DIST/manifest.txt"

# COMPOSE_PROFILES 강제 무효화 — practice-oracle(로컬 실습) 이미지가 번들에 섞이는 것을 차단
images() { COMPOSE_PROFILES="" docker compose config --images | sort -u; }

cmd_list() { images; }

cmd_save() {
  mkdir -p "$DIST"
  docker compose build                    # build: 서비스(pcs-ingestion) — 베이스 pull 포함
  # pull 전용 이미지는 순차 pull — getcollate 레지스트리 동시 pull 시 429 (→ infra/README 함정 1)
  local img
  for img in $(images); do
    docker image inspect "$img" >/dev/null 2>&1 || docker pull "$img"
  done
  local imgs; imgs="$(images)"
  # shellcheck disable=SC2086  # 이미지 목록은 공백 분리 다중 인자 의도
  docker image inspect $imgs --format '{{ index .RepoTags 0 }}@{{ .Id }}' > "$MANIFEST"
  docker save $imgs | gzip > "$TARBALL"
  echo "OK: $TARBALL ($(du -h "$TARBALL" | cut -f1)) — 목록: $MANIFEST"
}

cmd_load() {
  [ -f "$TARBALL" ] || { echo "!! $TARBALL 없음 — 프록시 서버 save 산출물을 dist/ 에 반입하라" >&2; exit 1; }
  docker load < "$TARBALL"
}

case "${1:-}" in
  save) cmd_save ;; load) cmd_load ;; list) cmd_list ;;
  *) echo "usage: $0 {save|load|list}" >&2; exit 2 ;;
esac
