# 병렬 환경 수 비교와 장기 학습 시작 설정

현재 장비에서는 **독립 CPU 환경16개 + GPU 정책**, medium망, H128/batch2048을 권장한다. 1/2/4/8/16개를 실제 실행했고, 빠른8/16개는 반복했다. 세 설정을 각각8192전이/4업데이트 비교한 뒤 **actor_lr=3e-5, 초기 std=exp(-3)≈0.049787**을 유지했다. 이는 안정성을 고려한 장기 시작값이다. 음악 성능의 최적값이나 수렴을 입증한 결과는 아니다.

장기 설정은 [long_B_16env_v1.json](/home/ajou/yigyu/3/guitar_learning/configs/long_B_16env_v1.json), 실행·재시작은 [장기 실행 안내](/home/ajou/yigyu/3/guitar_learning/PARALLEL_TRAINING.md)를 따른다. 이번 작업에서는 비교 시험을 완료했고8시간 실행은 시작하지 않았다.

## 실제 비교 조건

- i9-13900/24물리코어·32논리CPU, RAM약31.1GiB, RTX4070Ti/12282MiB. 장비 기록은 [hardware_host.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/hardware_host.json)에 있다.
- 원 장면의 CPU PhysX를 spawn 프로세스마다 하나씩 만들고 부모 정책이 묶어서 추론한다. GPU PhysX 벡터화나 수천 환경 동시 실행 구현은 아니다. 물리240Hz/정책60Hz, 물리thread1, Torch·BLAS thread1, 카메라0개다. OS 전체 thread 수가1이라는 뜻은 아니다.
- Root고정·하체 유한제어·105입력/97비영범위/8원영범위, 자유 기타·중력ON·스트랩OFF, 준비2초를 유지했다. 모델·충돌정책·gain·음악 보상·안전 임계값·역할별 행동 범위를 바꾸지 않았다. 정책 출력은39축이며 하체는 외부 유한 유지 제어다.
- 05_BN2-131-B_solo의 stageB/첫 목표/tempo1/seed7/medium1,931,600params를 사용했다. 부모 정책의 난수 배치 모양이 환경 수에 따라 달라지므로 서로 다른 N의 궤적이 완전히 동일하다는 비교는 아니다.
- 2초 준비 시점의 q/qvel/몸체 위치를 기존 저장 표본과 대조해 차이0, 회전 재구성 잔차약1.3e-16rad를 확인했다. 질량·관성·충돌/shape·PD·제어gain 등 저장된 물성도 동일했다. [상태 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/headless_parity_v1.json) · [물성 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/headless_property_parity_v1.json). 이 비교는 장시간 V3 전체 인증을 대신하지 않는다.

## 환경 수 선정

각 실행은 같은 H128, CPU 정책,1업데이트다. 수집 속도에는 수집 중 에피소드 종료와2초 재준비가 포함되고 최초 준비·업데이트·종료는 제외된다. 전체 실행 시간은 각 report.wall_s에 별도로 있다.

| 환경 수 | 수집 전이/초 | 측정 횟수 | 첫 실행 환경 RSS peak 합(MiB) |
| --- | ---: | ---: | ---: |
| 1 | 3.849 | 1 | 716.1 |
| 2 | 6.721 | 1 | 1430.5 |
| 4 | 11.705 | 1 | 2829.3 |
| 8 | 17.848 | 2평균 | 5687.5 |
| 16 | 21.971 | 2평균 | 11354.5 |

최고 유효 평균의90% 이내인 최소 N을 선택했다. N8은 N16의 약81.2%로90%에 미달해16을 선택했다. 첫 N8/N4 속도비가1.512이고 관측 RAM여유가8GiB 이상이어서 사전 규칙에 따라16도 시험했다. N32 이상은 이번에 시험하지 않았다. RSS 합은 공유 페이지를 중복 포함하며 실제 전용 RAM 소비와 같지 않다.

