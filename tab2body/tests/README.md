# tab2body tests

`tools/`의 실행 명령과 회귀 검사를 분리한 디렉터리다.

- `test_fret_*`와 규칙별 검사: fret goal/reward/safety/episode 계약
- `test_fret_v2_*`: 420D named-block ABI, model, checkpoint 및 v1/v2 비호환성
- `test_base_*`: 공용 Isaac 환경 reset/action/finite 계약
- `test_ppo_*`, `test_checkpoint_*`, `test_run_layout.py`: 공용 학습 배관 계약
- `test_train_task_dispatch.py`: `train.py --task fret|strike|full` 공용 진입점 dispatch 계약
- `test_full_*`: Canonical PlayEvent, rule Synchronizer, checkpoint·105D action·runtime 계약
- `test_song_bundle_paths.py`: 곡별 정본 경로·기본 goal·manifest 가용성
- `test_frozen_context_sampler.py`: 손가락별 적응 quota, 60/30/10 문맥 혼합, 고정 평가 cohort
- `test_frozen_context_eval_aggregation.py`: frozen 학습/평가 episode 분리와 raw evidence pooling
- `test_frozen_context_curriculum.py`: 가중치 변경 무-reset, 평가 1회 초기화, 승급 evidence 분리
- `test_fret_goal_pair_diagnosis.py`: 실행 중 로그를 변경하지 않는 goal-pair regime 분리, 조건부 표본 가중 및 손가락·희귀 chord 병목 판정

새 `test_strike_*`는 다음을 검사한다.

- 최소 goal schema와 time/frame/string 변환
- finite swept crossing, 방향·깊이·속도, zone, 물리 re-arm과 CPU/CUDA 동등성
- A0~A4 single→clean-recovery/S0~S3 strum 보상 masking과 완료-episode 기반 승급, no-evidence streak
- 2→6줄 span, `E0 endpoint→400→250→225→200→175→150→100→zone 100→67→50 ms` timing,
  tempo λ state 복원과 zone attempt/hit 저장공간 분리
- 마지막 줄만 남았을 때 방향대칭 final-string→exit 목표, 최대 투영 증가분의 cycle-safe terminal
  shaping과 timing 독립 physical-completion pulse
- down/up completed/event 및 scheduled-recovery raw count pooling, 최저 방향과 conditional/end-to-end
  recovery gate, 한 방향 evidence 누락 시 fail-closed
- 3-window endpoint 정체 탐지, 부족 방향 70/30 focus와 down/up 30/30 balanced holdout,
  focus PPO 표본과 uniform 승급 evidence 분리
- E0/T0에서 어깨·팔꿈치·손목 첫 9 action의 policy std `0.03` 하한과 update 뒤 clamp
- A3 miss 즉시 종료와 실제 hit의 12-frame recovery 분리
- matcher 결과와 독립적인 physical RELEASE 회복, 직전 줄·lane·방향 보존,
  READY miss phase 유지, 최소 회복 frame+detector re-arm 종료 gate
- direction `phrase_dp_microtiming_v3`/transition `entry_side_edge_gap_v2` roundtrip,
  exit→entry 직접 경로 기반 clearance, 두 lift waypoint와 첫 waypoint 목표 전환의 reach-potential reset
- motor phase·entry waypoint와 독립적인 물리 matcher 판정, phase 불일치 진단
- 겹치는 목표 window·전역 motor recovery보다 빠른 같은/서로 다른 줄 입력 거부와 time-authority 경계
- 단계별 평가 gate, checkpoint/plot/두 카메라 artifact 계약
- 마지막 완료 영상에서 1,900 iteration 뒤 다음 checkpoint를 고르는 주기 영상 scheduler,
  불완전 두-view 묶음의 재시도와 기존 완료 영상 재사용
- S0~S2의 강제 down/up × remembered/current paired 영상, 실제 방향 report와 capture 전후
  task runtime/RNG 복원
- motion 진단 JSON 경로·분포 요약과 학습 tooling provenance 계약
- strict curriculum 설정 매핑, checkpoint에 포함된 학습 lifecycle, 원자적 run manifest 갱신
- event failure의 노출 정규화·prior shrinkage, hard-window 10% 확률 상한과
  hard PPO/uniform-only S3 승급 evidence 분리
- 주기 영상·전체곡 평가 전후 failure-mining state·task RNG·reset generation 복원, report v2 완주 판정과
  `best_full_song.json` 선택·퇴행 경고
- S3 reward-alignment가 uniform F1·blocked·wrong evidence를 우선 사용하고 tempo 경계를
  넘어 가짜 경고를 내지 않는 계약
- CUDA/resource preflight 실패가 빈 strike run 디렉터리를 남기지 않는 실행 순서
- 기존 영상을 보존하는 strike zone/pick 진단 경로, 실제 6개 유한 줄 clip,
  가상 `RH:pick` 표시와 CPU/PIL 투영 계약
- bundle 전체의 canonical fingering/raw/JAMS/traversal-edge 품질 감사,
  `PASS/AMBIGUOUS/INFEASIBLE` 분류와 evidence 없는 reviewed override 거부
- 현재 v14 checkpoint/curriculum/environment strict 상태 계약. 327D S1/S2 actor-only transfer
  항목은 Strike-v1 호환 회귀이며 303D Strike-v2의 warm-start 권한이 아니다.

PPO의 재사용 관측 버퍼 회귀 검사는 공용 정확성 계약이므로
`test_ppo_actor_advantage.py`에도 유지한다.

`test_run_io.py`는 append journal의 동시 쓰기, 정상 record 복구, 해시·prefix·inode
불일치, 중간 손상과 검증할 수 없는 tail을 독립적으로 검사한다.
