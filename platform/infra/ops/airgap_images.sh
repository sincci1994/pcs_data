#!/usr/bin/env bash
# airgap_images.sh — 폐쇄망 반입용 Docker 이미지 번들러 (레지스트리 없음)
#
#   프록시 서버:  ./airgap_images.sh save     # 빌드/pull → dist/pcs-images.tgz
#   (파일 전송)   scp dist/pcs-images.tgz  target:/path/
#   타겟 서버:    ./airgap_images.sh load     # docker load ← dist/pcs-images.tgz
#   어디서나:     ./airgap_images.sh list     # 반입 대상 이미지 목록만 출력
#
# 이미지 목록은 루트 compose(=OM include 포함)에서 `docker compose config --images`
# 로 산출한다 → 버전 하드코딩/드리프트 없음. save/load 는 태그를 원형 보존하므로
# 타겟에서는 `docker compose up -d`(빌드/네트워크 없이)가 로컬 이미지를 그대로 쓴다.
#
# 주의:
#  - 프록시 빌드 서버와 타겟의 CPU 아키텍처가 같아야 한다(대개 linux/amd64).
#  - 타겟 기동엔 --build/--pull 금지(로드된 이미지 사용). 런타임 프록시 불필요.
set -euo pipefail

# 레포 루트로 이동 (이 스크립트는 platform/infra/ops/ 에 있다)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

DIST="$ROOT/dist"
TARBALL="$DIST/pcs-images.tgz"
MANIFEST="$DIST/manifest.txt"

images() { docker compose config --images | sort -u; }

cmd_list() { images; }

cmd_save() {
  mkdir -p "$DIST"
  echo ">> 코어 빌드 + OM pull (프록시 필요, 컨테이너는 안 띄움) ..."
  docker compose build                       # build: 있는 서비스 → pcs-airflow-practice:latest
  docker compose pull --ignore-buildable     # image: 전용 서비스만 pull (빌드 이미지 제외)

  local imgs; imgs="$(images)"
  echo ">> 반입 대상 이미지:"; echo "$imgs" | sed 's/^/   - /'

  echo ">> manifest 기록 → $MANIFEST"
  docker image inspect $imgs --format '{{ index .RepoTags 0 }}@{{ .Id }}' > "$MANIFEST"

  echo ">> docker save | gzip → $TARBALL (수 GB, 수 분 소요) ..."
  docker save $imgs | gzip > "$TARBALL"
  echo ">> 완료: $(du -h "$TARBALL" | cut -f1)  ($TARBALL)"
}

cmd_load() {
  [ -f "$TARBALL" ] || { echo "!! $TARBALL 없음 — 전송 파일을 dist/ 에 두세요" >&2; exit 1; }
  echo ">> docker load ← $TARBALL ..."
  docker load < "$TARBALL"
  echo ">> 로드 후 이미지 확인:"; images | sed 's/^/   - /'
  echo ">> 이제: docker compose up -d   (--build 금지)"
}

case "${1:-}" in
  save) cmd_save ;;
  load) cmd_load ;;
  list) cmd_list ;;
  *) echo "usage: $0 {save|load|list}" >&2; exit 2 ;;
esac
