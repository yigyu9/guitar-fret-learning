# 시뮬레이터 재사용 방식의 실제 학습 경과

**기존 25회 모델을 이어 약 31분 학습하여 누적 39회까지 진행했다. 이전 실행의 빠른 메모리 증가는 이번 관측에서 나타나지 않았다. 좌우 손 접근은 조금 개선됐지만, 실제 음악 성공은 여전히 0이다.** 새 학습은 시간 예산으로 정상 종료했고 최종 모델과 모든 감사 결과를 저장했다.

## 실행 조건과 저장 결과

| 항목 | 결과 |
| --- | ---: |
| 진입점 | guitar_learning.train_persistent |
| 실행 시간 | 1,855.25초, 약 30분 55초 |
| 업데이트 | 기존25 → 추가14 → 누적39 |
| 환경/rollout | N8 × H256 = batch2048 |
| 이번 학습에 반영된 전이 | 28,672 |
| 완료 episode | 320 |
| 초기 준비를 포함한 episode 시작 | 328, worker당41 |
| 폐기한 미완료 rollout 전이 | 0 |
| 종료 이유 | wall_budget, 정상 완료 |

추가 최대32update/soft wall1800초로 시작했고, 진행 중인 마지막 배치가 끝난 뒤 예산을 검사해14회에서 종료됐다. 따라서 30분보다 약55초 더 실행됐다. 마지막8개 episode의 각64tick도 완료된 rollout 안에서 bootstrap을 사용해 학습에 포함된다. 끝나지 않은 episode와 폐기된 미완료 rollout을 혼동하지 않는다.

모델은 [final.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/run_v1/final.pt)에 누적39회로 저장됐다. 중간 저장은 이번 실행의 checkpoint_000004.pt/000009.pt이며 내부 누적 update는 각각30/35다. 처음 재개할 때 기존 checkpoint_000024.pt와 모델·두 optimizer·계약·cost weight·업데이트 수·Python/NumPy/Torch/CUDA RNG가 정확히 같았음을 확인했다. 최종 가중치는 모두 유한하다.

보상·네트워크·행동·제어·음악 목표는 변경하지 않았다. medium/초기std exp(-3)/actor lr3e-5/value lr3e-4/dense_v2와 기존 PPO 설정을 유지했다. 목표는 `05_BN2-131-B_solo`의 첫 단음, **2번 현7프렛 약지/down**이다. 왼팔12·왼손21·오른팔꿈치/손목6의 **39축 공동 정책을 이어 학습**했으며 좌우 별도 학습이나 curriculum을 새로 적용하지 않았다. 하체와 상체 지지·우손 파지는 기존 유한 유지 제어를 사용한다.

설정의 initial_std는 새 정책 시작값이다. 이번 재개에서는 학습된 std와 optimizer를 포함한 기존 checkpoint 상태를 복원했으며 std를 새로 초기화하지 않았다.

## 음악 수행과 접근 변화

모든 지표는 이번 완료14update의28,672전이에 대한 집계다. 이전 마지막5update, 이번 첫5update, 이번 마지막5update는 각각10,240전이/완료112episode다.

| 지표 | 이전 마지막5 | 이번 첫5 | 이번 마지막5 |
| --- | ---: | ---: | ---: |
| 평균 완료 episode reward | −0.270702 | −0.266849 | −0.262994 |
| onset 직전 왼손 목표 거리 | 20.157mm | 19.846mm | 19.330mm |
| sweep 구간 우손 guide 거리 | 54.912mm | 55.156mm | 54.660mm |
| 평균 완료 episode cost | 0.002546 | 0.001815 | 0.001565 |
| 50ms/100ms 타현 매칭 | 0/0 | 0/0 | 0/0 |
| 목표 음 후보 유지 누적 | 0초 | 0초 | 0초 |

이번 전체320완료 episode에서도 strict/lenient 매칭은0, 목표 미스320, 목표음 유지 합0초, 60Hz 끝 표본의 압현 후보0이었다. 방향·속도·깊이 조건을 만족하는 통과나 접촉 후보를 성공했다고 설명할 근거가 없다.

