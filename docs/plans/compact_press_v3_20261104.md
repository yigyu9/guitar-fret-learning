# 압현 관측·동시 유지 개선 v3

사용자 승인: 상태 공간·보상 개선 구현 및 `paper/framework/정리.txt` 원문 뒤에 간단한 추가 설명. 기준일 2026-11-04.

## 범위

기존 기본557 및 compact v2 소스·체크포인트·실행은 보존한다. 새 실행 코드는 `guitar_learning/`의 `compact_press_v3` 모듈에 둔다. GPU 학습·물리 검사는 실행하지 않고 CPU에서 검증한다. 기존 E4 준비 방식, 행동33축, 물리·PD·힘·접촉·PPO·노출 일정은 유지한다.

## 구현 계획과 확인 기준

- [x] 관측: 기존443/452에 접촉 상실3, 남은 시간1, 남은 실패 음 예산1, 동시 수행4를 추가한다. 총452/461. 종료에 사용되는 누적시간·남은 시간·실패 음 예산이 실제 관측에 포함됨을 확인했다.
- [x] 목표: 기존16에 접촉 연속시간·보상 진행률·달성·최장 clean·누락시간·수행 부족 정산·정산 완료·필요 clean 시간·음 길이·목표 가중치10을 추가한다. 26×8슬롯, 빈 슬롯은0.
- [x] 보상: 동시 발음 구간의 유지 예산을 개별50%와 전원 동시50%로 분배한다. 단일음과 전원 clean의 최대 유지 예산은 동일하다. 실패 tick 억제를 유지한다.
- [x] 측정: 목표 집합이 일정한 겹침 구간에서 동시 clean 누적·최장 연속·비율을 측정한다. 기존 개별 달성을 보존하고 전체 음·동시 구간 연속 유지를 별도 엄격 성공으로 판정한다.
- [x] 정책·실행: 768 결합, actor512→256→33 유지. v3 train/evaluate/render·엄격 재개를 연결하고 구버전 체크포인트를 거부한다.
- [x] 검증: 부분 reset, 수집 경계, 비정렬 시간 경계, 시간분할 가짜 동시 성공, 관측 조회의 원장 무변이, CPU PPO·저장·복원 검사.
- [x] 독립 검토 및 기존 소스 해시·정리.txt 원문 보존 확인.

변경 효과는 아직 학습 성능으로 검증하지 않았다. 성공은 기존 표면 기하·몸체 합력 기준이며 실제 현 압력·음향과 구분한다. 신경망 크기와 준비 방식의 효과를 비교할 때는 같은 E4 조건을 사용한다.

## 구현과 검증 결과

- 새 환경: `guitar_learning/gpu/compact_press_v3.py`, 동시 발음 구간 구성: `guitar_learning/gpu/press_coordination.py`.
- 새 정책: `guitar_learning/training/compact_press_v3.py`, 실행: `guitar_learning/tool/experiments/compact_press_v3.py`.
- 대응 검사: `guitar_learning/tests/test_compact_press_v3_{environment,policy,entry}.py`.
- 새24개와 기존66개 CPU 검사 총90개 통과, 통합 실행18.718초. 정책→환경4substep 연결, PPO 갱신·저장·복원, 구버전 체크포인트·입력 변경 거부를 포함한다. 물리 시뮬레이션 성공 검사가 아니라 텐서·환경 로직 검사다.
- 새7개 Python 파일의 Python3.8 구문 검사와 GPU 없는 CLI 도움말 확인. 기존 Python338개 SHA256 변경0개. `정리.txt`는 원문을 유지하고 끝에 요약만 추가했다.
- 독립 검토자 `press_ppo_audit`: 미해결 Critical/Warning 없음. 목표 차원 설명·접촉 타이머 이름을 구현과 일치시켰고, 최종 음별 평가 로그 추가도 재검토했다.
- `--size`는 기존 인자 호환을 위해 받지만 v3의 층 크기는 위 고정값이다. 상태·보상 계약이 달라 v2 체크포인트를 직접 재개할 수 없다. 표본 수·학습률·탐색·PPO·E4·물리·접촉·커리큘럼 일정은 유지했다.
- 각 동시 구간은 목표 집합이 바뀔 때 분리한다. 최장 동시 clean도 이 구간별 최댓값이다. 같은 손가락 또는 같은 줄을 동시에 두 목표에 배정하는 입력은 거부한다. 준비 구간만 겹치는 순차 목표는 허용한다.

CPU 회귀 검사:

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -B -m unittest \
  guitar_learning.tests.test_finger_skill_joint_start \
  guitar_learning.tests.test_finger_skill_policy \
  guitar_learning.tests.test_finger_skill_environment \
  guitar_learning.tests.test_compact_press_policy \
  guitar_learning.tests.test_compact_press_environment \
  guitar_learning.tests.test_compact_press_entry \
  guitar_learning.tests.test_decision_ppo \
  guitar_learning.tests.test_rollout \
  guitar_learning.tests.test_gpu_wrong_press_sources \
  guitar_learning.tests.test_gpu_control \
  guitar_learning.tests.test_compact_press_v3_environment \
  guitar_learning.tests.test_compact_press_v3_policy \
  guitar_learning.tests.test_compact_press_v3_entry
```

## 다음 실행

GPU가 비어 있음을 확인한 뒤, 기존 IsaacGym용 Python 환경에서 새 출력 디렉토리로 실행한다. 아래는 아직 실행하지 않은 초기 학습 명령이며, 기본 곡을 사용한다. 먼저 짧게 실행해 유효 관측·관절 움직임·원장 저장을 확인한 후 동일 E4 조건의 v2와 비교한다. 성능 개선·정적 동시 압현·전환 성공은 실물리 평가 전까지 미확인이다.

```bash
python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.experiments.compact_press_v3 train \
  --num-envs 64 --horizon 32 --updates 100 \
  --out runs/compact_press_v3_01
```
