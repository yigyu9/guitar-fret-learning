# tab2body tests

`tools/`의 실행 명령과 회귀 검사를 분리한 디렉터리다.

- `test_fret_*`와 규칙별 검사: fret goal/reward/safety/episode 계약
- `test_base_*`: 공용 Isaac 환경 reset/action/finite 계약
- `test_ppo_*`, `test_checkpoint_*`, `test_run_layout.py`: 공용 학습 배관 계약
- `test_train_task_dispatch.py`: `train.py --task fret|strike` 공용 진입점 dispatch 계약
- `test_song_bundle_paths.py`: 곡별 정본 경로·기본 goal·manifest 가용성

새 `test_strike_*`는 다음을 검사한다.

- 최소 goal schema와 time/frame/string 변환
- finite swept crossing, 방향·깊이·속도, zone, 물리 re-arm과 CPU/CUDA 동등성
- A0~A4 보상 masking과 완료-episode 기반 승급, no-evidence streak, 100→67→50 ms state 복원
- 허용창 전 timing 표본 pooling과 A4 zone attempt/hit 저장공간 분리
- A3 miss 즉시 종료와 실제 hit의 12-frame recovery 분리
- 단계별 평가 gate, checkpoint/plot/두 카메라 artifact 계약
- 기존 영상을 보존하는 strike zone/pick 진단 경로, 실제 6개 유한 줄 clip,
  가상 `RH:pick` 표시와 CPU/PIL 투영 계약

PPO의 재사용 관측 버퍼 회귀 검사는 공용 정확성 계약이므로
`test_ppo_actor_advantage.py`에도 유지한다.
