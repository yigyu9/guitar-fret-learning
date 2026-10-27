# 구현·실험·학습 착수 결과

> 기준일: 2026-10-09. 원본 checkpoint와 실행 폴더는 보존했다.

## 구현한 것

- 정적 기타 배치 자료의 25개 단독 변화와 5개 조합을 source geometry에서 빠르게 걸러내는
  [screen 구현](/home/ajou/yigyu/3/stability_adapter_2/screen_static_guitar_pose_geometry.py)을
  추가했다.
- 30개 결과를 정적 native 후보 이름·의미각과 연결해 분석하는
  [analysis 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_static_guitar_pose_geometry.py)을
  추가했다.
- [실행 계획과 체크리스트](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/04_IMPLEMENTATION_EXPERIMENT_TRAINING_PLAN.md)에 결과와 실행 제약을
  반영했다. 세부 표와 방법 한계는
  [실험 phase 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_pose_geometry_screen_v1/README.md)에
  있다.

## 정적 형상 실험

원래 저장된 전신·양손 실제 native 상태를 고정하고 기타 배치만 바꿔 MuJoCo source mesh의
signed gap을 조회했다. 30개 전부에서 human–guitar 겹침이 한 쌍 이상 보고되어 전신 형상 gate를
통과한 배치는 없었다. `audience_yaw+10deg`는 왼손 겹침이 보고되지 않았지만 오른손·오른팔과
기타 사이 source 겹침이 20쌍 남았다. `elevation+10deg`는 LH:thumb3–기타 source gap이
−0.514 mm였다.

이 결과는 이전 고정 기타/손 관절 탐색의 반복을 줄이고, 기타 위치 하나를 옮기는 것만으로는
전신 충돌 문제를 해결하지 못한다는 점을 보탠다. 다음 물리 실험은 손·팔·기타의 상대 배치를
같이 다루는 방법을 비교해야 한다. 이 단계는 물리를 실행하지 않았고 어떤 자세도 채택하지
않았다.

## 학습 preflight와 미완료 게이트

- 현재 `rl38`은 PyTorch `2.4.1+cu121`이지만 CUDA 사용 가능 여부는 false, 장치 수는 0이다.
- Strike 1-env CPU smoke를 `/tmp` 출력 경로로 실행했지만 `training_resource_preflight`에서
  `strike Isaac Gym training requires CUDA`로 중단됐다. PPO update 및 run 출력 생성은 0이다.
- Fret 후보 `47,000`, `47,500`과 Strike 후보 `10,000`, `10,708` 모두 저장된
  strict G0 qualification이 false다. Fret 후보는 full-song 단계/봉인 qualification이 없고,
  Strike 후보도 봉인 qualification이 없다. 기존 metadata나 loader를 우회하지 않았다.

따라서 이 실행에서는 정책 학습이나 자유 기타 연주 actor 추론을 수행하지 않았다. 학습을 이어갈
첫 실질 단계는 GPU 환경에서 Fret를 full-song 평가 gate까지 학습·승급하고, 같은 checkpoint
계약을 쓰는 고정 기타 G0에서 Fret·Strike 결합을 검증하는 것이다. 이 source 승급과 GPU가
준비된 뒤 자유 기타 residual 학습을 시작한다. 대체 CPU 학습은 목표 물리환경과 다른 결과를
주므로 이번에는 임의의 synthetic 학습을 만들어 학습 완료로 계산하지 않았다.

수치·명령·qualification 상태는
[training_preflight.json](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/training_preflight.json)에 기록했다. 새 단계는
[작업 계획](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/04_IMPLEMENTATION_EXPERIMENT_TRAINING_PLAN.md)의 미완료 체크리스트에 남아 있다.
