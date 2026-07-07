# workspace/ — 작업 평면 (전원 공용)

사람이 일을 시키고, Agent(와 사람)가 계획·결과를 남기는 유일한 공용 폴더.

| 폴더 | 무엇 | 규칙 |
|---|---|---|
| `instructions/` | 작업 지시 인박스 (사람→Agent) | `TEMPLATE.md` 복사 → `<작업명>.md`. 목표/범위/제약/완료조건 필수. 완료 시 상단에 `상태: 완료` + act.md 링크 |
| `pdca/` | 작업별 계획·실행 기록 | `<feature>/{plan,do,check,act}.md` — `_TEMPLATE/` 복사로 시작. do.md는 시행착오·에러 포함 시간순 |
| `patterns/` | 재사용 성공 패턴 | PDCA act에서 승격. `TEMPLATE.md` 형식 |
| `mistakes/` | 실패 교훈(재발 방지) | 근본원인+예방책. `<feature>-YYYY-MM-DD.md`, `TEMPLATE.md` 형식 |
| `temp/` | 임시 산출물 | gitignore — 커밋하지 않는다 |

## Agent 규칙
1. 작업은 `instructions/`의 지시서에서 시작한다. 지시서 없는 작업은 먼저 지시서를 만들거나 사용자에게 확인.
2. 흐름: 지시서 → `pdca/<feature>/plan.md` → 실행하며 `do.md` 갱신 → `check.md`/`act.md` → 성공 패턴·실패 교훈 승격.
3. 정의(용어·지표)가 필요하면 `../governance/`를 먼저 본다 — 없으면 정의부터 요청.
4. 크로스세션 지속 사실(누가·목표·불변제약)은 여기가 아니라 Claude Code 파일 메모리에 저장한다.
