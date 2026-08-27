# 4. 보류 항목

아래 항목은 중요하지 않아서가 아니라 현재 에셋·데이터·정상 rollout 분포가 부족해 강제 규칙으로
정하면 오히려 핵심 타현을 방해할 가능성이 있어 보류한다.

| 항목 | 보류 이유 | 재개 조건 |
|---|---|---|
| 물리 pick asset V2 | 현재 `RH:pick`은 index2에 붙은 질량·geometry·orientation 없는 marker | marker S0 정확도 gate 통과 + tip/base 또는 blade frame, collision mesh, 질량·관성·마찰, contact 안정성 준비 |
| 엄지-검지 pick grasp/slip | humanoid self-collision OFF이며 marker는 손에 고정돼 실제 잡기·미끄러짐이 없음 | 별도 pick actor + grasp constraint/상태 + slip/regrip detector + 안전한 reset transition 준비 |
| pick face/edge·attack angle | 한 점 marker에는 피크 두께·면·모서리·회전이 없음 | 물리 pick orientation과 face/edge별 crossing/contact 판정 및 영상 감사 준비 |
| string compliance와 force release | 현은 비충돌 marker라 load energy·변형·release force가 존재하지 않음 | 탄성/접촉 현 모델과 timestep 안정성, marker S0 대비 A/B oracle·성능 검사 준비 |
| Xu pretrained RH 직접 로드 | legacy는 free wrist 6+손 21=27 action, 현재는 어깨·팔꿈치·손목9+손21=30 action이고 관측·goal 의미도 다름 | legacy trajectory/손 자세를 현재 skeleton에 retarget하고 FK·action 계약을 검증한 뒤 teacher/BC seed로만 사용 |
| palm mute | upstream에 mute 주법 라벨이 없음 | mute 라벨·접촉 위치·음향 평가가 함께 준비됨 |
| 강한 jerk/energy 벌점 | 정상 빠른 pick/strum 분포가 없음 | `motion_diagnostics.json`의 phase·관절군 분포를 성공/실패 checkpoint 사이에서 비교 |
| fingerstyle 인간 모션 prior | 기존 Xu RH clip이 p/i/m/a와 전신 팔을 충분히 덮지 않음 | technique별 깨끗한 reference와 retarget 감사 |
| rest stroke(apoyando) | 인접 줄 landing을 일반 FP와 구분할 mode/annotation이 없음 | `stroke_mode`, landing string, 전용 detector 준비 |
| phrase 중 pick regrip | 현재 pick은 index2 고정 marker이며 잡고 놓는 동작이 없음 | 물리 pick/regrip transition 및 충분한 rest annotation |
| 자연스러움 절대 임계 | 사람 reference 분포 없이 임의 jerk/관절값을 인간 기준으로 부를 수 없음 | phase-aligned motion 진단 분위수와 blind 영상 평가 |
| 손목 soft range | 자세별 정상 범위 미측정 | motion audit로 6줄·양방향 성공 정책의 관절 분포 확보 |
| 오른팔 기타 관통 hard gate | analytical monitor는 구현됐지만 정상 strike의 허용 깊이 분포가 없음 | 성공/실패 motion audit의 current/swept depth가 분리되면 threshold·frame ablation |
| recovery corridor hard gate | field 밖 회복 비율과 역방향 RELEASE의 정상 범위가 없음 | 성공 A4 여러 곡의 motion audit와 영상이 일치할 때 경로 비용 후보화 |
| 양손 R18~R28 실행 | StrikeTask에는 왼손 goal/state와 공통 event coordinator가 없음 | shared `event_id,target_time`, FretReady와 독립 RH/LH/combined evaluator 구현 |
| `G:pluck_range` 즉시 벌점 | net force가 접촉 상대·점을 특정하지 못함 | 정상/기대기 사례의 force와 영상 대조 |
| 탄성 string/음향 | 현은 비충돌 marker라 진동·소리가 없음 | 기하 타현과 full 결합 완료 후 별도 연구 단계 |
| 좌손 chord-ready gate | strike 단독에는 왼손 정책이 없음 | fret/strike 양쪽 기준 통과 후 `task_full` 구현 |
| rasgueado | 여러 손가락이 순차적으로 펼쳐지는 별도 주법 | agent 순서·손톱 방향 annotation과 detector 설계 |
| slap/tap | 일반 pluck crossing이 아니라 충격/타격 주법 | 물리 접촉·충격량과 주법 라벨 준비 |

보류 항목은 core metric에 섞지 않는다. 먼저 진단값으로 기록하고 정상·실패 분포가 분리된다는 증거가
있을 때 보상 또는 종료로 승격한다.

현재 자동 진단 명령은 다음과 같다. 학습 기본 실행은 같은 보고서를 종료 후 자동 생성한다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python \
  tab2body/tools/audit_strike_motion.py \
  --checkpoint strike/training/runs/<run>/checkpoints/strike_<iteration>.pt
```

물리 pick V2의 항목은 하나씩 독립적으로 켜지 않는다. orientation 없는 mesh, slip을 관측할 수 없는
grasp, compliance 없는 contact처럼 일부만 추가하면 복잡도만 늘고 “실제 피크 release”를 검증할 수 없다.
재개 시 [레거시 pick 분석](../90_references/LEGACY_GUITAR_PICK_ANALYSIS.md)의 V2 조건을 한 묶음의
설계·A/B 실험 계약으로 먼저 동결한다.