N8은17.6976→17.9981, N16은21.6979→22.2432 전이/초였다. [선정 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/pilot_decision.json) · [전체 실행 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/run_summary.json).

동일한 실제2048전이 buffer와 초기 체크포인트에서 optimizer를 기기별3회 시험했다. 첫 회를 제외한 중앙값은 CPU8.2013초/GPU0.2075초였다. 모든 시도는 KL 재시도0이었다. 실제 GPU pilot의 업데이트도 평균약0.21초였다. 이 약40배 차이는 optimizer 계산에 한정되며 전체 학습 속도 배수가 아니다. 물리와 재준비가 주된 비용이다. [기기 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/update_device_profile.json).

## 학습 설정 비교와 선택 근거

모든 후보는 N16/H128/batch2048/GPU/새 정책/seed7/4업데이트이며, 다른 보상·제어·PPO 설정은 같다. 후보별 완료80에피소드와 마지막 부분 에피소드를 따로 기록했다.

| 후보 | 초기 std | actor lr | 평균 episode cost | 기타 변위 최대(mm) | 후보 유지 합(s) | 50/100ms 타현 매칭 | 실패 종료 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| baseline | 0.049787 | 3e-5 | 0.00273559 | 2.221 | 0 | 0/0 | 0/80 |
| explore | 0.12 | 3e-5 | 0.39687406 | 46.414 | 0.029167 | 0/0 | 0/80 |
| faster | 0.12 | 1e-4 | 0.32128309 | 46.952 | 0.050000 | 0/0 | 0/80 |

변위 최대는 **60Hz 마지막 물리 표본의 최대**이며 전체240Hz 표본의 정밀 최대라고 주장하지 않는다. 실패 판정 자체는 매240Hz 표본에서 수행됐다. 후보 유지 합은80완료 에피소드 전체의 누적값이다. 한 번의 연속50ms 유지나 실제 현 압력을 뜻하지 않는다. 세 후보의 부분 에피소드에서도 타현 매칭은0이었다.

확대 탐색에서 짧은 접촉 후보가 생겼지만 비용과 기타 편차가 커졌고, 실제 타현 매칭의 이득은 없었다. 따라서 baseline을 안정적인 출발점으로 선택했다. 1e-4는 std0.12에서 정상 작동했으므로 높은 학습률 자체가 나쁘다는 결론은 아니다. std0.049787에서1e-4를 별도로 실제 수집해 비교하지 않았고, 다중seed·장기 수렴 비교도 아니다.

최대 analytic KL은 각각0.010954/0.010233/0.018697이며 재시도는 모두0이다. 체크포인트의 모든 값은 유한하고 정책도 실제 변했다. 같은 저장 학습 상태에서 결정적 행동의 평균 절대 변화는0.001708/0.004525/0.005011이었다. 이는 optimizer 작동 근거이며 독립 native 평가나 연주 성능 개선의 근거는 아니다. [체크포인트 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/pilot_checkpoint_analysis.json).

거리 보조 지표의 onset±50ms 평균은20.938/22.256/22.487mm였다. 이 값은 **손가락 distal body 원점과 명목 fret 목표점 사이 거리**다. 손가락 접촉면의 격차·침투 깊이·압현 성공률로 해석하지 않는다.

## 장기 설정과 시간·자원

H128은 약2.133초로 첫 B에피소드의 onset1.12초와 종료까지 담는다. H64도 bootstrap으로 학습할 수 있으나 초기 첫 사건을 한 수집 구간에서 확인하기 위해128을 유지했다. N16이 선택되면서 초기 예상batch약1024 대신2048을 사용했고 후보 간에는 동일했다.

