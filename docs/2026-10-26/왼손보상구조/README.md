# 현재 왼손 학습 보상 구조

**새 단순화 구성:** `--learning-family finger-skill`의 보상9개·손목 종료·단일 cost·공동 학습은 [12 v25 보상과 종료](12_v25보상단순화와종료.md)를 먼저 읽는다. 아래 song/v24 설명과 과거 검증은 해당 경로의 기록이다.

문서 확인일: **2026-10-26**. 현재 코드의 기본 실행과 명시적으로 선택하는 새 학습 구조를 구분한다. 이 폴더는 보상 설명이며, 모든 실험의 성공을 선언하는 결과 보고서는 아니다.

## 무엇부터 읽을까

1. [00 보상 구조 요약](00_보상구조요약.md): 기본 곡 학습에서 무엇을 측정하고 보상하는지 본다.
2. [01 범위와 계산 흐름](01_범위와계산흐름.md): 악보·관측·행동·240Hz 물리·60Hz 보상의 연결을 본다.
3. 손가락 학습 구조 v24를 선택했다면 [11 v24 학습 구조와 보상](11_v24학습구조와보상.md)을 먼저 읽는다.
4. 성과와 증거는 [07 PPO 진단과 최근 결과](07_PPO진단과검토쟁점.md), [09 근거와 검증](09_근거와검증.md)에서 확인한다.

## 기본 곡 학습과 v24의 차이

| 구분 | 기본 `song` | 선택 `finger-skill-v24` |
| --- | --- | --- |
| 실행 선택 | `--learning-family`를 생략하거나 `song` | `--learning-family finger-skill-v24` 명시, GPU 왼손 전용 |
| 보상 계약 | `guitar_learning.gpu_tensor_song_reward.v22` | `guitar_learning.finger_skill_reward.v1`, v22 측정·보상 기반 재사용 |
| 관측 | 552상태·일반64×24·우선8×24 | 기본552에 단계·결정 길이·남은 시간5열 추가, 총557 |
| 학습 과제 | 기본 곡67음 전체 | 자동 실행의 R/F는 원곡 연속 구간, J는 전곡 |
| 정책 | 선택한 손의 기존 정책 | support17축과 네 손가락16축을 분리하고 R/F/J별 학습 |
| 단계 | 완료곡 최근256개 기반 음악 stage0/1/2 | 독립 고정 평가의 R/F/J, 음악 가중치는 초기값 고정 |
| 제어 | 기본 `incremental`; `position`은 별도 비교 옵션 | `incremental`만 허용 |
| 결정과 물리 | 정책60Hz, 물리240Hz | 기본60Hz 결정, F의 최대3/6tick 유지는 명시 비교 옵션; 물리240Hz |

아래 01~05의 기본 수식과 단계0/1/2 설명은 `song` 범위다. v24의 선택 음·분모·단계별 보상 필터·결정 지속시간에는 [11장](11_v24학습구조와보상.md)의 별도 계약을 적용한다. CPU 왼손·오른손과 [별도 v7 해제 실험](08_v7해제개선.md)도 이 두 GPU 왼손 경로와 구분한다.

v23의 위치 제어 비교는 기본 채택을 보류했다. 같은128환경·100업데이트 비교의 평균 달성음은 누적5.6875, 위치0.078125/67이었다. 단일 비교의 결과이며 다른 설정의 일반적 우열을 뜻하지 않는다. [비교 원문](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_structure_v23/README.md).

## 최신으로 확인한 v22 학습 결과

같은 large/128환경/H32/seed7 정책을100회에서500회 더 학습해 누적600회를 완료한 결과다. 고정128환경의 첫 종료곡을 평가하고 실패도 분모에 포함했다.

| 지표 |100회 모델 |600회 모델 |
| --- | ---: | ---: |
| 평균 달성음/67 |2.015625 |2.515625 |
| 안전 시간축 완료/128 |112 |127 |
| clean/고정 전체 목표 음길이 |2.873% |4.681% |
| audible wrong/같은 고정 분모 |81.561% |35.178% |
| audible missing/같은 고정 분모 |14.373% |60.025% |

