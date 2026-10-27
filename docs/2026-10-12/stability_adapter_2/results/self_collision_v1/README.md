# Humanoid 내부 충돌 OFF/ON 저장 pose 시각화

2026-10-07. 동일한 `near2µm` 초기 자세, 기타 목표, 0N 초기 strap 법칙에 해당하는 고정 절대 길이 1.1018469719600776m, PD/PI 조건에서 실행한 OFF/ON 각 0.1초 결과를 저장 pose로 다시 표시했다. Root와 하체는 고정, 기타는 자유 상태였다. 그림 생성에서는 native 초기화나 물리 실행을 추가하지 않았다.

## 저장된 실행 요약

| 모드 | 최대 기타 위치오차 (mm) | 최대 기타 회전오차 (°) | self-contact raw 행 | 양의 raw `lambda` 행 |
|---|---:|---:|---:|---:|
| OFF | 4.041302462 | 0.641189242 | 0 | 0 |
| ON | 4.035079218 | 0.639348515 | 9 | 6 |

ON 기록 9행은 한 `human/LH:palm`–`human/RH:index1` 쌍이며 저장된 완료 step 20–24에 분포한다. 처음 기록된 행은 step 20 (0.083333초)이다. 이것은 정확한 최초 물리 접촉 시각을 뜻하지 않는다. 양의 raw `lambda` 6행은 힘 단위로 교정되지 않아 힘의 크기나 지지력으로 읽지 않는다. LH:palm–기타 contact 행은 두 모드 모두 0이다. 기타 오차의 작은 수치 차이는 안정화 성공을 입증하지 않는다.

초기 두 자세와 기타 목표·회전·strap 절대 길이·PD 설정은 일치하고 하체 상태는 그대로였다. ON mask 정책은 54개 active human body의 1,431쌍 중 1,115쌍을 허용하고 316쌍을 제외한다. importer 기본 행렬에 비해 323쌍을 추가 허용한 값이며 OFF 대비 변화량은 아니다. importer의 명시적 28개 제외와 동일 손 내부·연결부 제외를 유지했다. 좌·우 distal group에는 128/512 mask를 사용해 양손 및 비인접 body 조합을 허용한다. active human–guitar pair는 허용하고 기타 자체는 human mask와 분리된 예약 bit 4096을 사용했다. disabled proxy 제외 mask 1048575도 유지했다. 따라서 모든 self pair나 동일 손 손가락 사이 충돌을 전부 켠 상태는 아니다.

## 장면과 재생

왼손은 초록색, 오른손은 자홍색, 기타는 파랑, 나머지 인체는 회색이다. 시작 그림은 저장된 ON step 0 pose이며 native step-0 contact query는 사용할 수 없어 접촉을 표시하지 않는다.

![ON 초기 저장 pose: 전신·손과 기타 넥 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/images/initial_on.png)

아래 이미지는 OFF/ON의 0.1초 저장 pose를 같은 hands/neck 카메라로 비교한다. ON의 step 24에는 raw self-contact 행 1개가 있고, 24-step 누계는 9행이다.

![OFF/ON 완료 step 24의 손 확대 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/images/off_on_hands_step_024.png)

[ON의 전체 25 저장 pose 영상 (0.05×, 12 fps, 2.083 s)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/videos/self_collision_on_saved_poses_0p05x.mp4)

영상은 저장된 ON pose 0–24만 시간순으로 보여 준다. source collision geometry 재구성이며 PhysX 렌더도 cooked collider clearance 검증도 아니다. contact row 수는 충돌 이벤트 횟수, 연속 접촉, 힘, 원인 또는 안정적인 손 지지를 뜻하지 않는다. 손 사이 물리 상호작용 기록은 있었지만 지속 지지나 기타 안정화 성공으로 판정하지 않았다.

## Producer와 재현

[읽기 전용 renderer](/home/ajou/yigyu/3/stability_adapter_2/render_self_collision.py:1)은 기존 [`render_best_run_video.py` helpers](/home/ajou/yigyu/3/stability_adapter_2/render_best_run_video.py:61)를 재사용한다. 실행 직전 producer 사본은 [source_render_v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/source_render_v2/render_self_collision.py:1)에 저장했다. 최종 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/render_manifest.json)는 105개 raw/dependency 입력, 6개 renderer helper, 40개 source asset의 앞·뒤 SHA와 출력 해시를 기록한다. [실행 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_execution_v2.json)과 [log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_execution_v2.log)에 실제 명령, 환경, ffprobe 결과를 남겼다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib MUJOCO_GL=osmesa \
MPLCONFIGDIR=/tmp/stability2_self_collision MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.render_self_collision \
  --phase /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1 \
  --out-dir /tmp/self_collision_reproduction
```

첫 출력과 해당 producer는 원래 경로인 [render/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render/render_manifest.json) 및 같은 바이트의 보존 사본 [render_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v1/render_manifest.json), [source_render_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/source_render_v1/render_self_collision.py)에 보존했다. v1 source snapshot SHA는 당시 manifest의 producer SHA와 일치한다. 첫 시도에서 comparison manifest의 추가 입력 SHA를 producer에 포함하지 않은 실패도 [log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_execution_attempt1.log)에 남겼다. 이 시도는 이미지를 생성하지 않았다. 최종 render_v2가 canonical이다.

원자료 [OFF/ON comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/comparison.json), [importer filter probe](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/importer_probe.json), 각 모드의 report/state/trace/contact/self-contact/control/torque 파일은 같은 결과 폴더에 보존돼 있다. [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/CHANGED_FILES.md:1)에는 실제 코드·조건·계획 링크를 모았다. [최종 독립 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/review.md:7)는 완료됐고 남은 지적사항이 없다.
