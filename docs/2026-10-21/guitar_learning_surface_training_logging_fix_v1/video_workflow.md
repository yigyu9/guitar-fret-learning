# 초기·최종 평가와 최종 정책 전신 영상

이 도구들은 학습 패키지를 수정하지 않는다. 실제 GPU 평가와 GL 렌더링은 본학습 종료 후 작업 담당자가 순서대로 실행한다. 준비 중 CPU 검사는 선택 규칙·배열/시계·기존 준비 자세의 모델 좌표 readback만 확인하며 Renderer나 GL 컨텍스트를 열지 않는다.

## 1024환경 평가

원본 `guitar_learning_surface_training_v1/train1024_large_2000`과 첫 재개 `guitar_learning_surface_training_recovery_v1/resume1700`은 SIGFPE로 중단됐다. 어느 실행도 정상 완료로 표시하지 않는다. 원본 `checkpoint_000299.pt`는 optimizer300회, 첫 재개의 `checkpoint_000149.pt`는 optimizer450회다. 선택 이후 원본 update300~307의8개와 첫 재개 update150~184의35개는 최종 정책 체인에서 제외한다.

새 `resume1550/report.json`의 정상 완료1550업데이트·50,790,400전이·최종 optimizer2000회, 원본300회 prefix의9,830,400전이와 첫 재개150회 prefix의4,915,200전이, large/1024/H32/seed7/왼손/1969tick 계약을 확인해야 시작한다. 두 재개 입력이 각 선택 checkpoint SHA를 실제 고정했는지 확인하고 새 optimizer451~2000의1550개 연속 기록을 검사한다. CPU에서 원본300회 checkpoint↔첫 재개 initial300, 선택450회 checkpoint↔새 initial450의 모델·두 optimizer·RNG·curriculum이 실제 동일한지도 비교한다. 유효 정책 체인은300+150+1550회·65,536,000전이이며 **중단 없는 fresh2000 실행을 뜻하지 않는다**. Native 물리 에피소드는 각 재개 시 준비 자세에서 다시 시작한다.

새 소스는 JSON 쓰기의 FE_INEXACT trap을 잠시 마스킹하는 변경만 허용한다. 기존 `training/gpu_runner.py`, `recording.py`, `training_log_io.py`, `monitoring.py` 네 파일의 SHA 차이와 새 `training/json_io.py`, `tests/test_json_io.py` 두 파일 추가만 허용하며 나머지 입력 SHA와 물리·정책·보상 설정은 같아야 한다. 실제 차이 목록을 복구 체인에 기록한다. 평가·렌더의 모든 JSON 쓰기도 공개 `json_io.dump/dumps`를 사용하고, 이 helper는 원래 부동소수점 환경을 쓰기 직후 복원한다. 평가의 표준 JSON 읽기는 native 초기화 전, 렌더의 표준 JSON 읽기는 MuJoCo 초기화 전에 끝낸다.

초기 평가는 원본 중단 실행의 `train1024_large_2000/initial.pt`(0회), 최종 평가는 새 `resume1550/final.pt`(2000회)를 사용한다. 각각 strict PPO 전체 상태와 자체 저장 curriculum을 복원하며 `act(deterministic=True)`만 실행한다. PPO 업데이트와 curriculum 승급은 호출하지 않는다. 평가/캡처/combined 보고서에 이 복구 체인을 함께 기록한다.

```bash
cd /home/ajou/yigyu/3
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib /home/ajou/miniconda3/envs/rl38/bin/python /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_logging_fix_v1/evaluate_checkpoints.py
```

각 환경의 첫 종료만 채점한다. 배치의 다른 곡을 진행하기 위해 이미 종료한 환경은 필요할 때만 reset하며 이후 곡은 점수와 영상에서 제외한다. 모든 첫 곡이 끝난 마지막 tick에는 reset하지 않는다. 중요 lifecycle·원래 Python traceback·native faulthandler를 남기고 CUDA 동기화 후 실제 simulator를 닫아야 `report.json`이 생성된다.

평가별 출력:

