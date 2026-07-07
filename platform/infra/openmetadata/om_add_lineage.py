#!/usr/bin/env python3
"""
dbt manifest 의 ref/source 의존성을 읽어 OpenMetadata 테이블 간 lineage 엣지를 직접 생성.
(OM 의 dbt 자동매칭이 Oracle 대소문자 불일치로 실패하므로, 테이블명 기준으로 직접 연결)
"""
import json
import urllib.request as U
import urllib.error

BASE = "http://localhost:8585/api"
# 스크립트가 platform/infra/openmetadata/ 에 위치 → 루트까지 세 단계 상위
MANIFEST = "../../../transform/dbt/target/manifest.json"


def call(method, path, body=None):
    d = json.dumps(body).encode() if body is not None else None
    r = U.Request(BASE + path, data=d, method=method)
    r.add_header("Content-Type", "application/json")
    r.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with U.urlopen(r) as x:
            t = x.read().decode()
            return x.status, (json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


# login
_d = json.dumps({"email": "admin@open-metadata.org", "password": "YWRtaW4="}).encode()
_r = U.Request(BASE + "/v1/users/login", data=_d, method="POST")
_r.add_header("Content-Type", "application/json")
TOKEN = json.loads(U.urlopen(_r).read())["accessToken"]

# OM 테이블 name(대문자) -> id
_, tb = call("GET", "/v1/tables?limit=1000")
name2id = {t["name"].upper(): t["id"]
           for t in tb["data"] if t["fullyQualifiedName"].startswith("pcs_oracle.")}
print("OM tables:", len(name2id))

# manifest 로드 + unique_id -> 테이블명(대문자)
m = json.load(open(MANIFEST, encoding="utf-8"))
uid2name = {}
for uid, n in m.get("nodes", {}).items():
    if n.get("resource_type") in ("model", "seed"):
        uid2name[uid] = n["name"].upper()
for uid, s in m.get("sources", {}).items():
    uid2name[uid] = s["name"].upper()

# 엣지 수집: dep -> node
edges = set()
for uid, n in m.get("nodes", {}).items():
    if n.get("resource_type") not in ("model", "seed"):
        continue
    tgt = uid2name.get(uid)
    for dep in n.get("depends_on", {}).get("nodes", []):
        src = uid2name.get(dep)
        if src and tgt and src in name2id and tgt in name2id and src != tgt:
            edges.add((src, tgt))

ok = 0
for src, tgt in sorted(edges):
    st, _ = call("PUT", "/v1/lineage", {"edge": {
        "fromEntity": {"id": name2id[src], "type": "table"},
        "toEntity": {"id": name2id[tgt], "type": "table"},
    }})
    mark = "OK" if st < 300 else f"ERR({st})"
    print(f"  {src} -> {tgt}: {mark}")
    if st < 300:
        ok += 1
print(f"DONE: {ok}/{len(edges)} lineage edges created")
