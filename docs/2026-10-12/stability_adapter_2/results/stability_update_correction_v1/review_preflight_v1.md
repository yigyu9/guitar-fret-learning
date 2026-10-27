# 갱신·보정 폭 수정 사전 독립 검수

요약 판정: **문제없음 — 최종 PPO v3·native v5·runner v6에서 남은 실행 차단 오류 없음.** 검수 시점은 새 native 실행 전이다. 이 판정은 정적 계약·CPU 반례·초기화에 한정하며 실제 CUDA 갱신·물리 안정성·음악 성공·장기 완료를 인증하지 않는다. 검수자는 이 보고서만 작성했고 소스·기존 결과를 수정하지 않았다. 추가 native 실행이나 실제 환경 정책 학습은 하지 않았다.

## Critical

최종 버전에서 없음. 보존된 PPO v2에서는 NaN 후보가 `_kl`의 Normal 구성 예외를 내어 모델/Adam 복원을 건너뛰는 반례를 검수자가 CPU fake-step으로 재현했다. [최종 PPO v3](/home/ajou/yigyu/3/stability_adapter_2/deadline_guarded_ppo_v3.py:30)는 parameter·Adam tensor의 유한성을 먼저 검사하고 예상 KL 수치 예외를 거절/backtracking으로 처리한다. optimizer 예외도 양쪽 상태를 복원한 후 재발생시킨다. 검수자가 같은 NaN 반례에서8회 거절·모델 exact 복원·빈 Adam 복원을 확인했고, 후보 변경 뒤 fake optimizer 예외에서도 복원을 확인했다.

## 확인 사항

- [최신 계획 v2](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_UPDATE_CORRECTION_V2.md:7)는 직전 ON54갱신/완료35episode 모두 finite 속도 안전 종료, OFF40갱신/완료11episode 중 horizon8·속도 안전 종료3, 음악 성공0을 구분한다. 초기→1회 갱신 KL은 단일 초기 상태의81D 합산 값이며 rollout 평균·정규화 원인의 분리 측정으로 설명하지 않는다. [이전 결과 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/previous_analysis_v1.json)의 입력 SHA가 현재 원자료와 일치했다. 앞선 계획 v1의 OFF 전부 완주 문장은 새 v2로 정정하고 원문은 보존했다.
- [후단 KL 검사](/home/ajou/yigyu/3/stability_adapter_2/deadline_guarded_ppo_v3.py:75)는 갱신 전 수집 정책의 latent Gaussian mean/std를 고정해 각 승인 후보를 **완전한 rollout 전체**의 평균 old→new KL과 비교한다. joint별 합산81D이고 예산은0.02다. minibatch/epoch가 진행돼도 기준을 직전 후보로 바꾸지 않아 누적 변화가 제한된다. update 끝에서도 같은 기준을 재검사한다. RMS는 갱신하지 않고 mean/var/count exact 불변을 검사한다. latent/action/log_prob provenance와 종료/절단 GAE 경계는 기존 계약을 유지한다.
- [후보 rollback](/home/ajou/yigyu/3/stability_adapter_2/deadline_guarded_ppo_v3.py:20)은 각 optimizer step 직전 모델·Adam snapshot을 만들고, 같은 gradient로3e−5부터 최대8개 절반 LR 후보를 시험한다. 매 restore마다 Adam snapshot을 deepcopy해 보존된 v1의 alias 재시도 문제를 피한다. 모두 거절하면 해당 step 직전 상태로 돌아간다. 이미 승인된 이전 step 전체를 취소하는 계약은 아니다.
- [bounded codec](/home/ajou/yigyu/3/stability_adapter_2/deadline_bounded_residual_v1.py:7)은 native 순서의 group별 body0.03/head0.10/arm0.30/finger0.20rad를 사용한다. 요청은 `clip(nominal+cap×action, effective lower, effective upper)`이고0 action은 현재 nominal이다. [native v5](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v5.py:39)는 부모의 단일 rate owner 경로에 이 codec만 연결한다. PREP의 preload 및 PLAY의 동적 Fret/Strike nominal 계산·81 제출·4physics·소스 평가 시계는 부모 경로를 유지하며 gain·실제 초기 q·기타 force 법칙을 변경하지 않는다. cap은 요청 보정 폭이며 실제 q 오차나 직전 최종 목표와 새 nominal의 차이 한계가 아니다.
- [RMS 초기화](/home/ajou/yigyu/3/stability_adapter_2/deadline_rms_initialize_v1.py:14)는 pinned ON 초기 CP의 SHA·ABI digest·원본 source bytes·이전 물리/음악/관측 ABI를 확인한 뒤 RMS3개 buffer만 복사한다. Actor 마지막 weight/bias0, 새 Critic·log_std·Adam·카운터를 유지한다. 검수자가 실제 pinned CP를 CPU에서 읽고 helper를 실행해 RMS exact, 모든 nonRMS tensor 이식 전과 exact, 평균 출력 head0, 빈 Adam을 확인했다. 이전 실패 Actor나 RNG/optimizer를 재개하는 경로가 아니다. 새 runner의 native 실제 ABI 일치는 후속 실행에서 확인해야 한다.
- [runner v6](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v6.py:100)는 Isaac 경로를 Torch보다 먼저 import하고 실제로 PPO v3/native v5를 사용한다. 평가 child도 v6로 진입하며 exact 새 CP load와 RMS 초기화는 배타적이다. CP SHA는 attempt 입력에 보존하고 `.pt`는 학습 source ABI에서 제외해 자가참조를 피한다. 새 보상/floor/discounted safety tail은 부모의−8/−4·raw floor−8·scale0.1을 유지한다.
- native reset/step/ABI뿐 아니라 [중도 close](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v5.py:45)도 새 profile context로 감싸, 부분 episode 보고서가 이전 profile로 잘못 표기되는 검수 경고를 해결했다. 안전 판정과 강제 reset 계약은 유지한다.

