# v20 손가락 B 복귀 개선

승인한 [보상·제어 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_finger_reward_control_20261025.md)의 A를 기본 경로에 구현하고 B를 명시적인 비교 옵션으로 분리한다. 이번 작업은 구현·회귀·실제 GPU 구동·저장/재개 검증이다. 500회 성능 비교, 3,000회 학습과 자연스러움 개선의 입증은 별도 단계다. C 자동 복귀 제어는 아직 구현·적용하지 않는다.

## 적용 내용

- 관측 마지막 4열은 `idle_weight` 대신 실제 `standby_gate`다. 상태544·토큰24열·우선8·손가락별 직접입력20·3331단계 이력은 유지한다. 마지막 물리 표본에서 사라진 직전 접촉까지 보상과 같은 판정으로 전달하고, 관측 조회 자체는 원장·이벤트·시계를 바꾸지 않는다.
- B±15° 안은 품질1, 밖은 `Q=1/(1+Σ(excess/30°)²)`다. 기본 보상률은 `0.02×mean4(gate×Q)`/초로 손가락당 최대0.005/초다. 먼 자세에서도 이전 지수식보다 완만한 품질 차이를 남긴다.
- 본인 press−0.35..end·바깥0.15초 fade와 관련 목표 press−2..end의 근접/접촉 제외는 보존한다. B는 벌점·제어 목표·필수 경유 자세가 아니다.
- `--finger-standby-rate 0.04`는 별도 비교 계수다. 기본 실행에 자동으로 선택하지 않는다.
- `--finger-shape`를 명시하면 추종 중 `z=relu(DIP−PIP−50°)/30°`, `0.004×mean4(active/(1+z²))`/초를 기존 coordination 슬롯에 적분한다. 기본은0이다. 관절 비율·가동범위·움직임 속도를 강제하지 않는다.
- LH21 움직임 비용0, 누적 목표 `previous+4a/60`, native 가동범위·PD·힘·초기035/v14·자유 기타·물리·PPO·압현/달성 기준을 유지한다. CPU 왼손과 오른손 설정·계산은 기존 경로를 따른다.
- 관측 의미와 보상 계약이 달라 v19 이하 checkpoint는 거부한다. v20도 계수·옵션을 포함한 전체 계약이 같아야 strict resume한다.

## 진단

종료 에피소드의 `left_episode_diagnostics` v3에 다음을 저장한다. 매 프레임 대용량 추적을 학습 로그에 추가하지 않는다.

| 지표 | 분모와 해석 |
| --- | --- |
| 실제 지급량 | 손가락별 실제 보상률의240Hz 적분, 단계 계수·실패 control tick 전체 억제까지 환경 원장과 대조 |
| 실제 gate 연속구간 | `gate>0`와 `gate==1`을 분리해0.5/1/3초 이상 개수·시간·B대역 점유율 기록 |
| 악보 고정 대기창 | 본인 press−2..end의 합집합 바깥.1초 이상 창의 예정·관찰·유효·B대역 시간을 별도 기록 |
| 안정 복귀 | 시작 시 대역 밖이고 B 안에0.2초 유지한 첫 진입. 전체 창 관찰과3초 이내 조건을 모두 만족해야 성공 |
| 마지막 음 이후 대기 | 마지막 배정 음 이후5초 이상 창을 별도 집계. 미등장 손가락에는 마지막 음이 없으므로 해당 지표 평가 불가 |
| 초기 대기 품질 감소 | reset의 실제 B품질 대비 감소한240Hz 표본 비율. 첫 본인 press−2 전·full gate1·유효각도만 분모에 포함 |
| 실패·미관찰 | 예정 시간에는 남겨 두고 점유율을 주지 않음. 복귀 성공으로 세지 않으며 시작부터 B 안인 유지와도 분리 |

개수·예정 시간0은 평가 불가이며 자동 통과가 아니다. 실제 gate 구간은 정책의 접근/접촉으로 달라지므로 악보 고정창과 함께 읽어야 한다. 관절 한계 바깥 명령 비율은 기존60Hz `left_finger_motion.limit_outward_command_fraction`을 계속 기록한다.

## 보존과 검증

- 변경 전 Python459개와 문서17개, 총476개 원문·SHA는 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261025_before_finger_recovery_v20/manifest.json)에 보존했다.
- v19 체크포인트500/3000을 각각1,024환경 첫 종료곡으로 평가하고 각612입력SHA를 확인한 뒤 활성 소스를 변경했다. 이번 기준 평균은500회6.9375/67음(safe1018),3000회21.02246/67음(safe908)이다. GPU 물리는 같은 deterministic 정책도 재실행 궤적이 달라질 수 있다. 기존 평가를 덮어쓰거나 v20 성과로 재분류하지 않는다. [보존 확인](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/baseline_preservation.json).
- CPU 텐서 회귀와 실제 GPU 검증은 별도로 기록한다. 현재 [체크리스트](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/implementation_checklist.md), [독립 검수](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/independent_review.json)를 따른다.
- 관련 CPU342개와462Python 문법 검사를 통과했다. 실제 GPU A/B 각16환경65업데이트, A65→66 strict resume, large1024환경2업데이트를 정상 종료했다. 원시 로그 CRC/종료·체크포인트 SHA·실제 지급량/진단 원장도 검산했다. 모델·두Adam·모든 RNG·3331단계 상태를 정확 복원했고 실제 v19와 옵션이 다른 v20의 재개는 상태 변경 없이 거부했다. [CPU](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/cpu_validation.json) · [GPU 검산](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/gpu_verification.json).

## 새 비교 학습 명령

Isaac Gym 실행 환경을 설정한 뒤 프로젝트 루트에서 새 출력 경로로 실행한다. 아래 명령은 이번 작업에서500회 학습을 완료했다는 뜻이 아니다.

```bash
python -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu \
  --size large --num-envs 1024 --horizon 32 \
  --updates 500 --checkpoint-every 250 --seed 7 \
  --out /home/ajou/yigyu/3/runs/left_finger_recovery_v20_A_01
```

A의 복귀·음악 성능을 먼저 확인한다. 필요한 경우 새 출력에 `--finger-standby-rate 0.04` 또는 `--finger-shape`를 각각 분리해 비교한다. 옵션이 다른 저장본을 같은 계약으로 이어 학습할 수 없다. C 제어 보조·500회 비교·최종 후보3,000회·영상은 후속 검증 단계로 남는다.

## 짧은 구동 결과의 한계

| 실행 | 새 전이 | 종료곡 | 안전 완주 | 수집 중 평균 달성/67 |
| --- | ---: | ---: | ---: | ---: |
| gpu_A | 33280 | 16 | 15 | 0.625 |
| gpu_A_resume | 512 | 0 | 0 | — |
| gpu_B | 33280 | 16 | 16 | 0.5625 |
| gpu_large1024 | 65536 | 0 | 0 | — |

위 수치는 갱신되는 정책의 짧은 학습 수집이며 고정 정책 비교가 아니다. A/B 모두 충분히 학습된 정책이 아니고, large2회는1.067초 구동이라 전곡 안정성을 판단할 수 없다. A에는 물리실패1회가 있었고 B는16곡을 안전 완주했다. 이 작은 표본으로 장기 무실패나 자연스러운 자세·수렴을 주장하지 않는다. 이번 구현이 자세나 압현을 개선했는지는 승인 계획의500회 비교와 후속 평가로 확인해야 한다.
