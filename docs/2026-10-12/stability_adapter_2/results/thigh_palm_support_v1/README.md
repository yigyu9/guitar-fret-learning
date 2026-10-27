# 오른쪽 허벅지·왼손 손바닥 접근 재생

2026-10-07. 이 결과는 0.1초짜리 `clear_2um` native 실행에서 저장한 25개 pose(0–24 step, 240 Hz)를 source collision geometry에 다시 그렸다. 렌더링은 MuJoCo source-shape 재구성이며 PhysX 렌더나 cooked collider 검증이 아니다. 재생 과정에서 native 초기화·physics step은 추가하지 않았다.

## 후보 비교

하체와 root를 완전히 고정한 채 왼쪽 손목3관절·팔꿈치X의 초기각만 변경했다.
`clear_2um`의 기준 대비 보정은 아래와 같다. 다른 초기각과 기존 PD/팔 PI는 유지했다.

| 관절 | 기준 대비 초기각 보정 (rad) | 적용한 초기각 (rad) |
|---|---:|---:|
| L_Wrist_x | +0.0157279754 | −0.8906361675 |
| L_Wrist_y | +0.0162211214 | −0.3366271998 |
| L_Wrist_z | +0.0095207690 | −0.1319907905 |
| L_Elbow_x | −0.0110601404 | −0.8266583899 |

허벅지는 고정돼 있으므로 기타 생성 위치를 world XYZ로
(−0.415437,+0.012261,−1.026976)mm 이동했다. 초기 회전은 유지했고, 이 새 위치를
유지 목표로 삼았다. 생성 뒤 기타는 자유 상태이며 pose를 다시 덮어쓰지 않았다.
스트랩은 새 초기 경로에서 무장력 절대 길이를 계산한 뒤 실행 중 고정했다.
초기 source 손바닥 방향 proxy는 위쪽 반구이고 중심은 대응하는 국소 넥 아래였다.

| 실행 | 최대 기타 위치오차 (mm) | 최대 기타 회전오차 (°) | 초기 절대 strap rest length (m) |
|---|---:|---:|---:|
| 기준 | 2.279551 | 0.997176 | 1.1010801317960974 |
| `clear_50um` | 4.006289 | 0.637350 | 1.1018136421554945 |
| `clear_100um` | 4.006352 | 0.637339 | 1.1018136421554945 |
| `clear_150um` | 4.006696 | 0.637398 | 1.1018136421554945 |
| `clear_2um` (재생 후보) | 4.041302 | 0.641189 | 1.1018469719600776 |

`clear_2um`는 초기 source hull 간격이 가장 작은 후보여서 짧게 확인했으며 성능 최선 후보는 아니다. 기록상 초기 LH:palm–neck unsigned hull 간격은 1.896279 µm, 완료 step 1에는 0.212747 mm, step 24에는 38.065514 mm였다. 해당 수치는 source geometry 간격이며 실제 접촉력이나 cooked-shape 여유를 인증하지 않는다. 24개 native contact record에서 R_Hip contact는 24 step, LH:palm contact는 0 step이었다. native step 0 contact query는 사용할 수 없어 초기 contact 수를 추정하지 않았다. 마지막 저장 source pose에는 LH:palm–RH:index1 convex hull 교차가 기록됐지만, 이는 native contact 행이나 관통 깊이가 아니다.

### 시작·종료 장면과 전체 재생

시작 화면의 주황색·파란색 원과 연결선은 MuJoCo camera projection을 쓴 2D 설명 오버레이이며, source shape 가림을 무시한다. 원 크기는 예시일 뿐 거리 척도가 아니고, R_Hip 표시는 baseline preflight witness를 사용해 후보의 기록된 기타 이동량만 적용한 참고점이다. 손바닥–넥 표시는 후보의 step-0 source hull witness다. 어느 표시도 새 거리 계측이나 접촉 증거가 아니다.

![시작 자세와 projected witness 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/images/initial_annotated.png)

![0.1초 종료 저장 자세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/images/end_step_024.png)

![저장 trace의 기타 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/images/trace_metrics.png)

[전체 25-frame 재생 영상 (0.05×, 12 fps, 2.083 s)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/videos/clear_2um_saved_pose_0p05x.mp4)

영상은 25개 저장 pose만 같은 시간 순서로 표시한다. 사람은 회색, 기타는 파랑, 왼손은 초록, 오른손은 자홍색, strap 경로는 주황색이다. 느린 재생은 보기 편의를 위한 표시 속도이며 새 물리 시간이 아니다. 이 짧은 실행에서 지속 지지나 안정·연주 성공을 확인하지 못해 후보로 채택하지 않았다.

## 생성 및 재현

Producer [render_thigh_palm_support.py](/home/ajou/yigyu/3/stability_adapter_2/render_thigh_palm_support.py), 실행 직전 사본 [source_render_v2/render_thigh_palm_support.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/source_render_v2/render_thigh_palm_support.py), 실행 로그·SHA [render_execution_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_execution_v2.json), [render_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/render_manifest.json)를 참고한다. Manifest는 실제 116 입력 경로와 producer·helper·asset·출력 hash를 기록하고 입력 hash를 종료 시 실제 파일에서 다시 계산했다. ffprobe는 1920×720, 12/1 fps, 25 frames, 2.083333 s를 확인했다.

재현 시 기존 산출물을 덮어쓰지 않도록 아직 존재하지 않는 출력 경로를 지정한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib MUJOCO_GL=osmesa \
MPLCONFIGDIR=/tmp/stability2_thigh_renderer MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.render_thigh_palm_support \
  --phase /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1 \
  --out-dir /tmp/thigh_palm_support_reproduction
```

이전 출력과 원 manifest는 원래 경로인 [render/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render/render_manifest.json) 및 보존 사본 [render_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v1/render_manifest.json)에 같은 바이트로 남아 있다. 당시 producer 원문 사본은 남아 있지 않다. 이전 manifest에 기록된 producer SHA는 `bc451130be1101b4dd0b94387ea79927052717a8f92a05c051a93cf62d8c10f3`이며, v2 producer 사본은 v2 렌더 직전에 별도로 저장했다.

주요 원자료는 [비교 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/comparison_validated.json), [저장 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/short/clear_2um/trace.json), [contact 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/short/clear_2um/contacts.json)이다. 변경 경로와 실제 코드·계획 링크는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/CHANGED_FILES.md)에 모았다. [최종 독립 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/review.md:7)는 완료됐고 남은 지적사항이 없다.
