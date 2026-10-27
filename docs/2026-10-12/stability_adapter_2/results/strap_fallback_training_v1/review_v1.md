# 스트랩 대응 파일럿 사전 독립 검수 v1

요약 판정: **문제없음 — 최종 사전검사 소스의 명시된 파일럿 경로에서 추가 실행 차단 오류를 발견하지 않았다.** 실제 스트랩 안정화·학습 품질·연주 성공·정식 reward v4/v5 인증은 미검증이다. 이 기록은 native 결과 회수 전의 코드·CPU 검수다.

검수 범위는 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRAP_FALLBACK_TRAINING_V1.md:1), warm-start/helper·검사, runner4, 보존된 native2와 최종 native3/helper·검사다. 기존 지침과 소유권을 따랐으며 검수자는 이 파일 외 생성·수정, native 실행·추론·학습을 하지 않았다. root가 실행을 시작한 이후 A/main과 native 입력은 수정하지 않았다.

## Critical — 사전 발견과 해결

- 초안 runner4가 존재하지 않는 `NativeDeadlineEnvironmentV2` 이름을 import하던 문제를 전달했다. [runner4:103](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v4.py:103)은 최종 native3의 실제 클래스 이름을 alias로 import한다. [runner4:255](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v4.py:255)의 보고 profile도 실제 환경 metadata에서 읽도록 정정됐다.
- native2는 `self.gym`을 직접 `InitializationGuard`로 가정했다. root가 실제 카메라 constructor의 `GraphicsGym(InitializationGuard(raw))` 레이어를 발견했고, [native3:99](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:99)는 outer/inner 타입을 확인하고 inner만 새 force guard로 감싼다. 검수자의 초기 추가 차단 오류 없음 판단은 이 레이어를 놓친 것이므로 당시 판단을 철회하고 최종 소스를 다시 확인했다. headless도 `_create_scene`만 덮어쓰고 카메라 constructor는 유지하므로 같은 nested 레이어를 가진다.
- root가 native2 장력의 시점 혼동도 발견했다. [native3:125](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:125)는 현재 상태로 계산한 후보 장력과 직전 물리에 제출한 장력·점·힘·physics index·ON/OFF phase를 분리한다. [native3:228](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:228)의 마지막 관측 feature는 현재 enabled 계산 장력이며 센서 측정이나 직전 제출 장력으로 설명하지 않는다. 기존 native2와 검사 보존본은 변경되지 않았다.

현재 미해결 Critical은 없다. [사전 소스 SHA 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/source_before_native_v1/sha256.json:1)의 여섯 파일을 현재 소스와 대조했다. runner4 SHA는 `cd2e83237b870c8c3d086da4f361c7c82bc2c7c3e3970b50d6adb5be93a5532a`, native3 SHA는 `2af58367eb79727cef1d054fc03215fa3ea8dbcefec25a21bace4137eceb73d1`이다.

## Warning — 실제 시험에서 확인할 범위

- [native3:258](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:258): qdot 안전 판정은 제어 끝의 실제 상태 표본이다. 모든240Hz subframe의 안전을 인증하지 않는다. 실제 조기 terminal·관절명/q/qdot·물리 마지막 step·reset·완료 여부를 native 결과에서 대조할 것. 오류나 fatal 뒤에 가짜 물리 프레임을 붙이지 않는 구조는 맞다.
- [native3:244](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:244): ON/OFF는 mode가 다른 ABI이며 단일825 CP의 cross-mode exact load는 거절된다. 합의한 비교는 **같은 등록820 CP에서 두 조건을 각각 warm-start해 동일 policy/RMS의 별도825 CP를 만드는 것**이다. source SHA와 두 확장 model/RMS의 exact 일치·실제 초기33표본 동등성을 결과에서 확인할 것. CPU CUDA 확장 결과의 초기 입력은 zero proxy이며 실제 native t0 확인은 runner가 수행하도록 되어 있다.
- [runner4:64](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v4.py:64), [runner4:132](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v4.py:132): 마감은 다음 제어/reset/optimizer 진입을 막으며 진행 중 native·CUDA 연산을 선점하지 않는다. 평가600초/TERM15초/KILL5초와 추가 cleanup 대기가 있으므로11:40 순간 중단이나 정오 전 완성 영상의 무조건 보장으로 표현하지 말 것.
- [native3:301](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:301): raw evidence를 영상 encode 전에 저장해 이전 중단 저장 위험을 줄였다. 실제 IO/영상 실패는 계속 실행 실패이며, 정상 full-song 영상과 안전 종료 때문에 실제로 짧아진 영상을 구분할 것. 영상은 renderer와 계산 스트랩 경로 overlay다. 현재 경로에는 오디오 합성 출력이나 audible 연주 인증이 없다.

