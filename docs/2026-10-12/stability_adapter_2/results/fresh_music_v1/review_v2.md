# 음악 조건 공동 정책 보상 수정 검수 v2

2026-10-15. 독립 change-reviewer가 신규 v2 변경만 검수했다. 소비된 v1 소스와 결과, [v1 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/review_v1.md)는 수정하지 않았다.

## 요약 판정

문제없음. B의 신규 보상 기준 실행과 계획된 scratch 16갱신×256전이 pilot을 막는 Critical이나 추가 수정 Warning은 발견하지 못했다. 물리·검증 guard의 개선 판정이 아니라 접근 및 해제 보상 조건의 한정 변경에 대한 판정이다.

## 근거와 변경 범위

[v1 기준 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/baseline_b_v1/report.json)은 245개 valid control, 물리 980 step/4.083333초로 정상 종료했고 입력 변경과 금지 API가 없었다. 압현 유지·해제 후보는 완료되지 않았다. 실제 목표 접근 구간의 손가락 proxy와 프렛 목표 사이 거리는 154.1798–154.2297mm였다. 이는 당시 25mm squared-exponential 접근 보상의 거의 소실되는 구간이다. baseline의 실행 완료는 압현 성공이 아니다.

- [environment_v2.py:16](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/environment_v2.py:16)는 비음수 유한 거리에서 `exp(-distance_m/.15)`를 사용한다. 값은 [0,1]로 제한되고 거리가 줄면 증가한다. 관측된 최소 거리에서 v1 보상 약 3.0335×10⁻¹⁷은 v2 약 0.35777이 된다. 같은 거리에서 10mm 접근하면 약 0.38243으로 증가한다. 이는 거리 shaping이며 접촉 도달 가능성이나 실제 압현의 증거가 아니다.
- [environment_v2.py:23](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/environment_v2.py:23)는 `released_after_hold` 이력과 0.1초 이상 누적 할당 접촉·기하 이력을 모두 요구한다. 한 번도 접촉하지 않은 먼 손의 유휴 상태에는 해제 보상을 주지 않는다. 이 보상 게이트는 전체 유지·해제 후보 완료 기준(준비 readiness, 요구 가청 유지 구간의 80%, 해제)과 다르다. 해제 이력은 해당 음의 이력이므로 현재 시점의 접촉 상태나 연속 0.1초 압현을 인증하는 필드가 아니다.
- [environment_v2.py:31](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/environment_v2.py:31)는 v1 환경을 상속하여 위 두 보상 항과 ABI/metadata·진단 값을 변경한다. 타현/압현 후보 판정, 좌표·음악 시간축, 54개 목표 소유권, native physics/controller, strict Jacobian guard, force/audio 미검증 범위를 유지한다. 신규 ABI의 보상 profile은 이전 checkpoint와의 암묵적 호환을 허용하지 않는다.
- [run_v2.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/run_v2.py)와 [launch_v2.sh](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/launch_v2.sh)는 기존 실행기 대비 환경 import와 자기 launcher/module 경로만 변경한다. scratch 초기화·엄격한 음악 checkpoint 재개·fatal 검증 오류·미완료 rollout 미학습 경로는 같다.

baseline_v1의 사전 SHA에 포함된 기존 fresh_music 소스 8개를 현재 파일과 대조하여 모두 불변임을 확인했다. 신규 파일 추가를 이전 baseline에서 사전 봉인된 것으로 소급 설명하지 않는다.

## 검증과 한계

events 7 + 기존 environment 11 + 신규 v2 보상 4 + runner 4, 총 26개 CPU 테스트가 통과했다. 신규 환경·실행기·보상 테스트의 AST 검사와 `launch_v2.sh`의 `bash -n`도 통과했다. 신규 테스트는 관측 거리에서의 민감도, 비유한·음수 거리 거부, 접촉 없이 해제 보상 획득 불가, 다른 지표 보존을 확인한다.

이번 기록 시점에 v2 native 기준 실행과 scratch pilot 결과는 아직 판정하지 않았다. v1의 영상·완료 실적을 v2의 보상이나 정책 성능으로 승계하지 않는다. 새로운 넓은 행동 범위에서의 탐색 안정성은 실제 pilot과 기존 strict guard로 확인할 항목이며, guard 완화나 오류 전이의 정상 학습 치환을 승인하지 않는다.
