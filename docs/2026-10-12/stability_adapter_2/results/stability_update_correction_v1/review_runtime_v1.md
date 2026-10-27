# 갱신·보정 폭 수정 런타임 독립 검수

요약 판정: **문제없음 — 완료 smoke의 갱신 계약과 실제 원자료·설명·범례 보완본이 일치한다.** 실제 CUDA3갱신은 확인했으나 기타 안정화·음악 성공은 확인되지 않았다. 검수자는 저장 데이터의 읽기 전용 분석·CPU tensor 대조·이미지 육안 확인만 했으며 추가 물리 실행·환경 추론·학습을 하지 않았다. 이 새 보고서 외 파일을 수정하지 않았다. 진행 중 후속 Q 실행은 이 P 검수에서 제외한다.

## Critical

없음.

## 실제 갱신·평가 대조

[완료 runtime 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/runtime_verification_v2.json), 실제 training JSONL·CP·native controls를 독립 대조했다. runner는 CPU PhysX/CUDA, updates3/transitions768, completed/inputs_unchanged true였고 supervisor 종료 코드는0이다.

| 갱신 | 누적 전이 | 승인 optimizer step | 최종 rollout 평균 Gaussian KL |
| --- | ---: | ---: | ---: |
| 1 | 256 | 3 | 0.019762799 |
| 2 | 512 | 4 | 0.019921599 |
| 3 | 768 | 3 | 0.019898698 |

모든 승인 step과 최종 KL은0.02 이하였다. RMS_updated는 세 갱신 모두 false이며, 원본 pinned CP와 초기/1회/3회 저장 CP의 RMS buffer가 모두 exact였다. 초기 mean head0·빈 Adam을 확인했고, 최종 Actor와 Critic tensor가 초기와 실제로 달라져 갱신을 수행했음을 확인했다.

| 실제 평가 | 물리 경과 | 위치 범위 밖 control 비율 | 최대 범위 밖 벡터 크기 | 음악 성공 |
| --- | ---: | ---: | ---: | ---: |
| 초기 | 16.3667초 | 85.4379% | 0.465001m | 0 |
| 1회 갱신 | 16.3667초 | 86.0489% | 0.435782m | 0 |
| 3회 갱신 | 16.3667초 | 84.6232% | 0.470834m | 0 |

각 평가는982control/3928physics, 예정 horizon 종료였으며60Hz endpoint 속도 안전 조건에서 위반 검출이 없었다. baseline weights 불변·금지 API0·strap force51,064=13×3928을 기록했다. 실제 초기 상태는 이전 reference와 같았다. 요청 residual cap·native bounds·최종 target rate를 raw 배열로 재계산해 통과했고, 초기 평가의 adapter action은 모두0이었다. 실제 위치−8/초·회전 upper proxy−4/초 ledger 재계산 오차는 최대8.9e−16이었다.

## 실패 보존·시각 QA·입력 보존

- [verifier v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/verify_runtime_v1.py:64)의 고정 rate 허용치1e−7보다 실제 float32 target rounding의 초과량1.03314718e−7이 커서 세 caps/bounds/rates 복합 검사가 실패했다. 그 외 v1 검사는 통과했다. [v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/verify_runtime_v2.py:64)는 두 target의2 float32 ULP+1e−10을 명시하며 같은 raw에 적용했다. diff는 이 허용치·진단 field·새 출력 경로뿐이고 native 정책/물리는 변경하지 않았다. 원래 producer와 실패 JSON은 보존되어 있다.
- 완료 평가 영상6개 SHA와 capture의 모든 labelled/raw frame SHA를 독립 대조해 같았다. 각 capture는0→3928physics의492프레임이고 MP4 표시 길이16.4초와 실제 물리 경과16.3667초를 구분한다. 전신·손 몽타주와 거리 곡선을 실제로 열어0/2/종료 프레임 및 raw 수치를 대조했다. 마지막 실제 장면은 기타 하방 이탈을 보여주므로 무중단 완주가 평형 유지 성공이라는 해석을 지지하지 않는다.
- [native 산출물 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/native_provenance_v1.json)의37개 입력 before/after/current SHA, producer와3개 PNG SHA가 모두 일치했다. [README v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/README_V2.md:25)의 평가·optimizer·실패 한계 설명이 원자료와 맞는다. native 설명 원문은 유지하고 범례 보완 안내만 추가했다.
- 이전 분석 그림 v1의 시간 패널 범례가 OFF 막대 일부를 덮는 QA 경고를 제기했다. 원문·그림·producer를 보존한 [그림 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/previous_analysis_summary_v2.png)를 실제로 열어 외부 범례로 해결된 것을 확인했다. [v2 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/analysis_provenance_v2.json)의 입력7개 before/after/current SHA가 exact였다. producer SHA는 `901ce239228ab5c2c781875ceeff59bd3d7e1a82cc6e7444ffcbad8c34dcafd9`, PNG SHA는 `e8635536aeb51b934cf204339443d939a715f987d88893fa9e3b5d9ecdcb922e`로 실제 파일과 같다. [보완 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/CHANGED_FILES_V2.md:5)의 절대 링크·실제 줄 번호도 확인했다.
- runtime 검증에 기록된 audit 입력 SHA는 현재 데이터와 일치했다. 사전 봉인14개의 원본/사본 SHA도 그대로였다. main4는 작업 전 snapshot SHA 및 현재 원문 prefix가 exact였다. 종료 당시 runtime closure 불변 검증과 이후 Q의 새 소스/append 기록은 서로 다른 범위이며, 후속 append 이후 main의 전체 SHA까지 과거 attempt와 같다는 주장은 하지 않는다.

## Warning

새 수정 요구 없음. 평균 KL 제한은 해당 rollout 관측에 대한 것이며 전역 물리 안전 보장이 아니다. 세 평가는 이탈률이 높고 accepted crossing·공동 음악 성공이0이다. 단회 smoke의 비율 변화를 반복성 있는 성능 개선으로 판정할 수 없다. preload 대비 nominal 도달성은 후속 제어 후보의 진단이며 필수 접촉 조건이나 실패 원인의 확정도 아니다.

## Suggestion

추가 구조 변경 제안 없음. P의 결론은 갱신 제어·RMS 고정·해당 native 검증 경로가 작동했다는 범위로 유지해야 한다. 후속 Q의 효과는 그 별도 완료 원자료에서 판단한다.