## 계약 대조

[warm-start:16](/home/ajou/yigyu/3/stability_adapter_2/deadline_warm_start_v1.py:16)은 등록 CP 파일 SHA·원문 ABI digest·이전 core ABI·소비 source SHA·PPO config를 정책 변경 전에 확인한다. strict820 model을 읽고 Actor/Critic 첫층에0열5개, 추가 RMS mean0/var1을 확장하며 기존 RMS/count/log_std·나머지 가중치는 유지한다. 임시 모델로 동등성 검사 후 learner에 설치한다. 새Adam·updates/transitions0이며 optimizer나 이전 RNG를 복원하지 않는다. [runner4:160](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v4.py:160)은 이식 검사 중 소모한 Torch CPU/CUDA RNG를 새 실행의 원래 상태로 되돌린다. exact resume와 구분되어 있다.

[native3:26](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:26)의 정상 raw reward는−2 이상이며 fatal 비용은 다음과 같다.

`raw_fatal = −2 − 2 Σ(k=1..remaining) γ^k − 1`, `scaled = 0.1 × raw`.

[native3:289](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:289)은 현재 실제 step 뒤 증가한 tick을 사용해 `remaining=horizon_ticks−tick`을 계산한다. 따라서 현재 항을 중복하거나 미래 첫항을 누락하지 않는다. 기본 PPO와 같은60Hz/10초 half-life의γ에서 같은 유한 horizon의 모든 정상 reward가 floor 이상이라는 조건 아래 조기 종료로 남은 음수 보상을 회피하는 이득을 막는다. bound는 이 파일럿 scalar 계약에 대한 것이며 기존 음악 보상 전체나 다른γ·종료 계약의 인증은 아니다. raw 성분·floor 조정·fatal tail·scaled 합을 구분해 기록한다.

[force guard:57](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:57)은 owner의 물리 적분 구간에 계산된 route의 환경/body/force/point/space 인자와 순서가 정확히 일치하는 호출만 허용한다. 다른 API는 기존 guard에 위임한다. rest length1.1018469719600776m, stiffness6000N/m, damping120N·s/m, 인장 cap300N과 원본13점법칙을 유지한다. COM 보정 route 속도·작용반작용을 사용하며 기타의 목표 pose로 끄는 별도 힘은 없다.300N은 케이블 장력 cap이며 각 guide 합력의 cap이나 센서값이 아니다.

유한 qdot 초과는 실제 episode 종료로 반환하고 [native3:253](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:253)이 종료 뒤 추가 step을 막는다. collect는 terminated에 즉시 fresh reset하고 GAE bootstrap을 끊는다. 비유한값·금지 API·고정 하체 변경은 계속 실행 오류로 처리한다. 하나의81 제출자/4물리 tick·원본 PD/초기 상태·동결 Fret/Strike·준비2초 계약은 유지한다.

## 확인한 검사와 남은 검증

[native3 CPU11 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/native_checks_v1/pure_tests_v3.log:1), [warm-start CPU3 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/warm_start_tests_v1.log:1), [CUDA 확장 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/warm_start_cuda_v1.json:1), [schedule CPU3 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/schedule_tests_v1.log:1)를 읽었다. native3와 검사 소스는 사전 보존본과 byte-exact이며, 보존된 native2도 동일하다. 검사는 힘/토크 합, 인장/slack, exact force guard, floor/할인, 현재 장력 feature, 완료 후 재호출, wrapper forwarding, 확장 모델/RMS·변조 거절을 다룬다. 실제 forceguard scene·terminal/reset·PPO 연계·ON/OFF 효과는 이 순수 검사만으로 입증하지 않는다.

root가 별도 결과 경로에서 OFF 실행을 시작했다. 이번 기록에는 그 실행 결과를 소급하여 포함하지 않는다. 실제 두 조건의 이식 일치·압현/피크/음악 판정·기타 위치/회전·계산 장력·안전 종료·native 입력 보존·초기/갱신 영상은 후속 검수 대상이다.
