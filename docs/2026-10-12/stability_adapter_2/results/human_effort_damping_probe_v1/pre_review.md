# EFFORT damping 전달 사전 검수

요약 판정: 문제없음 — 사전 검수 PASS. Critical 없음 / Warning 없음 / Suggestion 없음. 실제 네 조건의 native 실행·초기 상태 동등성·damping 반응은 아직 검증하지 않았다.

- `run_human_effort_damping_probe.py:25–35`: 기존 v2와 diff를 대조했다. 오른팔 12축만 EFFORT/stiffness 0으로 변경하고 damping만 원래 값 또는 0을 요청한다. 전체 native properties getter exact를 검사한다. 다른 PD 항목·초기 상태·기타·충돌·스트랩 OFF 조건을 바꾸는 새 로직은 없다.
- `:47–71`: 첫 tick의 명시적 토크는 기존 kp×초기 목표 오차를 native effort 한계로 자른 float32 벡터다. 같은 벡터를 첫 네 physics steps에 제출한다. Step 4 상태 기록 후 전체 original POSITION properties를 복원·readback하고 다음 tick부터 zero effort를 매 step 제출한다. 복원 후 POSITION 목표는 기존 v2와 같이 +0.05rad가 포함된 동일 목표이며 초기 목표로 되돌리는 실험은 아니다.
- `:38–45,60–78`: 목표 setter/PD 복원·mass matrix 조회의 상태 보존, 81×81 finite mass, torque 범위 및 오른팔 소유권, 물리 상태 finite/속도 제한, root/하체 고정·카메라 상태 보존 검사를 유지했다. Mass matrix는 토크 계산에 사용하지 않는다. 추가 step1–4 표본은 첫 네 단계의 좌표·속도 비교용이다.
- `:81–96`: raw states/commands를 close/encode 전에 저장한다. 종료·인코딩 예외는 cleanup_failures에 기록하고 completed_5s를 false로 만든다. 입력/파일 저장 자체 실패의 완전한 보존은 이 계약의 범위가 아니다.
- `human_effort_damping_preserved_run.py:41–72`: 실제 candidate 및 재사용 helper/data의 보수적 입력 목록을 native import 전에 SHA·source_before로 보존하고 종료 후 재검사하며 argv를 finally 복구한다. 기존 소비된 v2 소스는 변경하지 않는다.

두 새 Python 파일의 AST Python3.8 문법 검사와 원본 대비 변경 검수를 완료했다. 기존 저장 v2의 kp=200, nominal +0.05rad 명령을 참고했으며 nominal 10Nm와 실제 float32 요청값은 구분한다. 새 물리 실행은 0회다. Property readback은 damping의 동적 작동 증명이 아니며 요청 토크는 측정 drive torque가 아니다. 새로운 hybrid 제어·연주·지지 성공을 인증하지 않는다.

확인 SHA256: runner `f10418e4f8c47ebec4c9e48f7fe60eac6cc91ddd5c5be4c4441e2afe6b3bfd2a`, wrapper `76c69cf9103c242efa46c253d9180f0a1be5e9ee0cf1ab7294b51d5efda06f44`, 계획 `76edd10a618b95a6e1e4fc91f2aca9735e5e3c48905f7bd4800797b18718c3d8`. 이 사전 검수는 동결한다.
