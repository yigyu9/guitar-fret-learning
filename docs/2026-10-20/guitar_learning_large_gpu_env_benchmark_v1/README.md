# large 모델의 GPU 학습·병렬 환경 수 실측

2026-10-20. 현재 기본 왼손의 **large·CUDA 정책/CPU 물리**에서 2/4/8환경 전곡 시험과 8환경 strict resume 반복 검증을 완료했다. 시험한 후보 중 runner 처리율은 **8환경**이 가장 높았다.
**16환경은 측정하지 않았으며 시험한 8환경을 절대 최대치로 해석하지 않는다.**

## 조건

- [실제 CUDA 확인](cuda_probe.json): NVIDIA GeForce RTX 4070 Ti 1개에서 `cuda:0` 텐서 계산값 512를 확인했다. sandbox에서 `/dev` 장치가 보이지 않았던 사실과 실제 GPU 실행 가능 여부를 구분한다.
- 세 후보 모두 `--device cuda:0`을 명시했다. 부모의 정책 추론·PPO는 GPU, 독립 worker의 Isaac Gym PhysX 물리는 기존 CPU 방식이다. CPU로 자동 대체한 측정이 아니다.
- 현재 기본 왼손 512상태/39행동·유연한 LH21 제어·성능 기반 보상, `05_BN2-131-B_solo`의 67음 전체다. 초기 035/v14·native 대기 0·정책 준비 3초·240Hz 물리/60Hz 정책·headless를 유지했다.
- `large` 결합층 1024→1024→512·seed 7. N2/N4/N8은 각각 새 정책으로 **H1969·PPO 1회** 수행한다. 환경 수 외 설정 일치를 검사하며, 고정 Python 소스 410개와 실행 입력 SHA를 확인한다.
- 후보는 동시에 겹치지 않게 실행한다. 서로 다른 N은 배치·난수·수집 자료가 달라지므로 처리율을 연주 성능의 우열로 읽지 않는다.

## 전곡 부하와 처리율

| 환경 수 | 전이 | 수집 시간 | PPO 시간 | runner 시간 | runner 처리율 | 검사 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 | 3,938 | 15.5분 | 1.0초 | 15.6분 | 4.21전이/초 | 통과 |
| 4 | 7,876 | 18.4분 | 2.0초 | 18.5분 | 7.08전이/초 | 통과 |
| 8 | 15,752 | 23.0분 | 6.4초 | 23.2분 | 11.32전이/초 | 통과 |

처리율은 `report.transitions / report.wall_s`이며 runner 시작~보고 구간 기준이다. CLI 바깥 초기 import와 최종 전곡 요약까지 포함한 전체 프로세스 처리율은 아니다. N8은 N2보다 수집 전이가 4배이므로 업데이트 1회의 실행 시간도 함께 비교한다.

## RAM·GPU 메모리

| 환경 수 | 가용 RAM 관측 최소 | GPU 전체 사용 관측 최대 | GPU 전체 여유 관측 최소 | Torch allocated 최고 | Torch reserved 최고 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 18.29GiB | 1346.0MiB | 10529.0MiB | 494.8MiB | 676.0MiB |
| 4 | 17.63GiB | 2238.0MiB | 9637.0MiB | 810.6MiB | 1170.0MiB |
| 8 | 15.91GiB | 4023.0MiB | 7852.0MiB | 1422.3MiB | 2158.0MiB |

- GPU 전체 사용/여유는 약 2초 간격 `nvidia-smi` 표본이다. 다른 프로세스의 사용량도 포함하며 순간 최고/최저를 보장하지 않는다.
- Torch 수치는 해당 부모 학습 프로세스의 실제 CUDA allocator 최고치다. `allocated`는 텐서 등에 할당한 양이고 `reserved`는 allocator가 확보한 영역이므로 같은 값이나 전체 GPU 사용량으로 취급하지 않는다.
- 가용 RAM은 다른 프로그램도 포함한 host `MemAvailable` 관측 최소다. runner 값은 제어 tick 표본도 포함한다. 단계별 RSS/PSS는 약 5초/단계 전환 표본이며 worker별 누적 HWM 합은 동시에 사용한 RAM의 최고치가 아니다.
- 외부 supervisor는 GPU 여유 1GiB·host 가용 6GiB를 보호 기준으로 사용한다. 프로세스 그룹의 종료·잔존 여부도 기록한다. 이 기준이나 기존 물리 안전을 완화하지 않았다.

세 후보는 기대 전이·PPO 1회·유한 모델/optimizer·CUDA 난수/메모리 사용·입력 SHA·persistent/worker/guard 감사를 통과했다. 집계상 안전 전곡은 14회, 물리 실패는 0회, **손별 전곡 음악 성공은 0회**다. 자원·실행 안정성과 압현 학습 성공을 구분한다.

원자료: [N2](n2/report.json) · [N4](n4/report.json) · [N8](n8/report.json) · [집계와 검사](comparison.json). 각 실행의 설정·계약·checkpoint·전이·에피소드·자원 기록을 보존한다.

## 저장 모델 재개·반복 확인

N8의 `final.pt`를 같은 8환경·large·CUDA 계약으로 strict resume하고 **H256·PPO 2회**를 추가 수행했다. 추가 4,096전이이며 누적 업데이트는 1→3회다.
재개 직후 모델·optimizer·부모 난수·curriculum을 포함한 payload는 이전 저장본과 metadata를 제외하고 정확히 같았다. 수집 길이와 이번 업데이트 수 외 설정도 일치한다.
가용 RAM 관측 최소 16.07GiB·실행시간 6.2분이다. 이 짧은 재개 시험의 메모리를 H1969 전곡 부하의 최고치로 대신하지 않는다. [재개 검사](repeat_verification.json) · [실행 보고](n8_repeat/report.json).

## 실행 예

프로젝트 [실행 환경 설정](/home/ajou/yigyu/3/guitar_learning/README.md)을 적용한 뒤, 아직 없는 새 출력 경로에 실행한다. 아래는 전곡 1업데이트 명령이며 100업데이트를 측정했다는 뜻이 아니다.

```bash
cd /home/ajou/yigyu/3
python -m guitar_learning.train \
  --hand left \
  --song 05_BN2-131-B_solo \
  --size large \
  --num-envs 8 \
  --device cuda:0 \
  --horizon 1969 \
  --updates 1 \
  --out /home/ajou/yigyu/3/runs/left_large_gpu_n8_01
```

같은 크기·손·곡·제어·PPO 계약끼리만 strict resume한다. `medium`을 `large`로 바꿔 재개하거나 이전 제어 계약을 암묵적으로 이전하지 않는다.

## 범위와 보존

- 한 seed의 전곡 1업데이트와 별도 H256 재개 시험이다. 16환경·100업데이트 장기 안정성·메모리 누수 부재·보상 진급·압현 수렴을 입증하지 않는다.
- [이전 CPU 측정](../guitar_learning_large_env_benchmark_v1/README.md)은 당시 CPU 명시 경로의 별도 결과이며 원문을 보존한다. 이번 GPU 처리율로 과거 CPU 결과를 다시 분류하지 않는다.

[고정 소스 SHA](source_manifest.json) · [CUDA 확인](cuda_probe.json) · [집계](comparison.json) · [재개 검사](repeat_verification.json) · [계획](PLAN.md) · [실행 감시 버전](controller_versions.json) · [독립 검수](review.json)
