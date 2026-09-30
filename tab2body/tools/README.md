# tab2body tools

이 디렉터리는 현재 실행 가능한 fret/strike 데이터 생성·학습 산출물·환경 진단 도구만 둔다.
회귀 검사는 [`../tests/`](../tests/)로 분리한다.

- `register_song_bundle.py`: 검수된 Stage1 결과를 `data/song_bundles/<song_id>` 정본으로 등록하고 manifest 생성
- `plot_fret_diagnostics.py`: fret 로그에서 손가락·오압현·관절 한계·자연스러움 그래프와 JSON 요약 생성
- `diagnose_fret_goal_pair.py`: 현재 goal-pair regime만 분리하고 표본 수로 가중해 손가락별 full-song 전이, 기존 압현 보존, 승급 gate와 희귀 chord 병목을 JSON/Markdown으로 진단
- `analyze_reference_hand_motion.py`: 사람 왼손 reference의 관절 각도 분포와 인접 손가락 연동 분석
- `build_right_hand_motion_profile.py`: 오른손 reference frame을 gesture/phase별 관절 분위수 profile로 변환
- `build_fret_training_data.py`: JAMS 또는 검수된 `mapping/fingering.json`을 60Hz fret goal로 변환
- `build_fret_pose_library.py`: 곡의 고유 손모양과 checkpoint의 검증된 자세 캐시를 라이브러리로 변환
- `build_strike_training_data.py`: fingering note를 최소 `[time,frame,string]` v3로 변환한다. 기존
  v1/v2 입력도 읽으며, v3는 선택적 source timing provenance와 근거가 있는 reviewed
  `merge`/`separate` override를 보존한다.
- `build_strike_plan.py`: raw strike 입력을 방향·strum microtiming·실제 traversal-edge 전이가
  포함된 `strike_plan.v4`로 컴파일한다. `--require-original-tempo-feasible`로 물리적으로
  실행 불가능한 원속도 계획 생성을 차단한다.
- `audit_strike_goal_quality.py`: 한 곡 또는 전체 bundle의 fingering→raw→plan→JAMS 정합성,
  묶음 경계, traversal-edge 간격, 방향 반전 재통과를 CPU에서 읽기 전용으로 검사하고
  `PASS`/`AMBIGUOUS`/`INFEASIBLE`로 분류한다.
- `audit_strike_runtime.py`: A0~A4/S0~S3 GPU 환경·줄·충돌·tensor 계약 감사
- `plot_strike_training.py`: 단계·보상·F1·timing·zone·failure 곡선 저장
- `record_strike_rollout.py`: 같은 deterministic rollout을 remembered/current 두 시점 MP4로 저장
- `record_strike_visualized_rollout.py`: 기존 영상과 물리를 바꾸지 않고 실제 6개 줄의
  allowed/preferred/current lane과 `RH:pick` 가상점을 두 시점 진단 MP4로 추가 저장
- `strike_visualization.py`: 라이브 기타 좌표를 카메라 PNG로 투영하는 비충돌 CPU/PIL 오버레이
- `render_pick_grip_pose.py`: guitar 연구에서 얻은 A0 오른손 자세 렌더

이 도구들은 현재 checkpoint 계약만 읽는다.
