# 유한 손 유지 제어 연결부 교정

독립 검수에서 run11.baseline_guard의 경로가 inputs_maintenance_v2/baseline_v1.json에 남아 있음을 확인했다. 실제 cfg는 v3이고, 기존 CPU는 command/CLI를 확인했지만 이 guard의 실제 본문을 실행하지 않았다. 따라서 원 run11/execute14와 실패 CPU를 보존하고, run12는 해당 경로 literal 하나만 v3으로, execute15는 child module 하나만 run12로 교정한다.

- [x] 새 두 파일 최소 교정 및 문법 확인.
- [ ] 실제 guard 본문과 실제 v3 설정/기존 raw schema를 사용한 CPU: old11 거부/new12 네 action 허용, missing/false/extra gate·SHA·class·참조 누락·불완전 report 거부.
- [ ] 독립 FINAL/SHA → Root 원본 재현 증거·복사·ACK → prospective before_v11.
- [ ] 새 baseline_v10 실제 28초 실행 및 모든 필수 기하·접지·건강·압현준비·보정후 정지 감사. 통과 뒤에만 다음 action.

CLI CPU의 libpython/cache/PATH 환경 오류도 각 source/before/log와 함께 보존한다. 이들은 native 물리 실패가 아니다. 새 controller/초기 상태/수치 기준·gain/force cap은 바꾸지 않는다. 원 strict EPS0/원인미확정·동적미검증·최종채택 False를 유지한다.