이번 첫5→마지막5의 왼손 거리는 약 **0.516mm**, 우손 거리는 약 **0.497mm** 줄었다. 이전 마지막5와 비교하면 왼손 약0.827mm/우손 약0.253mm 감소다. 실제 연주 성공을 발견한 변화는 아니다. 오른손은 중간에 오르내렸고, 마지막 단일 update의 좋은 값만 선택하지 않고5개 평균을 사용했다.

왼손은 각 episode의 동일 시각67/60=1.11667초에 측정한 **distal body 원점–명목 fret점** 거리다. pad의 실제 격차·압력과 다르다. 오른손은 onset 전후80ms의 기타 상대 **피크–guide** 거리다. 이번 첫/마지막5의 sweep 표본은 각각1120/1136개로 rollout 경계의 일부 episode도 포함한다. 서로 다른 proxy를 동일한 물리 접촉 오차로 해석하지 않는다.

보상 증가의 주된 근거는 접근 shaping이다. 이번 보상 합은 미스−160, 조기 왼손+43.0449, 우손 guide+28.7278, 기존 접근+5.1486, 우손 방향+0.1075, 행동 변화−0.0234였고 타현·유지·해제 보상은0이다. 정책이 업데이트됐다는 사실과 연주 목표를 해결했다는 사실을 구분한다.

이전 모델에서 계속 학습한 관찰이며 별도 결정적 정책 평가나 독립 seed 실험은 하지 않았다. 정책 업데이트 수·시뮬레이터 이력·동시 시스템 부하가 달라, 접근이나 비용 변화 전체를 reset 변경의 인과 효과로 설명하지 않는다.

## 메모리와 시뮬레이터 수명

| 같은8개 worker의 현재 메모리 합 | 시작 약64초 | 종료 직전 약1854초 |
| --- | ---: | ---: |
| RSS | 4.924194GiB | 4.924446GiB |
| PSS | 3.331077GiB | 3.331386GiB |

시작 준비를 제외한 RSS 증가는 끝점 기준 **약0.26MiB**다. 60초 이후 RSS OLS 기울기는 약 **+0.000958GiB/시간**이고, 후반 절반은−0.000288/마지막10분은−0.000595GiB/시간으로 작은 변동 수준이었다. 기울기의 R²도 각각 약0.236/0.010/0.019로 낮다. 이전 구식 실행의 약 **+9.00GiB/시간** 증가가 이번 약31분 구간에서는 재현되지 않았다.

이는 현재 RSS와 PSS의 실제 주기 표본이다. 공유 페이지를 포함한 RSS, 공유분을 나눈 PSS, 각 프로세스 peak RSS를 구분했다. parent의 현재 RSS는 처음 약1.010GiB에서 마지막1.276GiB로, worker의 지속 증가와 구분한다. 시스템 가용 메모리 최저는 **24.384GiB**, 보호 하한은4GiB였다.

8개 worker는 각각 **create_sim=1/create_env=1/load_asset=2/destroy_sim=1**이었다. worker당41번 준비하는 동안 sim/env/controller/FK와 자산을 유지했고 마지막에만 종료했다. 준비 경계의 state readback, 물성 불변, 제어 이력/local clock 초기화, 상태 쓰기 계수와 최종 누적 guard 검사를328개 모두 통과했다. [최종 lifecycle 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/run_v1/persistent_audit.json).

이번 범위에서는 반복 장면 재생성을 제거한 경로에서 메모리 증가가 억제됐다. 다만 두 실행의 길이와 정책 시작점·시스템 부하가 다르며, 기존 native 자원 보유의 정확한 원인이나8시간 누수 부재를 증명한 것은 아니다.

## 반복 준비와 정책 구간 안정성

reset 상대 비용만 보면 준비 자세가 매번 변하는 것을 놓칠 수 있어, **328개 준비 후 실제 상태**를 각 worker의 첫 준비 상태와 별도로 비교했다.

- 기타 위치 차이 최대 **0.4221mm**, 회전0.00154869rad.
- 발 위치 차이 최대 **0.0548mm**, 관절 q 차이 최대0.00098330rad.
- 328개 모두 세 주요 부위 양성 지지와 양발 양성 접촉이 있었다.
- 105채널/원래 영범위8축, Root 고정·기타 자유·중력 ON 플래그를 모두 확인했다. nominal 영범위축의 실제 움직임이0이라는 주장은 하지 않는다.

