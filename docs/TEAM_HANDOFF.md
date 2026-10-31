# 팀원 전달 안내 — 2026-10-31

현재 학습·평가 입력은 프로젝트 내부 파일을 사용한다. Python·CUDA·NVIDIA 드라이버·ffmpeg 등 설치 환경은 각 PC에 필요하다. 실행 방법은 [외부 자료 없는 실행 안내](PORTABILITY.md), 현재 연구 결과는 [프로젝트 현황](../CURRENT_STATUS.md)을 따른다.

## 요청한 두 자료

| 요청 | 현재 사용할 파일 | 설명 |
| --- | --- | --- |
| finger FK/native MCP·distal 대조용 trace.npz | [진단 입력 묶음](../data/diagnostic_inputs/finger_fk_native_v1/README.md)의 `trace.npz` | 기존 `baseline/trace_initial/trace_env0000.npz`를 바이트 변경 없이 전달용 이름으로 보존했다. |
| support_candidate.json | [내부 초기 자세 입력](../guitar_learning/assets/runtime_inputs/paper/initial_pose/archive/experiment_records/lower_body_release_v1/front_facing_pose_v1/source_v9/support_candidate.json) | 4,959바이트. SHA256 `15ae33e4b96a760c83cfad1dd12f7525ea007af526619d9c7e400a6a9ad67b65`. |

trace와 함께 `trace_metadata.json`, `joint_body_order.json`, `gpu_scene_initial.json`, `manifest.json`을 같은 디렉토리에서 받는다. q는1969×105, body_state는1969×106×13이며 환경0의 전곡1회 60Hz 기록이다. MCP와 끝마디의 정확한 몸체 인덱스·xyzw quaternion·좌표계·원본 SHA는 묶음 README와 manifest에 있다. 기타 논리 마커를 native 접촉점으로 해석하지 않는다.

## 이전 안내와 달라진 점

- 이전 failure_diagnosis의 다음 단계는 현재 작업 순서가 아니다. 현재는 손가락 목표각 position 직접 제어로 바뀌었으며 목표 전환v2까지 검증했다. 당시 incremental 비교 지시는 status의 `historical_next`로 보존했다.
- 정확히 `trace.npz`라는 기존 진단 파일명은 없었다. 현재 묶음은 실제 남아 있는 `trace_env0000.npz`와 같은 SHA의 자료이고, 새 실험이나 임의로 만든 궤적이 아니다.
- trace는 이전 초기 자세·판정·제어의 기준 정책 기록이다. 현행 v9 또는 전환v2 학습 성과를 뜻하지 않는다. 기존 finger FK의 정확성이 이번 파일 정리만으로 입증된 것도 아니다.
- `assets/runtime_inputs/.../archive/`는 현재 실행에 필요한 실제 자료다. 일반 archive 제외 정책 때문에 Git에서 빠질 수 있었으므로 assets 내부는 예외로 고쳤고 커밋 검사도 일치시켰다.
- docs의 원시 NPZ는 로컬 실험 산출물로 제외한다. 공유해야 하는 진단 입력은 `data/diagnostic_inputs/`에 모아 위치 기준으로 포함한다.

## 받는 쪽 확인

Git LFS로 실제 파일을 받은 뒤 프로젝트 루트에서 입력 검사를 실행한다. 모든 파일을 자동 커밋하거나 메일로 전송한 작업은 아니므로, 저장소로 전달할 때 새 진단 입력과 필수 자산 변경을 함께 반영해야 한다.

```bash
git lfs pull
python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.validation.portable_inputs
```

LFS 포인터만 받은 상태에서 배열을 열면 안 된다. 진단 입력 README의 NumPy 예제로 파일을 읽고 `manifest.json`의 SHA256을 대조한다. 과거 JSON에 남은 `/home/...`·`/media/...` 문자열은 원본 계보일 수 있으며 현재 읽어야 할 경로로 만들지 않는다. 현행 실행 입력 경로는 실제 프로젝트 내부로 해석하고 외부 탈출 경로는 읽기 전에 거부한다.

검증 범위·Git 정책 대조·실제 GPU 결과는 [작업 검증 기록](maintenance/self_contained_20261031/REPORT.md)에 모았다.