- `first_episodes.jsonl`: 현재 환경이 내보낸 episode 원문을 한 번씩 저장한다. `left_note_ledger`, 손가락별 지표, 보상·비용 성분을 포함하며 과거 TRAIN 음별 이력을 추정하지 않는다.
- `targets.json`: 실제67음의 ID·원곡 매핑·현·프렛·손가락·시간·요구 clean 시간. `string`은0=high-e, `canonical_string_1based`는1=high-e, `source_string`은 원본0=low-E다.
- `report.json`: 원장을 중복 저장하지 않는 episode 요약, all1024/해당 정책의 안전 완주 집단별67음 집계, fixed curriculum·native GPU 종료·입력 SHA 정보.
- 최종 평가의 `poses_env0000.npz`~`poses_env0007.npz`: 미리 정한 환경0~7의 첫 곡만 준비 t0 및 실제60Hz endpoint로 기록한다. 106개 논리 body의 world pose/속도·105개 q/qd/목표·39개 적용 행동·실제240Hz 시계·음 진단 수를 포함한다. 좌표는 native env-local world이며 env origin을 더하지 않는다. 기타39마커는 현재 GPU 강체 transform으로 복원된 값이다.
- `capture_metadata.json`, `visual_initial.json`: 실제 평가에 사용한 이름 순서·시각화 자산·checkpoint SHA와 영상 선택 규칙.

대표 영상은 사전 환경0~7 중 **안전 전곡 완주 환경의 최저 ID**를 선택한다. 모두 실패하면 첫 곡이 가장 길었던 환경, 동률이면 최저 ID를 사용한다. 음악 점수로 최고 사례를 선택하지 않으며 그 결과를 `capture_metadata.json`에 기록한다.

## 전신 영상

GPU 평가가 정상 종료된 다음 실행한다. 기본값은 OSMesa 소프트웨어 headless 렌더링이며 CUDA/EGL 장면을 재실행하지 않는다.

```bash
cd /home/ajou/yigyu/3
CUDA_VISIBLE_DEVICES= MUJOCO_GL=osmesa LIBGL_ALWAYS_SOFTWARE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/ajou/yigyu/3 /home/ajou/miniconda3/envs/rl38/bin/python /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_logging_fix_v1/render_video.py
```

기존 `static_visual_v7.build_model/set_body_poses`로 원래 visible mesh를 저장된 몸체 자세에 직접 배치한다. MuJoCo 물리 적분·정책·보간을 실행하지 않는다. 실제 기타 마커에서 얻은 여섯 현을 추가한다. 모든 기록 프레임의 보수적인 mesh bounding sphere를 포함하도록 정면 카메라를 고정하고, 머리·발·기타가 자막 영역 밖의 화면 안에 들어오는지 매 프레임 확인한다.

영상은1280×720/60fps다. NPZ의 준비 프레임0은 보존하고 영상은 실제 endpoint 프레임1~종료를 사용하므로 영상 길이는 첫 곡의 실제 정책 시간과 같다. 자막은 해당 source endpoint 시각과 그때의 음·접근·접촉 후보 수를 표시한다. 몸체 pose readback 오차·MuJoCo 시간0·렌더 중 pose 불변을 감사하며 ffprobe로 크기·프레임 수·60fps·길이를 검사한다.

`final_video/final_fullbody_60fps.mp4`, 처음/중간/종료 예시 PNG, `pose_audit.json`, `presentation.json`, 입력 SHA와 영상 SHA를 생성한다. `source_visual.xml`은 원래 모델 구조이며 실제 고정 카메라 override는 `presentation.json`에 기록한다.

두 평가 모두 같은 곡·준비 자세의1024환경이며 각 checkpoint의 자체 curriculum/관측을 사용한다. 독립 seed 평가나 동일 관측의 가중치만 비교한 실험이 아니다. near는 접근, contact/clean은 새 기하 후보이고 실제 현 압력·음향·일반화 성공을 인증하지 않는다. 영상에 오디오를 합성하지 않는다. 실패 출력 디렉토리가 있으면 원본을 보존한 후 별도 시도로 관리하며 기존 결과를 덮어쓰지 않는다.

CPU 검사:

```bash
CUDA_VISIBLE_DEVICES= MUJOCO_GL=osmesa PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/ajou/yigyu/3 /home/ajou/miniconda3/envs/rl38/bin/python /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_logging_fix_v1/test_video_workflow.py -v
```
