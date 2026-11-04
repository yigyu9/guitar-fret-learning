# 기타 압현 학습 — V5

새 왼손 압현은 **V5**를 사용한다. 기본 진입점 `python -m guitar_learning.train`과 명시적 `tool.experiments.compact_press_v5`는 같은 V5 설정·환경·정책을 사용한다. 상태464/선택473, 목표26×8, 행동33 구조다. 이전 압현 학습·비교 실행기는 제거했으며 [이력](../docs/history/press_before_v5.md)에 과정과 대표 결과만 남겼다.

## 실행

Isaac Gym Preview4와 Torch를 사용할 수 있는 환경에서 프로젝트 루트를 기준으로 실행한다. 다른 PC에서는 먼저 [로컬 실행기](../scripts/README.md)를 준비한다. 아래 출력 경로는 매번 새 경로로 지정한다.

```bash
python scripts/tab2body.py run -m guitar_learning.train \
  --song 05_BN2-131-B_solo --size large --num-envs 1024 \
  --horizon 32 --updates 2000 --checkpoint-every 250 --seed 7 \
  --improvement-profile corrected --out runs/press_v5_01
```

이는 예시 예산이며 학습 성공을 보장하지 않는다. V5는 GPU 왼손 전용이다. `--size`는 기록되지만 상태·목표 인코더와 Actor·Critic의 폭은 V5 고정값이다. 실행 환경과 입력 자산은 [assets](assets/README.md)와 [이식성](../docs/PORTABILITY.md)을 따른다.

동일 소스·입력·정책 계약으로 재개할 때 아래 반복 수는 추가 학습량이다. 생략한 학습 조건은 저장본에서 읽으며 처음 계획한 구간→전체 노출 문턱을 다시 계산하지 않는다.

```bash
python scripts/tab2body.py run -m guitar_learning.train \
  --resume runs/press_v5_01/J/final.pt --updates 500 \
  --out runs/press_v5_resume_01

python scripts/tab2body.py run -m guitar_learning.tool.evaluation.evaluate_finger_skill \
  runs/press_v5_01/J/final.pt --scope full_song --num-envs 2 \
  --out runs/press_v5_eval_01

python scripts/tab2body.py run -m guitar_learning.tool.demonstration.render_finger_skill \
  --checkpoint runs/press_v5_01/J/final.pt --num-envs 2 \
  --out runs/press_v5_video_01
```

입력 SHA·설정·신경망 identity·정책/물리 계약이 다르면 거부한다. 활성 코드 정리 전의 저장본은 원래 봉인 runtime에서만 검증·실행한다. 이번 정리는 과거 checkpoint를 새 소스에 자동 이전하는 변경이 아니다.

## C1~C6 합성 목표

곡 대신 손가락 조합의 연속 압현을 학습하려면 [합성 목표 전용 안내](../docs/2026-11-09/압현_v5_합성목표연결_v1/README.md)를 따른다.

```bash
python -m guitar_learning.tool.experiments.press_sequence list
python -m guitar_learning.tool.experiments.press_sequence check --all
python scripts/tab2body.py run -m guitar_learning.tool.experiments.press_sequence train C1 \
  --size large --num-envs 1024 --horizon 32 --updates 2000 \
  --checkpoint-every 250 --seed 7 --out runs/press_v5_c1_01
```

C번들은 압현 시각을 원본대로 적용하는 전용 연결이 필요하다. 일반 곡용 `--song`에 C번들 ID를 직접 넣지 않는다. 평가·영상도 저장된 C조합·시각 계약을 사용한다.

## 구조와 학습 흐름

1. 등록 입력의 목표·시각·1~14프렛 범위·SHA와 v9 초기 자세를 검증한다.
2. V5 환경이 신체·기타 상태와 손가락별 현재/다음 목표를 만든다.
3. 상태464→256과 목표26→64×8을 결합해768차원을 만들고, Actor768→512→256→33에서 행동을 표본 추출한다. Critic은 독립된 인코더와768→256→256 뒤 보상·비용 값 두 개를 낸다.
4. 왼팔12·엄지5·나머지 손가락16축을 제어한다. 손가락은 v9 기준 직접 목표각, native 전체 범위·4rad/s 제한·기존 PD/힘 한계를 사용한다. 오른손6축 운반 칸은0이다.
5. 정책60Hz마다 새 행동, 물리240Hz 네 번의 접촉·보상·안전 측정을 수행한다. H32에서는32tick 수집 후 PPO를 갱신하며 진행 중인 장면·시계·음별 원장·종료 타이머를 유지한다.
6. 처음 계획한 전이 예산의25% 뒤 새로 reset하는 환경부터 구간 대신 전체 목표를 학습한다. 성공률 기반 전환은 아니다.
7. 정상 종료나 물리·손목 실패에서 해당 환경만 초기화하고, 반복 지표·에피소드 요약·저장본을 남긴다.

초기 탐색 표준편차는 팔·엄지17축0.15, 검지~소지16축0.35이며 학습 중에도 갱신한다. 이는 tanh 이전 정규분포의 값이다. 손가락 움직임 비용은0이다. 구체적인 관측 필드·보상·종료·PPO·저장은 [V5 코드 해설](../docs/2026-11-02/코드해설/V5_학습코드해설.md)에 모았다.

## 보상 조건과 출력

| 조건 | 기본 corrected 대비 변경 |
| --- | --- |
| `corrected` | 현재 V5 기준; 대기 맥락·유효 속도·예산 관측과 완료 평가 반영 |
| `preparation` | 대기 중 노출된 목표의 접근 신호를 최대치의10% 남김 |
| `full_hold` | 달성 문턱을 기존 음 길이40% 기준에서 전체 길이로 변경 |
| `combined` | 위 준비 신호와 전체 유지 문턱을 함께 적용 |

이 조건들은 보상 가중치를 자동 조절하는 장치가 아니다. 비교에는 같은 입력·물리·예산과 전체 유지·해제 완료 평가를 사용한다.

주요 출력은 `settings.json`, `report.json`, `J/final.pt`, `J/checkpoint_manifest.jsonl`, `J/learning_metrics.jsonl`, `J/episodes.jsonl`, `J/episode_metadata.json`, 입력·학습 계약과 손가락 진단이다. 항목별 보상은 `learning_metrics.jsonl`에서 확인한다. 에피소드는 압축 메타데이터를 복원하는 `training_log_io.iter_episode_rows()`로 읽는다. `report.completed`는 실행 완료이며 음악 성공이 아니다.

## 코드·도구·별도 정책

[코드 지도](docs/CODE_STRUCTURE.md) · [상세 해설](../docs/2026-11-02/코드해설/README.md) · [도구 안내](tool/README.md) · [타현27](tool/experiments/right27/README.md) · [전신37](docs/WHOLE_BODY_TRAINING.md).

공용 측정·기록 API와 V5 메타데이터에 남은 `finger_skill`, `v3`, `v4` 표시는 기존 로그 필드·수학·저장 계약의 식별자다. 구버전 압현 실행기나 선택 가능한 옛 신경망이 남아 있다는 의미가 아니다. 과거 문서·입력·모델은 당시 근거로 보존한다.