## 검사와 봉인

[CPU v3 원로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/pure_tests_v3.log)의7개 검사는 모두 통과했다. [검사 소스](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_guarded_update_v3.py:30)는 interleaved81 codec/경계, 해석적 KL, populated Adam exact rollback, reduced-LR 재시도, 전체 update/RMS/누적 KL, NaN/KL 예외, 잘못된 CP pin의 learner 불변을 포함한다. 검수자가 추가한 인메모리 확인은 위 RMS 초기화 및 fake numerical/optimizer 반례이며 저장된 CP를 변경하지 않았다.

[최종 실행 전 봉인 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/source_before_native_v2/manifest.json)의14개 원본·사본·예상 SHA를 독립 대조해 전부 일치했다. 계획 v2도 포함한다. 주요 최종 SHA는 다음과 같다.

| 파일 | SHA-256 |
| --- | --- |
| deadline_guarded_ppo_v3.py | 7b48dcb1576cb7d3b6afb515a5874cf6027325a4bccf5b1a80a8f36277337d2b |
| deadline_native_v5.py | 4ceec3b9df4944f285374e519b46f461118c03d29f21198ddaf929661309559c |
| run_deadline_training_v6.py | a933528a0efa63421ca52acd4a77e0c9ab8365ef1e4fd199a60e8ff324b097b8 |
| STABILITY_UPDATE_CORRECTION_V2.md | 7027bdc643e921337c3819ce7c870ea0e804a8b4131c65f95dcf731cb4b2fa67 |
| pinned ON initial CP | 5f2c6b055c2b268311870a3cf84e49e22887343010b7030cc264484a7a29131b |

## Warning

새 수정 요구 없음. KL≤0.02는 수집한 관측의 평균 제한이며 모든 상태·개별 관측·미래 trajectory의 전역 제한은 아니다. bounded residual도 동적 baseline의 품질이나 물리 안전을 보장하지 않는다. 기존 baseline은 진단용 미인증 경로다.30분 평가와11:40 cutoff는 호출 경계의 설정이며 비선점 native/optimizer·영상 정리 시간을 포함한 hard deadline 인증이 아니다. 이 제한을 실제 결과 설명에서 유지해야 한다.

## Suggestion

추가 구조 변경 제안 없음. 다음 판정은 실제 CUDA 최소3갱신에서 승인된 optimizer step·최종 KL·RMS exact 불변·81요청/rate·초기 및 baseline/SHA 불변·실제 종료 사유와 영상에 근거해야 한다.