달성322개는 모두 약지였고, 중지·약지·소지의 B 계획창 점유는0%였다. 엄지 접촉 후보는 전체 곡시간의0.011209%였다. wrong 감소와 missing 증가를 함께 읽어야 하며, 전 손가락 압현·B 복귀·엄지 지속 접촉·자연스러움 해결로 해석하지 않는다. clean/wrong/missing은 완전한 분할이 아니다.

[누적600회 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_v22_continue_500/RESULTS.md) · [전체 분석](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_v22_continue_500/learning_analysis.json) · [실행 검증](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_v22_continue_500/verification.json)

## v24에서 확인한 범위

495개 소스의 봉인과54모듈525개 CPU 검사, 짧은 GPU R/F/J·상관 탐색·동일 단계 재개·명시적 Actor 이전 검증 기록이 있다. 이번 문서 갱신은 그 자료와 현재 코드를 읽어 대조한 작업이며 학습을 새로 실행하지 않았다.

기록된 R의 독립4개 구간 평가는 안전4/4이지만 손목 영역 체류61.366959%로80% 기준을 넘지 못해 `ready=false`, 해당 단기 예산에서는 `stalled=true`였다. 진단 목적의 R→F 이전 검증은 자동 준비 기준 통과가 아니다. F의 짧은1024환경 구동·재개에는 완료 에피소드가 없으며, F3 비교에서는46개 종료 중 물리 실패3개를 기록했다. 이를 자동 R→F→J 전체 성공이나 장기 성능 향상의 증거로 확대하지 않는다.

[전체 구현·실행 안내](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_skill_v24/README.md) · [R 준비 평가](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_skill_v24/support/final_readiness_transfer_verification.json) · [실제 GPU 자료 검증](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_skill_v24/support/final_native_data_verification.json)

## 상세 목차

| 문서 | 내용 |
| --- | --- |
| [00 보상 구조 요약](00_보상구조요약.md) | 기본 song의 한 음·보상 묶음·단계 |
| [01 범위와 계산 흐름](01_범위와계산흐름.md) | 실행·관측·제어·보상의 연결 |
| [02 측정과 성공 판정](02_측정과성공판정.md) | 패드·접촉 후보·clean·달성의 구분 |
| [03 접근·접촉·유지](03_접근접촉유지보상.md) | 손목·PBRS·최초접촉·유지·달성 수식 |
| [04 추종과 자세](04_손가락추종과자세.md) | 추종·B 대기·선택 shape·움직임 비용 |
| [05 감점·안전 비용·총합](05_감점안전비용과총합.md) | wrong/missing/missed·실패·reward와cost |
| [06 단계 전환](06_단계전환과가중치.md) | 기본 음악 stage와v24 R/F/J의 차이 |
| [07 PPO·진단·최근 결과](07_PPO진단과검토쟁점.md) | 기본PPO·결정PPO·평가 분모·누적600회 |
| [08 별도 v7 해제 실험](08_v7해제개선.md) | 과거 별도 실험, 기본 및v24에 미통합 |
| [09 근거와 검증](09_근거와검증.md) | 근거 파일·검사 범위·과거 기록 구분 |
| [10 엄지 지지와 오압현](10_엄지지지와오압현개선안.md) | 적용된 엄지 안내·최근 결과와 미해결 사항 |
| [11 v24 학습 구조와 보상](11_v24학습구조와보상.md) | 정책 분리·원곡 구간·R/F/J·결정PPO |

## 과거 검수와 이번 확인

`source_audit.json`과`verification.json`은 v20의 기록 인덱스, `verification_pre_review.json`은 v17 기록 인덱스다. `verification_v22.json`은 v22의100회 결과이고 `independent_review.md`는 이전v17/v20 검수 이력이다. 파일 안의 “현재”는 당시 시점이며 이번 최신 검수로 재사용하지 않는다. 원본은 그대로 보존했다.

이번 확인은 [verification_latest.json](verification_latest.json), [independent_review_latest.md](independent_review_latest.md)를 따른다. 변경 전17파일과SHA는 [보관 목록](/home/ajou/yigyu/3/docs/archive/left_reward_structure_before_latest_20261026_v1/manifest.json)에 있다. 보상·제어·모델·학습 설정은 변경하지 않았다.
