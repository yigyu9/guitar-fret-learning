# 초기 자세 시험 후처리 경고 해결 검수

요약 판정: **문제없음 — 실제 사용 경로 기준**. 미해결 Critical 0건, Warning 0건. 기존 `review_post_preflight_v1.md`와 batch V1 원본은 보존하며, batch 코드의 결함을 수정했다고 주장하지 않는다.

## 경고 처리

1. 후속 poll 무제한 대기와 최초 보고서 exists/parse 경쟁은 **해당 스케줄러 사용 중단**으로 이번 실행 경로에서 제외했다. root는 관리 프로세스를 종료코드143으로 중단했고 그때 자식 시험을 아직 띄우지 않았다고 보고했다. 보존된 [batch_log_v1.txt](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/batch_log_v1.txt:1)는 baseline/static 대기 메시지4개뿐이다. 이번 검수에서는 종료 신호 자체를 독립 보존 프로세스 기록으로 인증하지 않으며, 로그의 대기 상태와 root 실행 기록에 근거한다. 이후 개별 native 실행은 root가 직접 관리한다. 배치 V1을 향후 재사용하면 기존 두 경고는 여전히 적용된다.
2. 직접 helper pin 누락은 [render_initial_pose_qualification_v1.py:16](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v1.py:16)에 `initial_pose_noise_v1.py`를 추가해 해결했다. 후처리 소비 이전 수정이라는 범위다. 현재 실제 생성된 visual_baseline_v1/visual_static_v1/visual_strike_v1의 report input map에 직접 helper가 들어 있으며, 각각912/912/462개 전체 입력 SHA가 현재 파일과 모두 일치한다.

## 정지 실행 보존 경계

- [native_static_v2/report.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/native_static_v2/report.json:1)는 `completed=false`, `inputs_unchanged=false`를 그대로 유지한다. physics_steps=2400, failure=null, forbidden_calls=[]다. 이를 전역 봉인 통과로 바꾸지 않는다.
- V2의 before map 전체를 현재 파일과 비교해 달라진 항목은 post renderer 단1개임을 독립 확인했다. [재구성 사본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/guard_boundary/render_before_helper_pin.py:16)의 SHA256은 native가 실제 캡처한 expected SHA `ca8d31cd0edcca7a1dae4fb26a44692de2b04b09c5e2cfb7d2b01507f013398e`와 정확히 같다. 현재 소스와의 diff는 직접 helper를 pin 목록에 추가한 한줄뿐이다. 이 파일은 독립 원본 사전 복사본이 아닌, native-before 해시로 검증한 재구성 사본임을 구별한다.
- 후처리 소스는 native 물리 루프가 사용하지 않지만 conservative shallow A/*.py map에는 포함되어 있었다. 따라서 전역 guard 실패는 실제 사실이며 그대로 보존한다. 이 이유로 V2를 성공 실행으로 소급 인증하지 않는다.
- 새 [native_static_v3/report.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/native_static_v3/report.json:1)는 completed/inputs_unchanged=true, forbidden_calls=[]다. V3 before 입력1,303개도 현재 전부 일치한다.
- [static_reproduction_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/static_reproduction_v1.json:1)의5개 비교를 독립 SHA로 확인했다. V2/V3의 initial_values.json, 60Hz trace.json, 전체240Hz actual_contacts.json, final_state.json, final_efforts.json은 모두 바이트 동일하다. 차이가 난 것은 원래 실패를 기록한 report/입력 봉인 경계이며, 두 실행의 저장된 물리 기록은 같다.

이 검수는 위 경고 해결·보존 범위에 한정한다. 전체 조건의 물리 결과·적합성 및 최종 미디어 검수는 별도다. 검수자는 이 새 문서만 작성했고 기존 소스·보고서·결과를 수정하지 않았다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_batch_v1.py`: `efa492d44774e9cfbab49350d29ad0554affca171689357b2fbbcc18a29d28ca`
- `/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v1.py`: `7ab8080a8a7480b1d7290cdc0515d79b549bbbdefa7fc374b63389cc88ae2c89`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/batch_log_v1.txt`: `893fa7d5844e522804109de54a7817c9b1fce34c713cca8337e6edbcefeb6cbe`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/guard_boundary/explanation.json`: `f8875b88e4d770289f1552ba8563e48b39b09adf54fb5cfd9f36c1f95f6b201f`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/static_reproduction_v1.json`: `7c0a2cce941a48e03564c93bb5b151fc4d89aa51bda725291e54015eab901f42`
