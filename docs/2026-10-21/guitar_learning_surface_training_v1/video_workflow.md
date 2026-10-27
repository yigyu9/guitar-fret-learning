# 초기·최종 평가와 최종 정책 전신 영상

이 도구들은 학습 패키지를 수정하지 않는다. 실제 GPU 평가와 GL 렌더링은 본학습 종료 후 작업 담당자가 순서대로 실행한다. 준비 중 CPU 검사는 선택 규칙·배열/시계·기존 준비 자세의 모델 좌표 readback만 확인하며 Renderer나 GL 컨텍스트를 열지 않는다.

## 1024환경 평가

`train1024_large_2000/report.json`의 정상 완료2000회·65,536,000전이와 large/1024/H32/seed7/왼손/1969tick 설정, 모든 원래 입력 SHA가 일치해야 시작한다. 초기0회·최종2000회 checkpoint를 각각 strict PPO 전체 상태와 저장된 curriculum 상태로 복원한다. `act(deterministic=True)`만 실행하며 PPO 업데이트와 curriculum 승급은 호출하지 않는다.

```bash
cd /home/ajou/yigyu/3
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib /home/ajou/miniconda3/envs/rl38/bin/python /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_v1/evaluate_checkpoints.py
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
CUDA_VISIBLE_DEVICES= MUJOCO_GL=osmesa LIBGL_ALWAYS_SOFTWARE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/ajou/yigyu/3 /home/ajou/miniconda3/envs/rl38/bin/python /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_v1/render_video.py
```

기존 `static_visual_v7.build_model/set_body_poses`로 원래 visible mesh를 저장된 몸체 자세에 직접 배치한다. MuJoCo 물리 적분·정책·보간을 실행하지 않는다. 실제 기타 마커에서 얻은 여섯 현을 추가한다. 모든 기록 프레임의 보수적인 mesh bounding sphere를 포함하도록 정면 카메라를 고정하고, 머리·발·기타가 자막 영역 밖의 화면 안에 들어오는지 매 프레임 확인한다.

영상은1280×720/60fps다. NPZ의 준비 프레임0은 보존하고 영상은 실제 endpoint 프레임1~종료를 사용하므로 영상 길이는 첫 곡의 실제 정책 시간과 같다. 자막은 해당 source endpoint 시각과 그때의 음·접근·접촉 후보 수를 표시한다. 몸체 pose readback 오차·MuJoCo 시간0·렌더 중 pose 불변을 감사하며 ffprobe로 크기·프레임 수·60fps·길이를 검사한다.

`final_video/final_fullbody_60fps.mp4`, 처음/중간/종료 예시 PNG, `pose_audit.json`, `presentation.json`, 입력 SHA와 영상 SHA를 생성한다. `source_visual.xml`은 원래 모델 구조이며 실제 고정 카메라 override는 `presentation.json`에 기록한다.

두 평가 모두 같은 곡·준비 자세의1024환경이며 각 checkpoint의 자체 curriculum/관측을 사용한다. 독립 seed 평가나 동일 관측의 가중치만 비교한 실험이 아니다. near는 접근, contact/clean은 새 기하 후보이고 실제 현 압력·음향·일반화 성공을 인증하지 않는다. 영상에 오디오를 합성하지 않는다. 실패 출력 디렉토리가 있으면 원본을 보존한 후 별도 시도로 관리하며 기존 결과를 덮어쓰지 않는다.

CPU 검사:

```bash
CUDA_VISIBLE_DEVICES= MUJOCO_GL=osmesa PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/ajou/yigyu/3 /home/ajou/miniconda3/envs/rl38/bin/python /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_v1/test_video_workflow.py -v
```
