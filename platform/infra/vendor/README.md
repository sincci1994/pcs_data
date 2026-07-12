# vendor/ — 이미지에 베이크할 바이너리 반입물

## Oracle Instant Client (thick 모드)

`instantclient-basiclite-linux.x64-*.zip` 을 이 폴더에 두면 이미지 빌드가 `/opt/oracle` 에 풀고 ldconfig 등록한다.
없으면 no-op — 집/일반망 빌드는 비워두면 된다(로컬 검증은 Postgres 목소스라 불필요).

- 다운로드: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html (Basic Light, 로그인 불필요) — 프록시 서버에서 받아 넣는다.
- 실 EES(Oracle) 접속은 thick 모드 전제(버전·인증 편차 대비) — 코드에서 `oracledb.init_oracle_client()` 호출 필요.
- zip 실파일은 gitignore(~120MB, 환경별 반입물) — 커밋하지 않는다.
