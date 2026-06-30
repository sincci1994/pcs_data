#!/usr/bin/env python3
"""
OpenMetadata 비즈니스 온톨로지 구성:
  - PCS 7도메인을 Domains 로 등록
  - 인제스트된 pcs_oracle 테이블을 이름 휴리스틱으로 ❶/❷ 도메인에 귀속
  - 업무 용어 Glossary 생성
host python(stdlib urllib)으로 localhost:8585 OM API 호출.
"""
import json
import urllib.request as U

BASE = "http://localhost:8585/api"
TOKEN = ""  # 로그인 후 채워짐


def req(method, path, body=None, ctype="application/json"):
    data = json.dumps(body).encode() if body is not None else None
    r = U.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", ctype)
    if TOKEN:
        r.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with U.urlopen(r) as resp:
            t = resp.read().decode()
            return resp.status, (json.loads(t) if t else {})
    except U.HTTPError as e:
        return e.code, e.read().decode()[:300]


# 1) 로그인
_, login = req("POST", "/v1/users/login",
               {"email": "admin@open-metadata.org", "password": "YWRtaW4="})
TOKEN = login["accessToken"]
print("login OK")

# 2) 7 도메인
DOMAINS = [
    ("01-EquipmentMaster",     "❶ 설비 마스터·자산",        "EAM·SMDM·AMS·EDCP·S5D·FRM·SETTI"),
    ("02-EquipmentPerformance","❷ 설비 가동·성능",          "EES·FDC·TPSS·YMS·iEES·SIMAX·SMAS"),
    ("03-WorkMaintenance",     "❸ 작업·정비",               "G-EMS·CPMS"),
    ("04-SafetyEnvCompliance", "❹ 안전·환경·컴플라이언스",   "EHS·SMCS·IDPS·iEES·인프라WP·PEPS"),
    ("05-Procurement",         "❺ 조달·협력사",             "BQMS·GPMS·SETTI·PEPS"),
    ("06-CostBudget",          "❻ 비용·예산",               "NERP·SMAS"),
    ("07-StandardInnovation",  "❼ 표준·혁신",               "SMDM·S5D·FRM"),
]
dom_id = {}
for name, disp, desc in DOMAINS:
    st, r = req("PUT", "/v1/domains", {
        "name": name, "displayName": disp,
        "description": desc, "domainType": "Aggregate",
    })
    if isinstance(r, dict) and r.get("id"):
        dom_id[name] = r["id"]
    print(f"domain {name}: {st}")

EQ = dom_id["01-EquipmentMaster"]
PF = dom_id["02-EquipmentPerformance"]

# 3) pcs_oracle 테이블 목록 → 이름으로 도메인 귀속
_, tbls = req("GET", "/v1/tables?limit=1000")
rows = tbls.get("data", []) if isinstance(tbls, dict) else []
assigned = {"01": [], "02": []}
for t in rows:
    fqn = t.get("fullyQualifiedName", "")
    if not fqn.startswith("pcs_oracle."):
        continue
    nm = t["name"].upper()
    if any(k in nm for k in ("SENSOR", "TRACE", "KPI")):
        target, tag = PF, "02"
    elif any(k in nm for k in ("EQP", "LINE", "MGMT")):
        target, tag = EQ, "01"
    else:
        continue  # CTL/D_DATE 등은 비귀속
    st, _r = req("PATCH", f"/v1/tables/{t['id']}",
                 [{"op": "add", "path": "/domains",
                   "value": [{"id": target, "type": "domain"}]}],
                 ctype="application/json-patch+json")
    if st < 300:
        assigned[tag].append(t["name"])
print("assigned ❶:", assigned["01"])
print("assigned ❷:", assigned["02"])

# 4) Glossary + 용어
req("PUT", "/v1/glossaries",
    {"name": "PCS_Terms", "displayName": "PCS 업무 용어",
     "description": "설비/센서 도메인 핵심 용어"})
TERMS = [
    ("Equipment",    "설비", "공정 설비(Etcher/CVD/Scrubber 등). 마스터=SMDM/EAM"),
    ("Sensor",       "센서", "설비에 부착된 측정 포인트(온도/압력/유량). 상·하한 보유"),
    ("UptimeRatio",  "가동률", "RUN 상태 측정 비율 = RUN건수/전체건수"),
    ("Alarm",        "알람", "센서값이 HI/LO 한계를 벗어난 건수"),
]
for name, disp, desc in TERMS:
    st, _ = req("PUT", "/v1/glossaryTerms",
                {"glossary": "PCS_Terms", "name": name,
                 "displayName": disp, "description": desc})
    print(f"term {name}: {st}")

print("DONE")
