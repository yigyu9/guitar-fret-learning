# 손가락 FK와 native 몸체 관측 비교용 전달 자료

이 디렉토리의 실제 파일만으로 기존 진단의 관절각과 몸체 위치·회전을 읽을 수 있다. 원래 `trace_env0000.npz`를 전달용으로만 `trace.npz`라는 이름으로 보존했다. 원자료는 삭제하거나 다시 생성하지 않았다. 현재 학습 모델의 새 결과가 아니라 2026-10-27 초기 기준 정책의 env0·전곡 1회 기록이다.

- `trace.npz`: 관절각 q와 qd는1969×105, 몸체 상태는1969×106×13. `score_time_s`로 정렬한다.
- `trace_metadata.json`: 수집 당시105관절 순서·기준각·native 한계·60Hz 표본/240Hz 물리·정책 모드.
- `joint_body_order.json`: 정확한 joint/body 순서와 상태13열 정의. 이 순서의 근거인 내부 initial_values.json SHA는 수집 당시 입력 봉인 SHA와 같다.
- `gpu_scene_initial.json`: native68몸체/논리106몸체, 물리·장면 설정.
- `manifest.json`: 원래 경로·SHA256·배열 목록·요청받은 support_candidate의 현재 내부 경로.

## 읽는 예

프로젝트 루트에서 NumPy가 설치된 Python으로 실행한다. Isaac Gym을 띄울 필요가 없다.

```python
import json
import numpy as np
from pathlib import Path

p = Path('data/diagnostic_inputs/finger_fk_native_v1')
order = json.loads((p / 'joint_body_order.json').read_text(encoding='utf-8'))
with np.load(p / 'trace.npz', allow_pickle=False) as trace:
    q = trace['q']
    index_mcp = order['body_names'].index('human/LH:index1')
    index_distal = order['body_names'].index('human/LH:index3')
    mcp_pose = trace['body_state'][:, index_mcp, :7]
    distal_pose = trace['body_state'][:, index_distal, :7]
    time_s = trace['score_time_s']
    print(q.shape, mcp_pose.shape, distal_pose.shape, time_s[[0, -1]])
```

MCP는 각 손가락의 `*1`, 끝마디는 `*3` 몸체다. 관측은 환경 로컬 좌표, quaternion은xyzw 순서다. FK를 계산할 때 q좌표를 임의의 XYZ Euler로 바꾸지 말고 해당 모델의 joint axis와 native 좌표 정의를 따른다. 인간 몸체66개의 위치·회전은 native 관측이고, 기타의39개 논리 몸체는 단일 강체 기타에서 재구성한 마커다. 손가락/현 접촉점·현 압력·음향의 정답 데이터는 아니다.

## 같이 요청받은 초기 자세 입력

`support_candidate.json`은 이미 다음 내부 경로에 있다. manifest에 크기와 SHA를 기록했고 Git 정책에서 assets 내 archive를 필수 입력으로 허용했다. 파일을 별도로 복제할 필요는 없다.

`guitar_learning/assets/runtime_inputs/paper/initial_pose/archive/experiment_records/lower_body_release_v1/front_facing_pose_v1/source_v9/support_candidate.json`

## Git으로 전달

이 입력은 `data/diagnostic_inputs/`에 있어 docs의 원시 NPZ 제외 규칙에 걸리지 않는다. `.gitattributes`의 NPZ 규칙에 따라 Git LFS를 사용하므로 수신자는 `git lfs pull`로 실제 배열을 받아야 한다. .gitignore 정비만으로 파일이 자동 커밋되지는 않는다. 과거 docs 대량 로그 전체를 공유하지 않고 이 작은 근거 묶음과 현재 실행 입력을 공유한다.
