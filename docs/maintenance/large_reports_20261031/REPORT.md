# 대용량 보고서 로컬 보존 — 2026-10-31

파일 정책이 차단한 생성 JSON11개를 로컬에 보존하고, `.gitignore`에 각 파일의 정확한 프로젝트 상대 경로를 추가했다. 설정·학습 입력 JSON 전체를 제외하거나10MiB 제한을 완화하지 않는다.

[manifest.json](manifest.json)은 각 원본의 경로·바이트 수·SHA256과 기존 스테이징 blob ID를 기록한다. 수정 전 `.gitignore`는 [gitignore.before](gitignore.before)에 보존했다. 원시 결과의 수치·내용·성공 분류는 변경하지 않는다.

스테이징 정리와 정책 재검사 결과는 validation.json에 기록한다. 커밋은 사용자가 실행한다.

검증 완료:11개245492903바이트(약234.1MiB)의 크기·SHA256이 모두 동일하고 파일도 남아 있다. 대상11개가 모두 ignore되며 index에서만 제거됐다. 다른 스테이징 항목은 기존 blob/모드와 동일하다. `python3 .githooks/check-staged-files.py`는 종료코드0으로 통과했다.