정책 구간의 한 부위 이상 기타 지지와 양발 접촉은60Hz endpoint에서 각100%, 세 부위 동시 양성 지지는 **89.648%**였다. 기타 이동 최대 **1.7834mm**, 회전0.00614539rad, 발 이동 최대0.3326mm였다. 물리 실패 전이는0이다.

접촉 비율·편차 최대값은60Hz 끝 표본이며, 실패는 각 전이의 네240Hz 표본을 합친 `failure_reasons`로 집계한다. 정책 구간114,688물리스텝에 해당하지만 전 표본을 raw로 저장한 것은 아니다. 기타 직접 보조 힘·스트랩·강제 부착·제어 중 상태 덮어쓰기는 추가하지 않았다. Root 자유 균형, 실제 현 압력·진동·음향, V3 전체 정밀 감사 완료를 뜻하지 않는다. 숨은 PhysX solver/contact cache의 완전 동등성도 주장하지 않는다.

## PPO와 시간 병목

최대 analytic/시도 KL은 **0.015366**으로 상한0.02 안이었고 재시도0회, actor lr3e-5를 유지했다. 최종 Gaussian std 평균0.0497819(축별0.0496714~0.0498755)로 초기 규모를 유지했다. 비유한 가중치나 분산 붕괴로 정체됐다는 증거는 없다.

전체 시간 대비 reset/준비는 **48.48%**, policy step은 **49.80%**, 신경망 갱신은 **0.166%**였다. reset 재생성은 사라졌지만 **실제 물리2초 준비는 매 episode 유지**하므로 초기화 비용이 사라진 것은 아니다. 또한 step/reset에는 원래의 유한 제어·측정·통신 등이 포함된다. collection 타이머는 다른 항목과 겹치므로 모든 비율을 더하지 않는다. 이번 자료에서 GPU 신경망 갱신이 주된 시간 병목은 아니다.

![재개 학습의 보상·좌우 거리·메모리·성공·KL](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/training_progress_v2.png)

권장 그림은 v2다. 첫 그림의 KL 범례가 낮은 점을 가리는 문제를 확인해 원본·소스·입출력 SHA를 보존한 뒤 범례만 옮겼다. 메모리 그림에서 이전 실행은 약60분, 새 실행은 약31분까지만 그렸다. 이전 수치를 새 실행 구간으로 외삽하지 않았다. [PDF 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/training_progress_v2.pdf).

## 현재 판단과 다음 순서

**운영 측면의 반복 재생성·빠른 메모리 증가 문제는 이번 관측에서 개선됐지만, 공동 정책이 압현과 타현의 성공을 발견하는 문제는 남아 있다.** 접근·반환값은 조금 좋아졌으나 같은 첫 음에서320번의 완료 시도 모두 미스였다. 기존25회와 합치면 누적39회지만 보존된 성공 모델이라고 부를 수 없다.

다음 우선순위는 단순 학습 연장이나 망 확대보다 **왼손의 유효 압현 후보와 오른손의 유효 기하 통과를 각각 native에서 성공시킬 수 있는지 확인하는 것**이다. 초기 자세·관절 범위·파지·행동 스케일과 성공 판정의 positive 사례를 분리해 확인한 뒤, 성공 가능한 부분 목표를 학습 단계로 연결하는 편이 현재 결과에 맞는다. 이번 실행 중 보상/정책 구조를 바꾸거나 별도 손 학습을 시작하지 않았다.

## 원자료와 재현

- [실제 최종 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/run_v1/report.json)는 core 결과와 persistent 수명 감사를 합친 판정이며 completed=True다. 기존 원시 core 결과는 core_report.json에 SHA와 함께 보존됐다.
- [음악/PPO/checkpoint 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/learning_analysis.json), [자원·기존 실행 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/runtime_analysis.json), [준비 후 자세 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/preparation_analysis.json)를 남겼다.
- [실행 전73파일 보존](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/source_run_v1/manifest.json), [재개 모델 선택과 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/resume_selection.json), 각 후처리의 사전 입력 SHA와 전후 무변경 검사를 보존했다. 실행에 소비된 소스·입력·기존 결과는 변경하지 않았다.
- [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/review_preflight.md)를 마쳤다. 최종 독립 검수 및 root의 source_final/artifact_inventory/final_verification은 실제 결과 문서 확정 뒤 별도로 생성한다.