장기 설정은256추가 업데이트/최대524288전이,8시간 soft budget,10회마다 체크포인트다. baseline 전체 wall454.90초/8192전이를 단순 환산하면 약8.09시간이다. 최초 준비가 없는 수집 TPS만으로 예상하면 재준비 빈도를 과소평가할 수 있다. 약8시간을 예상하되 시간 예산에 따라256회 전에 멈출 수 있고, 예산은 업데이트 경계에서 확인하므로 마지막1회만큼 초과할 수 있다. 선택한 체크포인트와 장기 설정의 엄격한 재시작 계약도 확인했다. [선정과 예산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/long_training_decision.json) · [설정/재시작 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/long_config_validation.json).

GPU pilot의 수집은 약20전이/초였다. baseline의 관측 RAM여유 최소는약11.41GiB, 환경 RSS peak 합은약12.14GiB, 부모 RSS peak는약1.29GiB였다. Torch GPU 할당 peak는약279.2MiB, reserved392MiB이며, 장치 전체 GPU 메모리의2초 간격 관측 최대는3850MiB였다. Torch 할당과 장치 전체 메모리는 서로 다른 양이다. MemAvailable은 시작과 control tick 뒤의 표본 최소이며 초기화·재준비 도중 순간 최저를 보장하지 않는다. 8시간의 메모리 거동은 아직 검증하지 않았다.

음악 매칭0이므로 장기 실행에서도 성공·목표 유지·접근·비용 추세를 함께 봐야 한다. 단순 반환값 상승만으로 연주 학습 성공을 선언하지 않는다. 현재 설정은 첫 B목표용이며 전체 곡·자동 curriculum·새 하체 정책·Root자유 균형을 완성하지 않았다.

## 구현·보존·검증

- 신규 [headless_session.py](/home/ajou/yigyu/3/guitar_learning/headless_session.py), [parallel.py](/home/ajou/yigyu/3/guitar_learning/parallel.py), [train_parallel.py](/home/ajou/yigyu/3/guitar_learning/train_parallel.py)와 관련 CPU 검사만 추가했다. 기존 환경/정책/PPO 구현은 유지했다. CUDA 수집의 마지막 비동기 계산도 시간에 포함하도록 runner를 보존 후 한 번 개정했다.
- [이전44파일](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_parallel_tuning/archive_manifest.json), [계측 개정 전4파일](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_cuda_collection_timing/archive_manifest.json), [첫 실행 소스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/source_run_v1_manifest.json), [GPU 실행 소스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/source_run_v2_manifest.json)를 보존했다.
- [최종 CPU 검사104개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/cpu_tests_v2.txt)를 통과했다. native10실행/31616전이, 후보 비교는 그중24576전이다. 각 실행의 입력 SHA·실제 child import·모델/물성/제어권·금지 API/worker 오류·Root/기타 flags를 사후 검사했다.
- [Root 입력 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/input_audit.json)는1580입력 경로, 실제 로드XML과 모든 선언mesh106파일, 보관/snapshot151파일을 대조했다.398준비 기록의 저장된 물성이 동일했고295완료 에피소드/실패0을 확인했다. 독립 검수도 원본 compact로그에서 이 집계와 후보별 지표를 재확인했다. 이는 학습 환경의 실패 임계값 기준이며 과거 모든 큰 행동 범위의 실패를 취소하지 않는다.
- 각 worker의 audit_episode_*/initial_values.json, contract.json, 첫 transition의240Hz 원자료, transitions.jsonl.gz의60Hz compact기록, update_*.json, final.pt를 보존했다. 모든240Hz 표본 전체를 저장했다고 설명하지 않는다.
- optimizer profile 최초 절대경로 실행은 프로젝트 import 실패였으며 로그를 보존하고 PYTHONPATH를 명시해 같은 소스로 재시도했다. sandbox에서 CUDA RNG를 볼 수 없었던 재시작 검사 실패도 보존하고 GPU가 보이는 실행으로 통과했다. 두 실패에서 물리 장면은 만들지 않았다. 기존 importer의 visual geom 경고도 console에 남겼으며 이를 숨기거나 원자산을 수정하지 않았다.
- [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/review.md) · [최종 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/final_verification.json) · [파일 inventory](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/artifact_inventory.json).
