# large 모델의 병렬 환경 수 실측

2026-10-20. 현재 기본 왼손 학습의 **CPU 시험에서는 `--size large --num-envs 8`을 권장**한다. 시험한2/4/8환경 중8환경까지 전곡 수집·PPO·저장·최종 감사가 통과했고 처리율도 가장 높았다. **16환경은 측정하지 않았으므로8을 절대적인 최대치로 해석하지 않는다.**

## 조건

- i9-13900·논리CPU32개·RAM약31.1GiB. 현재 실행 환경에서 GPU를 인식하지 못해 정책과 물리를 모두 CPU로 측정했다. [하드웨어](hardware_before.json) · [GPU 확인](gpu_probe.json).
- 현재 기본 왼손512상태/39행동·유연한 LH21 프로필·성능 기반 보상, 기본곡 `05_BN2-131-B_solo`의67음 전부다. native대기0·정책준비3초·물리240Hz/정책60Hz·headless를 유지했다.
- `large` 결합층1024→1024→512, seed7. 각 후보는 새 정책으로 시작해 **horizon1969·PPO1회** 실행했다. 환경 수 이외의 설정은 동일함을 검사했다. 서로 다른N은 난수 배치와 수집 자료가 달라지므로 연주 성능의 우열 비교가 아니다.
- 환경2→4→8을 동시에 겹치지 않게 실행했다. 각 환경의 물리 장면은 독립적이며, 부모의 정책은 공유한다. source410개와 실행 입력 SHA·원래 물리/guard 계약을 유지했다.

## 전곡 부하 결과

| 환경 수 | 수집 전이 | 수집 시간 | PPO 시간 | runner 전체 시간 | runner 처리율 | 가용 RAM 관측 최소 | 안전 전곡 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 3,938 | 15.4분 | 37.2초 | 16.1분 | 4.07전이/초 | 18.81GiB | 2/2 |
| 4 | 7,876 | 18.5분 | 137.8초 | 20.9분 | 6.28전이/초 | 17.75GiB | 4/4 |
| 8 | 15,752 | 23.0분 | 517.0초 | 31.7분 | 8.29전이/초 | 15.73GiB | 8/8 |

세 실행 모두 기대 전이 수·PPO1회·유한한 모델/optimizer·persistent 감사·실행 입력 SHA·물리 flags·worker/guard 검사를 통과했다. 물리 실패는0회이며 **손별 전곡 음악 성공도0회**다. 자원/실행 안정성과 압현 학습 성공을 구분한다.

원자료: [2환경](n2/report.json) · [4환경](n4/report.json) · [8환경](n8/report.json) · [집계와 검증](comparison.json). 각 디렉토리에 `settings.json`, `training_contract.json`, `initial.pt`, `final.pt`, 전이·에피소드·자원 기록을 보존했다.

처리율은 `report.transitions / report.wall_s`이며 runner 시작~보고 구간 기준이다. CLI 바깥 초기 import와 최종 전곡 요약까지 포함한 전체 프로세스 처리율은 아니다. 8환경은2환경보다 수집량이4배이므로 한 업데이트의 실행시간도 길다. 같은100업데이트를 지정하면 총 전이는393,800개에서1,575,200개로 늘어난다.

현재 PPO는 각 actor minibatch 갱신 뒤 전체 수집분으로 KL을 검사한다. 환경 수와 전곡 batch가 늘면 최적화 비용도 커지므로 수집 처리율만으로 설정을 고르지 않았다. 구현은 [ppo.py](/home/ajou/yigyu/3/guitar_learning/training/ppo.py)를 따른다.

## 저장 모델 재개·반복 확인

8환경 모델의 `final.pt`를 strict resume하고, 같은8환경·large에서 **H256/PPO2회**를 추가 실행했다. 이 시험은 짧은 반복 갱신과 상태 복원 확인이며 위 H1969 전곡 최대 부하 시험과 구분한다.

- 추가 4,096전이·누적 PPO 3회. 모델·optimizer·부모 난수·curriculum의 재개 직후 payload는 이전 저장본과 metadata를 제외하고 동일하다.
- 반복 실행의 환경 수·곡·손·모델·제어·PPO 설정은 baseline과 같고 수집 길이와 이번 업데이트 수만 다름을 검사했다.
- 메모리 여유 관측 최소16.92GiB, 실행시간6.6분. [반복 검증](repeat_verification.json) · [실행 보고](n8_repeat/report.json).

## 실행 예

프로젝트 [실행 환경 설정](/home/ajou/yigyu/3/guitar_learning/README.md)을 적용한 뒤, 아직 없는 새 출력 경로에 실행한다. 아래는 이번 측정과 같은CPU에서 시작하는 명령이다.

```bash
cd /home/ajou/yigyu/3
python -m guitar_learning.train \
  --hand left \
  --song 05_BN2-131-B_solo \
  --size large \
  --num-envs 8 \
  --device cpu \
  --updates 100 \
  --out /home/ajou/yigyu/3/runs/left_large_n8_01
```

동일한 `large`·손·곡·제어 계약끼리만 저장 모델을 재개한다. `medium` 모델을 `large`로 바꿔 strict resume하는 것은 지원하지 않는다. 상세 저장/재개 흐름은 [학습 흐름 문서](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)를 따른다.

## 범위와 자원 해석

- 이번 결과는 한 seed의 전곡1업데이트와 별도 H256 반복 시험이다.100업데이트 장기 실행·메모리 누수 부재·보상 진급·압현 수렴을 입증한 결과는 아니다. GPU가 정상 인식되는 환경의 성능도 별도다.
- 가용 RAM은 당시 다른 프로그램의 사용량을 포함한 host MemAvailable 관측값이다. 전체 실행 최소에는 제어 tick 표본과 모니터 표본이 포함된다. 단계별 RSS/PSS/가용 RAM은 약5초 및 단계 전환 시의 표본 통계로, 순간 극값을 보장하지 않는다.
- `*_rss_current_*`는 현재 사용량 표본 최대이고, `*_lifetime_hwm_*`는 그 단계에서 읽은 프로세스 시작 이후의 누적 최고치다. worker별HWM합은 동시에 사용한RAM의 최고치가 아니며 공유 페이지도 중복 포함할 수 있다.
- 기존4GiB자원 보호와 물리 안전을 유지했다. 후보 증가 판단에는 최소6GiB여유를 기준으로 사용했다. 학습 코드와 과거 실행 결과를 바꾸지 않았다.

[고정 소스 SHA](source_manifest.json) · [작업 계획](PLAN.md) · [독립 검수](review.json)
