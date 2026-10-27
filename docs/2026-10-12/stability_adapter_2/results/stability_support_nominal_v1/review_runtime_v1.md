# 지지 nominal 제한 런타임 독립 검수

요약 판정: **문제없음 — 완료된 smoke_on_v2의 실제 갱신·nominal 제한·원자료·최종 문서가 일치한다.** 기타 안정화·음악 성공은 확인되지 않았다. 검수자는 저장 데이터의 읽기 전용 분석·CPU tensor 대조·이미지 육안 확인만 했으며 추가 native 실행·환경 추론·학습은 하지 않았다. 이 새 보고서만 작성했다. 진행 중 long_on_v1의 완료·성능은 검수에서 제외한다.

## Critical

없음. 보존된 smoke_on_v1의 초기 평가는 완료했지만 collect readiness의 profile 불일치로 updates0에서 실패했다. 그 오류를 놓친 앞선 사전 검수와 실패 소스를 보존하고 [보완 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/review_preflight_v2.md)로 정정했다. 실제 v2는 collect와 optimizer 갱신까지 통과해 해당 수정 경로를 검증했다.

## 실제 실행 대조

[runtime 검증 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/runtime_verification_v2.json) 및 원래 runner/exit/training 기록을 대조했다. CPU PhysX/CUDA, exit0, completed/inputs_unchanged true,1update/256transitions였다. 승인 optimizer step은6개, 최종 rollout 평균 Gaussian KL은0.01992567256093이며 모든 승인 step의 KL이0.02 이하였다. RMS_updated는 false다.

실제 CP를 CPU tensor로 비교해 P 초기와 Q 초기의 모델 전체 exact, 초기 빈 Adam, 원본 pinned CP·Q 초기·Q CP1의 RMS exact를 확인했다. CP1의 Actor와 Critic은 실제로 초기 값에서 변경됐다. [CPU13회귀 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/cpu_validation_v2.json)은13개 통과/exit0이며 명시된 검사·구현 source SHA가 현재 파일과 같았다. 검수자가 회귀 optimizer 학습을 추가 실행하지 않았다.

| 완료 Q 평가 | 실제 물리 경과 | 위치 범위 밖 control 비율 | 최대 범위 밖 벡터 크기 | 공동 음악 성공 |
| --- | ---: | ---: | ---: | ---: |
| 초기 | 16.3667초 | 55.193483% | 0.338208m | 0 |
| CP1 | 16.3667초 | 45.824847% | 0.473142m | 0 |

두 평가 모두982control/3928physics의 예정 horizon 종료, accepted crossing0,60Hz endpoint 속도 안전 조건 위반 검출 없음이었다. 범위 밖 비율은 감소했지만 최대 이탈은 약0.134934m 증가했다. 이 한 쌍을 안정화 성공으로 해석할 수 없다.

[nominal 검증 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/verify_runtime_v2.py:63)와 각 controls의 teacher/guarded nominal/request/final PD 배열을 독립 대조했다. fixed preload 기준 팔24 ±0.15rad·왼엄지5 ±0.10rad와 native bounds 교집합을 적용한 nominal이 exact였고, 다른 channel은 teacher와 exact였다. adapter residual cap·2 float32 ULP+1e−10의 rate 허용치도 통과했다. PREP의 source action null과 PLAY의 Fret/Strike30D 요청 기록을 구분한다. baseline 추론은 각862회, baseline weights 불변·금지 API0·strap force51,064=13×3928이었다. 위치/회전 새 ledger 재계산 오차는 최대8.9e−16이었다. P0/Q0/Q1의 native 초기 상태 및 PD properties도 동일했다.

## 비교·시각 QA·보존

- [비교 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/comparison_v2.json)는 기타 actor root 이동과 초기 기타 quaternion 대비 SO(3) 회전을 분리한다. P0/Q0는 neutral policy, Q1은 학습 후 deterministic 평가다. 이를 모두 neutral로 부르는 소비 JSON의 scope 문구는 [새 범위 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/COMPARISON_SCOPE_V2.md)으로 정정했고 원문은 보존했다.
- [최종 README v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/README_FINAL_v2.md:11)는 기타 orientation과 native 관절 scalar q를 구분한다. [45행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/README_FINAL_v2.md:45)은 normalized source action을 rad로 자르는 것이 아니라 source/native 교집합 변환 뒤 nominal 목표각을 제한함을 명시한다. P0→Q0의 조건 변경과 Q0→Q1의 단회 갱신 전후 비교, 최대 이탈 악화·음악0·진행 중 장기 학습을 분리해 설명한다. 제기한 두 좌표/단위 표현 경고는 보완본에서 해결됐다.
- 전신·손 몽타주와 이탈 시간 곡선3개를 실제로 열어 P0/Q0/Q1의0/2/16.3667초 native 프레임과 raw 수치를 대조했다. 캡션은 프레임 밖, 곡선 범례는 축 밖에 있어 표본을 가리지 않는다. 영상4개 및 capture의 labelled/raw 모든 프레임 SHA가 기록과 일치했다. 각 MP4는492프레임/표시16.4초로 실제 물리 경과와 구분한다. 마지막 그림만으로 자연스러운 연주나 안정성을 인증하지 않는다.
- [그림 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_final_comparison_provenance_v1.json)의58개 입력과 [추가 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_final_comparison_provenance_addendum_v2.json)의20개 입력은 before/after/current SHA가 모두 같았다. producer·PNG·최종 v1 문서의 path/hash 기록도 현재 파일과 일치했다. [v2 문서 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/README_FINAL_v2_provenance.json)는 원래 v1 문서와 그림을 보존한 표현 수정만 기록한다. v2 README SHA는 `b3941eee8479d20bf40b099ab57a36bbf6c2cc03c21069e13bdc9485386b98ce`, [v2 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/CHANGED_FILES_FINAL_V2.md) SHA는 `5c5ec6090d60355315086f38a16a0be2e0f98c04e16be34f4dd840e9c15667af`로 실제와 같다.
- runtime audit 입력 SHA, 사전9개 source 원본/사본 SHA, main4 작업 전 원문 prefix가 현재 파일과 일치했다. [historical prefix 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/historical_input_prefix_v1/manifest.json)의 A/main2는 실패 Q1 attempt의 SHA와 exact이고 현재 main의 원문 prefix로도 남아 있다. 이는 원래 A 문서를 되돌린 것이 아니라 과거 입력을 별도 사본으로 보존한 것이다. [root 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/CHANGED_FILES_ROOT_V1.md) 및 최종 산출물 링크·명시된 실제 줄 번호를 확인했다.

## Warning

새 수정 요구 없음. 업데이트 후 이탈률 감소와 최대 이탈 악화는 함께 보고해야 한다. baseline 요청 후처리는 원본 정책 행동의 정확한 재현이 아니며, KL 제한은 해당 rollout 관측의 평균 제한이다. 이번 단회 smoke는 음악 성공·반복성·전역 안전·자연스러움·정식 reward 인증을 제공하지 않는다. 진행 중 long_on_v1은 별도 완료 자료가 나오기 전까지 상태 snapshot으로만 취급한다.

## Suggestion

추가 구조 변경 제안 없음. 후속 장기 결과는 완료 시점의 실제 갱신·종료 사유·이탈과 회전·음악 판정·입력 불변·영상에 근거해 별도로 검수해야 한다.
