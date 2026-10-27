# 종료한 8환경 dense_v2 학습 분석

**자세와 접지는 유지됐지만 연주 성공은 아직 발견하지 못했다. 왼손 접근에는 작은 개선이 있고 오른손은 거의 정체됐다. 별도로, 워커의 현재 RSS/PSS가 한 시간 내내 증가한 문제가 뚜렷하다.** 이번 종료 원인은 사용자의 중단이며 메모리 부족 예외는 아니다.

대상: [13:01 원 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_20261018_130137) · [원 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_20261018_130137/report.json). 원 코드·설정·로그·모델은 변경하지 않았고 새 학습이나 native 평가를 실행하지 않았다.

## 실행과 저장 상태

| 항목 | 결과 |
| --- | ---: |
| 실행 시간 | 3,599.21초, 약 60분 |
| 완료 PPO 업데이트 | 25회 |
| 실제 업데이트에 반영된 전이 | 51,200 |
| 전체 전이 로그 | 52,096 |
| 중단 때 폐기한 26번째 수집 | 112/256 tick × 8환경 = 896전이 |
| 완료 업데이트 구간에서 끝난 episode | 576 |
| 전체 로그에서 끝난 episode | 592 |
| 마지막 정규 저장 모델 | checkpoint_000024.pt, 누적 25update |
| 중단 복구 모델 | failure_last_valid.pt, 누적 25update |

학습 대상은 `05_BN2-131-B_solo`의 **첫 단음 하나**, 2번 현·7프렛·약지·down 타현이다. press=1.00초, onset=1.12초, 음 종료=1.3522초, episode 시간표=1.4522초이며 실제 정책 단계는 88tick이다. pool이나 전체 곡을 학습한 실행은 아니다. 설정은 N8/H256/medium/GPU 정책/초기 std exp(-3)/dense_v2였다.

부모는 episode reset 응답을 기다리는 중 `KeyboardInterrupt`를 받았다. 워커 8개도 준비 중 같은 예외를 받았고, 모두 강제 terminate/kill 없이 종료 코드 0으로 정리됐다. `report.completed=False`, `stopped=interrupted`이며 최종 `final.pt`는 없다. `status.json`에 남은 alive=true는 정리 전 상태다. 최종 정리는 report의 `pool_close_diagnostics`로 확인한다.

`failure_last_valid.pt`와 마지막 정규 checkpoint의 **모델·두 optimizer·계약·cost weight·업데이트 수가 정확히 같다.** 모델의 1,931,600개 저장 scalar는 모두 유한하다. 부분 수집의 난수 소비와 metadata 때문에 파일 SHA 자체가 같은 것은 아니다. 896전이는 optimizer에 반영되지 않았으며 로그의 592완료 episode를 모두 25업데이트의 성과로 합산하지 않는다. 경계에 걸친 episode도 있어 전이 수를 episode 수×88로 단순 환산하지 않는다.

## 음악 수행과 두 손의 변화

아래 전체 집계는 **완료 업데이트의 51,200전이/576완료 episode**다. 전반·후반 비교는 각각 첫 5업데이트와 마지막 5업데이트이며, 각각 10,240전이와 완료 112episode다.

| 지표 | 전체 | 첫 5업데이트 → 마지막 5업데이트 |
| --- | ---: | ---: |
| 50ms/100ms 타현 매칭 | 0 / 0 | 모두 0 |
| 목표 음 후보 유지 누적 최댓값 | 0초 | 0 → 0 |
| 압현 후보가 있는 60Hz 끝 표본 | 0 | 0 → 0 |
| 완료 episode의 목표 미스 | 576 | 112 → 112 |
| 평균 완료 episode reward | −0.273362 | −0.274964 → −0.270702 |
| onset 직전 왼손 거리 | 20.716mm | 21.085 → 20.157mm |
| 타현 sweep 구간 우손 guide 거리 | 55.013mm | 55.068 → 54.912mm |
| 평균 완료 episode cost | 0.003017 | 0.003014 → 0.002546 |

왼손은 onset에 가까운 동일 시각 67/60=1.11667초의 표본을 episode마다 하나씩 비교했다. 전반과 후반 각각 112개 표본에서 약 **0.928mm, 4.4%** 가까워졌다. 측정값은 손가락 말단 body 원점과 명목 fret 목표 사이 거리다. 손가락 pad의 실제 격차나 접촉 압력을 뜻하지 않는다. 작은 접근 변화는 관찰되지만 적합한 압현 후보나 목표 유지로 이어지지 않았다. 통계적 유의성이나 독립적인 결정적 정책 평가를 새로 수행한 결과는 아니다.

