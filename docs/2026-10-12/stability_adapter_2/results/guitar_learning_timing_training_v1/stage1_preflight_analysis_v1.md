# Stage1 Actor 이전 사전평가

검증 조건 충족: **True**. stage1 범위의 판단이며 다음 단계 승격을 뜻하지 않는다.

stage0의24회 학습 source와 새 stage1의 학습 횟수를 구분한다. 시간창은 ±0.5초이며 정책 pre-roll1초·전체5초·native 정착2초는 유지한다.

| 손 | 회차 | 단계 성공 | audible 유지율 | 최초 down 절대오차(ms) | 추가 목표 down | 반대 up | 기타 최대 이동(mm) |
|---|---:|---:|---:|---:|---:|---:|---:|
| left | 1 | True | 1.000000 | None | 0 | 0 | 5.874268 |
| left | 2 | True | 1.000000 | None | 0 | 0 | 5.677706 |

left: stage0 최종 대비 audible 유지율 평균 변화 0.000000, 최초 down 절대오차 평균 변화 None ms. 동일 시작 조건의 기술적 비교다.
| right | 1 | True | 0.000000 | 15.712061 | 1 | 1 | 0.224923 |
| right | 2 | True | 0.000000 | 15.712061 | 1 | 1 | 0.224923 |

right: stage0 최종 대비 audible 유지율 평균 변화 0.000000, 최초 down 절대오차 평균 변화 -1.968283 ms. 동일 시작 조건의 기술적 비교다.

240Hz 비용 적분·시계·실제 crossing 깊이/속도·inactive 행동0·원 joint music·입력 SHA는 JSON에 보존했다.

[전체 수치와 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage1_preflight_analysis_v1.json)
