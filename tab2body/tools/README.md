# tab2body tools

이 디렉터리는 현재 실행 가능한 fret/strike 데이터 생성·학습 산출물·환경 진단 도구만 둔다.
회귀 검사는 [`../tests/`](../tests/)로 분리한다.

새 strike 도구:

- `register_song_bundle.py`: 검수된 Stage1 결과를 `data/song_bundles/<song_id>` 정본으로 등록하고 manifest 생성
- `build_fret_training_data.py`: JAMS 또는 검수된 `mapping/fingering.json`을 60Hz fret goal로 변환
- `build_strike_training_data.py`: fingering note를 최소 `[time,frame,string]` v1으로 변환
- `audit_strike_runtime.py`: A0~A4 GPU 환경·줄·충돌·tensor 계약 감사
- `plot_strike_training.py`: 단계·보상·F1·timing·zone·failure 곡선 저장
- `record_strike_rollout.py`: 같은 deterministic rollout을 remembered/current 두 시점 MP4로 저장
- `record_strike_visualized_rollout.py`: 기존 영상과 물리를 바꾸지 않고 실제 6개 줄의
  allowed/preferred/current lane과 `RH:pick` 가상점을 두 시점 진단 MP4로 추가 저장
- `strike_visualization.py`: 라이브 기타 좌표를 카메라 PNG로 투영하는 비충돌 CPU/PIL 오버레이
- `render_pick_grip_pose.py`: guitar 연구에서 얻은 A0 오른손 자세 렌더

이 도구들은 기존 pilot checkpoint가 아니라 새 `tab2body.strike_checkpoint.v1` 계약만 읽는다.