오른손은 onset 전후 80ms sweep 구간의 기타 상대 피크–guide 거리를 비교했다. 평균 변화는 약 **0.156mm**, 전체 guide 유효 구간 평균도 50.463→50.457mm로 거의 같다. 목표와 거리가 여전히 수 cm 남아 있고 실제 타현 매칭은 0이다. 첫/마지막 단일 update의 끝값만 선택해 큰 개선으로 설명하지 않는다. sweep 비교 표본 수는 전반 1,120개/후반 1,136개이며 rollout 경계의 부분 episode를 포함한다.

미완료 수집 896전이에서도 매칭·유지·압현 후보는 0, 물리 실패도 0이었다. 이 수집에서 끝난 16episode의 평균 reward −0.268802는 별도로 보존하며 학습에 반영된 성과로 취급하지 않는다.

## 보상과 PPO의 해석

완료 전이의 주요 보상 성분 합은 다음과 같다.

| 보상 성분 | 합계 |
| --- | ---: |
| 목표 미스 | −288.0000 |
| 조기 왼손 접근 dense_left_early | +72.6334 |
| 오른손 guide 접근 dense_right_guide | +50.7802 |
| 기존 press~onset 접근 | +8.7347 |
| 오른손 방향 보완 | +0.1694 |
| 행동 변화 | −0.0418 |
| 타현 성공·유지·해제 | 0 |

초기보다 episode reward는 소폭 좋아졌지만, 그 변화는 성공 보상이 아니라 접근 shaping과 관련된 변화다. 특히 후반에도 미스는 episode마다 유지된다. 과거 legacy 보상의 약 −0.485와 이번 약 −0.273은 **보상식이 달라 직접적인 연주 개선 비교값으로 사용할 수 없다.**

PPO의 최대 analytic KL은 **0.017028**, 시도된 최대는 0.017116으로 상한 0.02 안이었다. KL 재시도는 0회, actor lr은 3e-5를 유지했다. reward critic loss는 0.003135→0.0000483으로 줄었지만, 실제 성공이 없는 반환값을 예측하는 개선과 연주 수행은 구분해야 한다. `actor_grad_norm` 약7.54→9.79는 clipping 전 norm이므로 이 값만으로 gradient clipping 실패라고 볼 수 없다.

학습 전 Gaussian std 평균은 0.0497871, 마지막은 0.0497904(축별 0.0496763~0.0498735)다. NaN·분산 붕괴·KL 폭주가 정체의 직접 원인이라는 증거는 없다. 정책 행동의 역할별 평균 절댓값은 약0.04로 유지됐고, 정규화 행동 절댓값0.9를 넘긴 표본 성분은 없었다. 정규화 Gaussian std를 실제 관절각 std와 동일하게 해석하지 않는다.

## 안정성

정책 끝 표본 기준 양발 양성 접촉과 세 부위 중 한 부위 이상의 기타 지지는 **각 100%**였다. 세 부위가 동시에 양성인 비율은 **83.439%**였으며 접촉 분담 변화는 허용된다. 기타 이동 최대는 **2.427mm**, 회전 **0.008113rad**, 발 이동 최대 **0.379mm**였다. 물리 실패가 기록된 전이는 0이다.

접촉 비율·위치/회전 최대값은 **60Hz endpoint 집계**다. 종료 판정의 `failure_reasons`는 환경이 각 전이의 네 240Hz 표본에서 합친 결과다. 목표 유지0초는 240Hz 음악 적분 결과이며 준비 중 모든 접촉이 없었다는 주장은 아니다. 이 실행으로 V3 전체 정밀 자세 감사, 실제 현 압력·진동·음향, Root 자유 균형·보행을 검증한 것은 아니다. 현재 정책 출력은 39축이며 하체는 기존 외부 유한 제어가 담당한다.

최종 report의 `physical_flags_errors=[0,...,7]`는 따로 해석해야 한다. reset 예외가 session을 닫아 None으로 만든 뒤 final audit가 플래그를 읽어, Root/기타/중력 값이 모두 None으로 남았다. 따라서 최종 검사에 실패했으며 전체 감사 통과 실행으로 인증하지 않는다. 이 목록 자체가 기타 고정·중력 해제의 증거는 아니다. 읽기 전 SHA를 고정한 초기·중간·마지막 준비 감사 24개에서는 필요한 물리 플래그가 유지됐다. 전 단계의 최종 감사 공백은 남는다.

## 메모리와 시간 병목

**현재 메모리가 계속 증가했다. 과거의 peak RSS만 있는 경우보다 훨씬 강한 증가 근거다.**

| 8개 worker 메모리 합 | 시작 약63초 | 종료 직전 약3,598초 |
| --- | ---: | ---: |
| 현재 RSS | 5.093GiB | 13.953GiB |
| 현재 PSS | 3.510GiB | 12.371GiB |

