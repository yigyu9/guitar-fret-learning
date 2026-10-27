# 지지 nominal 제한 사전 독립 검수

요약 판정: **문제없음 — 새 native 실행 전 차단 오류 없음.** 정적 코드·CPU 원로그·저장된 이전 요청의 순수 projection만 확인했다. 검수자는 추가 native 실행·정책 추론·학습을 하지 않았고 이 새 보고서 외 파일을 수정하지 않았다. 실제 지지·음악 성공·물리 안전은 아직 인증 대상이 아니다.

## Critical

없음.

## 확인 사항

- [계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_SUPPORT_NOMINAL_V1.md:11)과 [helper](/home/ajou/yigyu/3/stability_adapter_2/deadline_support_nominal_v1.py:7)는 reset의 고정 preload 기준 팔24 ±0.15rad·왼엄지5 ±0.10rad와 effective native bounds의 교집합을 사용한다. 다른 channel은 teacher nominal 그대로다. 실제 native81 이름 목록에서 팔24개 및 `LH:thumb1_x/y/z`, `LH:thumb2/3`5개를 독립 확인했다. 원본 teacher/preload 배열을 변경하지 않는다.
- 검수자가 이전 P 초기 평가의 저장된982개 nominal을 실제 names/groups/bounds로 helper에 순수 투영해 팔·엄지 제한, 다른 channel exact 불변, PREP 기준 보존을 확인했다. 이는 새 물리 장면의 지지 검증이 아니다. [CPU 원로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/pure_tests_v1.log)의4검사도 통과했다. [검사 소스](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_support_nominal_v1.py:18)는 양부호 cap·native 교집합·입력 불변·잘못된 매핑/기준 거절을 포함한다.
- [native v6](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v6.py:25)는 부모의 실제 Fret/Strike nominal을 얻은 뒤 새 helper로 후처리한다. 관측에 들어가는 nominal과 residual 기준은 같은 후처리 값이다. 기존 bounded81 residual·한 제출자/rate owner·동적 teacher 추론·실제 final PD의 source history·물리/보상/안전 종료 경로는 그대로 유지한다.
- [기록과 종료](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v6.py:37)는 물리 step 전에 현재 raw teacher nominal과 source action을 tick별 deepcopy하고, 종료에서 controls에 raw teacher·clip 후 nominal과의 delta·source action을 붙인 뒤 부모의 raw 출력 경로를 호출한다. PREP의 source action은 아직 추론하지 않았으므로 null일 수 있다. reset은 이전 장면을 close한 뒤 기록을 비워 에피소드 간 혼합을 피한다. 정상·부분 종료의 새 profile context도 유지한다.
- [새 ABI](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v6.py:31)는 기존의825 관측·81 residual/PPO 계약에 새 nominal 제한을 명시한다. [runner v7](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v7.py:103)과 평가 child는 native v6/runner v7로 진입한다. 검증된 PPO v3·고정 RMS·새 mean0 Actor/Critic/Adam 시작 및 기존 pinned ON CP의 RMS-only 초기화 경로를 유지한다. 이전 control ABI의 exact resume로 설명하지 않는다.
- [launcher](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/launch_run_v1.py:18)는 ON/CUDA/v7,30분 평가와11:40 cutoff를 명시하고 실제 PID·종료 코드를 보존한다. [실행 전 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/source_before_native_v1/manifest.json)의8개 원본/사본/예상 SHA가 검수 시점에 모두 동일했다.

## Warning

새 수정 요구 없음. Teacher 추론 호출 유지와 원본 정책 행동 재현은 다르다. 팔·엄지 후처리는 운지/타현 도달 범위를 줄 수 있다. preload는 음악의 필수 접촉 조건이 아니며 팔 최대±0.45rad·왼엄지±0.30rad는 residual을 더한 **요청 공간**으로, 실제 q·세계 손 위치·접촉 유지 보장이 아니다. 새 계획은 이를 구분한다. 실제 음악 성공·위치/회전 이탈·안전 종료를 함께 평가해야 한다.

## Suggestion

추가 구조 변경 제안 없음. 후속 판정은 실제 CUDA 갱신 및 초기/갱신 평가에서 teacher→guarded nominal→요청→최종 PD, 관측·rate·RMS·초기 상태·baseline·입력 SHA와 실제 종료 영상이 일치하는지에 근거해야 한다.
