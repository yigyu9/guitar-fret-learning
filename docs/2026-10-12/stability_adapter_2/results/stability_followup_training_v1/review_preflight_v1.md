# 후속 체크포인트 오프라인 분석기 사전 독립 검수

요약 판정: **문제없음 — 최종 analyze_checkpoint_v3.py의 남은 실행 차단 오류 없음.** 새 periodic CP는 아직 생성되지 않았으며, 이번 판정은 소스 경계와 기존 CP1의 저장 자료 함수 검증에 한정한다. 검수자는 새 분석 CLI·native·학습·대기 실행을 하지 않았고 이 새 보고서 외 파일을 수정하지 않았다.

## Critical

최종 버전에서 없음. v1은 실제 runner의 `record_0001.json` 방식과 달리 `<update_label>.json`을 읽어 파일 없음으로 실패하는 경로였다. 검수 지적으로 원본을 보존한 v2/v3는 순번 기록의 내부 label을 읽고 일치하는 기록이 정확히1개인지 확인한다. 현재 검사 기록은 새 CP를 실제로 분석했다는 증거가 아니다.

## 확인 사항

- [최종 분석기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/analyze_checkpoint_v3.py:1)는 기존 실행의 CP·완료 평가·JSON/영상만 읽는다. 입력 SHA를 등록하고 끝에 다시 확인한다. 선택 CP의 schema·PPO config·ABI digest/동일성·label-update 수·평가 기록의 CP 경로를 검사한다. 각 `evaluation.json`의 CP SHA·updates/transitions·deterministic·RMS 미갱신·control 수를 해당 CP와 직접 대조한다.
- 라이브 training 로그는1회 읽은 bytes에서 newline으로 끝난 완성 행만 선택 CP의 updates까지 추출한다. 추출한 고정 prefix를 별도 `xb` 파일로 저장하고 그 파일의 SHA를 분석 입력으로 등록한다. 이후 live append를 고정 입력의 변동으로 오판하지 않는다. 업데이트 순서2..선택 CP 및 마지막 transitions, 승인 optimizer step·최종 KL/RMS 기록을 검사한다. stochastic episode return은 deterministic 평가와 분리하며 episode 도중 정책이 갱신될 수 있으므로 고정 정책 수익으로 해석하지 않는다.
- 완료 평가의 실제 초기 상태/PD, native trace·nominal/residual/bounds/rate·baseline·force·music counts·영상 SHA와 종료 endpoint를 대조한다. full horizon·안전 조기 종료를 별도 field로 기록한다. 위치 이탈과 기타 actor root 이동은 구분하고, SO(3)는 초기 기타 quaternion 대비 max 및60Hz control endpoint 평균이다. native 관절 scalar q 변화/속도 진단과 혼동하지 않는다.
- 압현 cell 집계는240Hz 전체 및 PLAY(`physics_step>480`)를 구분한 진단이다. 목표 운지 정확성·음악 성공·힘 센서 인증으로 설명하지 않는다. `longest_outside_interval_s`는 연속된60Hz 이탈 표본 수×1/60초이며 미관측 subframe의 실제 연속 이탈을 인증하지 않는다.
- [함수 검증 v3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/analyzer_function_verification_v3.json)는24개 모두 통과했고 등록 input SHA가 현재 파일과 일치했다. 기존 CP1의 이탈률45.824847%·최대 이탈0.473142m·초기 대비 최대 SO(3)95.864500°는 기존 검증과 같다. 실제 순번 기록 선택과 미존재 label 거부도 검사한다. [검증 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/verify_analyzer_functions_v3.py:1)는 CLI 전에 정의된 함수만 추출하여 검사하므로 새 CP의 전체 CLI/로그 prefix 경로까지 실행한 시험은 아니다.

검수한 분석기 SHA는 `a54f990a388c3a454a0ce5fbcc900d40e48977d47a8df57e6b70c69c2d680e1e`, 함수 검증 producer SHA는 `c18871d90c5911aef9316ddb27856f4c5ff1349cf4d7dadf9ed94838ea7e986a`다. 이전 v1/v2 소스·함수 검증을 보존했고 A/main·native/PPO 제어 변경은 없다.

## Warning

새 수정 요구 없음. 새 periodic CP/완료 평가가 확보된 뒤 전체 분석의 통과 여부를 별도로 확인해야 한다. 이번 단일 CP 비교는 반복성·자연스러움·전역 물리 안전·음악 성공·장기 학습 완료 인증이 아니다. 같은 출력 경로는 exclusive 생성하므로 후속 비교나 실패 재시도는 기존 결과를 덮어쓰지 않는 새 버전/경로가 필요하다.

## Suggestion

추가 변경 제안 없음. 기존 학습을 중복 실행하지 않고 완료된 저장 CP·평가 영상으로만 후속 분석한다.
