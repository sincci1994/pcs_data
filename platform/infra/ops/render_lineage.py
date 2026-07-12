"""render_lineage.py — 커밋 산출물에서 전 경로 계보 문서(transform/LINEAGE.md)를 생성.

입력(전부 커밋된 선언 — 런타임 조회 없음, 결정론):
  platform/extract/sources.yml  : 소스 테이블 → brz (extract 경로)
  transform/manifest.json       : brz(source) → slv → gld (ref 그래프) + meta.publish_to → 서빙

실행: platform/infra/ 에서  python ops/render_lineage.py   (manifest 갱신 시 함께 재생성·커밋)
표준 라이브러리만 사용 — sources.yml 은 extract/config.py 가 강제하는 제한 형식만 파싱한다.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ROOT / "platform" / "extract" / "sources.yml"
MANIFEST = ROOT / "transform" / "manifest.json"
OUT = ROOT / "transform" / "LINEAGE.md"

_TOP = re.compile(r"^([a-z0-9_]+):\s*(?:#.*)?$")
_KV = re.compile(r"^\s+(table|target)\s*:\s*([a-z0-9_.]+)")


def parse_sources():
    """sources.yml 에서 (소스 이름, table, target) 만 추출 — 제한 형식 전제."""
    out, cur = {}, None
    for line in SOURCES.read_text(encoding="utf-8").splitlines():
        m = _TOP.match(line)
        if m:
            cur = m.group(1)
            out[cur] = {}
            continue
        m = _KV.match(line)
        if m and cur:
            out[cur][m.group(1)] = m.group(2)
    return {k: v for k, v in out.items() if "table" in v and "target" in v}


def nid(name: str) -> str:
    return name.replace(".", "_").replace("-", "_")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sources = parse_sources()

    # manifest 노드: 운영 모델/시드만 (sbx 실험 계층은 계보 문서에서 제외)
    nodes = {
        k: n for k, n in manifest["nodes"].items()
        if n["resource_type"] in ("model", "seed") and n.get("schema") != "sbx"
    }
    mf_sources = manifest.get("sources", {})  # brz 테이블 선언

    lines = ["flowchart LR"]

    # 소스(운영 DB) → brz : sources.yml
    lines.append('  subgraph SRC["소스 (운영 DB — 로컬 대역: src)"]')
    for name, s in sorted(sources.items()):
        lines.append(f'    {nid(s["table"])}["{s["table"]}"]')
    lines.append("  end")

    lines.append('  subgraph BRZ["brz (원본 보존)"]')
    for key, s in sorted(mf_sources.items()):
        lines.append(f'    {nid(key)}["{s["schema"]}.{s["name"]}"]')
    for name, s in sorted(sources.items()):
        target_ids = [nid(k) for k, ms in mf_sources.items()
                      if f'{ms["schema"]}.{ms["name"]}' == s["target"]]
        tid = target_ids[0] if target_ids else nid(s["target"])
        if not target_ids:
            lines.append(f'    {tid}["{s["target"]}"]')
        lines.append(f'    %% extract: {name}')
    lines.append("  end")

    by_schema = {}
    for key, n in nodes.items():
        by_schema.setdefault(n["schema"], []).append((key, n))
    for schema in [s for s in ("slv", "gld") if s in by_schema]:
        title = {"slv": "slv (표준화)", "gld": "gld (데이터 제품)"}[schema]
        lines.append(f'  subgraph {schema.upper()}["{title}"]')
        for key, n in sorted(by_schema[schema]):
            lines.append(f'    {nid(key)}["{n["schema"]}.{n["name"]}"]')
        lines.append("  end")
    extra = sorted(set(by_schema) - {"slv", "gld"})
    for schema in extra:  # 시드 등
        lines.append(f'  subgraph {schema.upper()}_X["{schema}"]')
        for key, n in sorted(by_schema[schema]):
            lines.append(f'    {nid(key)}["{n["schema"]}.{n["name"]}"]')
        lines.append("  end")

    # 서빙 (publish_to 선언)
    published = {k: n["config"].get("meta", {}).get("publish_to")
                 for k, n in nodes.items() if n["config"].get("meta", {}).get("publish_to")}
    if published:
        lines.append('  subgraph SRV["서빙 (Oracle — 소비 조회 단일 창구, → design/08 §1.1)"]')
        for key, target in sorted(published.items()):
            lines.append(f'    srv_{nid(key)}["{target}"]')
        lines.append("  end")

    # 간선
    for name, s in sorted(sources.items()):
        target_ids = [nid(k) for k, ms in mf_sources.items()
                      if f'{ms["schema"]}.{ms["name"]}' == s["target"]]
        tid = target_ids[0] if target_ids else nid(s["target"])
        lines.append(f'  {nid(s["table"])} -->|extract__{name}| {tid}')
    for key, n in sorted(nodes.items()):
        for dep in n["depends_on"].get("nodes", []):
            if dep in nodes or dep in mf_sources:
                lines.append(f"  {nid(dep)} --> {nid(key)}")
    for key, target in sorted(published.items()):
        lines.append(f"  {nid(key)} -->|publish| srv_{nid(key)}")

    mermaid = "\n".join(lines)
    OUT.write_text(
        "# LINEAGE — 전 경로 계보 (자동 생성 — 직접 수정 금지)\n\n"
        "생성: `platform/infra/` 에서 `python ops/render_lineage.py` — manifest 갱신 시 함께 재생성한다.\n"
        "실행 순서·의존은 Airflow `manager__pcs_transform` Graph, 테이블 계보는 OpenMetadata 리니지가 정본이고,\n"
        "이 문서는 오프라인·코드리뷰용 스냅샷이다 (→ GUIDE.md §계보·의존성 어디서 보나).\n\n"
        "```mermaid\n" + mermaid + "\n```\n",
        encoding="utf-8",
    )
    print(f"OK: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