60초 이후 RSS 기울기는 약 **+9.00GiB/시간**, 마지막 15분에도 약 **+8.42GiB/시간**으로 상한에 도달하지 않았다. PSS도 같이 늘어 공유 페이지의 중복 합산만으로 설명되지 않는다. 인접 표본의 작은 감소는 있었으므로 엄밀한 단조 증가라는 뜻은 아니다. 부모 메모리는 후반에 대체로 일정했다.

메모리 보유·증가 문제의 증거는 강하지만 **native 자원 누수와 allocator/cache 보유의 정확한 원인은 아직 구별하지 못했다.** 기존 경로에서 반복 장면 재생성과 함께 나타났고, 이것이 우선 확인할 대상이다. 이미 구현한 persistent 경로가 이 증가까지 해결했다고 단정할 수는 없다. 그 경로의 검증은 짧은 연결 시험이었다.

시스템 가용 메모리 최저는 **10.476GiB**로 4GiB 보호 하한보다 높았다. 이번 중단은 OOM이나 memory_guard가 아니다. 다른 작업의 메모리 변화 때문에 전역 가용량이 늘어도 해당 worker 증가가 멈춘 것은 아니다. 현재 증가 추세로 8시간 실행이 안전하다고 판단할 근거는 없다.

벽시계 시간의 reset은 **49.13%**, policy stepping은 **48.91%**, PPO 신경망 갱신은 **0.143%**였다. 완료 update당 평균 수집 약139.93초, 신경망 갱신 약0.206초다. 준비 완료 감사는 worker당74개, 총592개로 기존 경로의 같은 수 장면 생성·준비 완료에 해당한다. 마지막 중단된 준비는 제외했다.

병렬 reset 배치는 평균 약23.895초였다. 장면 제거·생성·자산 로드·실제 물리 2초 준비·감사·IPC를 모두 포함하므로 이를 순수 자산 로딩 비용이라고 설명하면 안 된다. collection은 reset/step을 포함하고, 마지막 실패한 reset과 미완료 수집은 타이머에 온전히 포함되지 않아 모든 비율을 더해 정밀한 전체 시간 분할로 취급하지 않는다. GPU 신경망 갱신 속도가 주된 병목이라는 증거는 없다.

![학습·두 손 거리·KL·현재 메모리·시간 비중](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/training_analysis.png)

위쪽과 왼쪽 아래는 완료25업데이트만, 메모리는 종료 직전까지의 실제 주기 표본이다. 왼손은 onset 직전 동일 시각, 오른손은 sweep 구간이라는 서로 다른 proxy다. [PDF 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/training_analysis.pdf).

## 다음 작업의 우선순위

1. **persistent 경로의 현재 RSS/PSS 추세부터 확인한다.** 기존 장면 재생성 경로로 8시간을 단순 재시도할 근거는 없다. 새 방식에서도 증가하면 per-reset/per-step 자원과 참조 보유를 분리해 원인을 좁힌다.
2. **왼손 접촉 후보와 오른손 기하 타현을 각각 성공시킬 수 있는지 확인한다.** 관절 범위·초기 자세·관측·현재 행동 스케일/평활화에서 목표가 도달 가능한지 분리해야 한다. 이번 로그는 두 손이 함께 성공한 보상을 한 번도 경험하지 못했다.
3. 그 뒤 성공 가능한 부분 목표를 학습 단계로 연결하고 결합한다. 오른손의 변화가 작은 이유를 확인하기 전에 망 확대나 무조건적인 std 증가로 해결된다고 가정하지 않는다. 이전 큰 행동 검증에서는 기타 편차가 커진 기록이 있다.

가중치를 이어 쓸 경우 마지막 유효 모델은 [checkpoint_000024.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_20261018_130137/checkpoint_000024.pt)이며 [failure_last_valid.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_20261018_130137/failure_last_valid.pt)도 같은 25update 가중치·optimizer다. 같은 dense_v2 고정 목표 설정에서 새 `guitar_learning.train_persistent` 진입점의 `--resume`으로 연결하는 대상이다. 이번 분석에서 실제 재개 학습은 하지 않았다. 보상이나 목표 계약을 바꾸는 후속 작업은 기존 strict resume 조건과 함께 결정한다.

## 분석 근거와 보존

- [음악·안정성·PPO·checkpoint 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/analysis.json), [분석 입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/inputs_before.json), [입력 무변경 확인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/analysis_verification.json).
- [자원·종료 수치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/runtime_analysis.json), [담당 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/runtime_notes.md), [해당 입력 무변경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_analysis_v1/runtime_inputs_after.json).
- 생산자는 스트리밍 로그 분석과 그림 소스를 함께 보존했다. 성공한 분석·그림 원자료는 덮어쓰지 않는다. 독립 검수와 root의 최종 입력·산출물 봉인은 문서 확정 뒤 별도로 기록한다.
