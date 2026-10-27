# Three-face support-loss diagnostics

이 단계는 두 선행 조건의 실제 저장 자세에서 palm source-hull gap, 선택 facet 방향, 관절별 좌표 오차를 여섯 시점으로 비교한다. 별도의 fresh native 5초 실행에서는 같은 saved-target 설정으로 초기값과 shape-property query를 기록했다. 저장 배열 다섯 개와 두 영상의 SHA가 기준 재실행과 일치한 관측은 성능 gate가 아니며, 후보 채택이나 안정성 성공을 뜻하지 않는다.

## 요약

| 항목 | 기록 |
|---|---|
| fresh native 실행 | `saved_finger_targets`, 초기화 1회, 1200 physics step, simulation 5.0 s; runner elapsed 95.3363209029194 s |
| native 상태 | root와 하체가 고정된 조건. 몸통 9개 PD 목표와 기타 목표·절대 strap 길이를 보존했고, 팔·손을 포함한 66축 제어 인터페이스를 유지했다. 손–몸통 내부 충돌은 활성 상태이며 연결부 및 같은 손 제외 규칙을 유지했다. 자세를 step마다 다시 쓰지 않았다. |
| 시작 설정 | `initial_values.json`에 실제 81 관절각, 기타 world 목표 위치·xyzw 회전, 속도, PD, solver, 절대 strap 길이와 입력 trial을 기록했다. 절대 strap rest length는 1.1018469719600776 m, 시작 route 길이는 1.0868332051527874 m다. |
| native 검사 | report checks 전부 true, constraint violation 없음. native shape-property query는 상태·PD·Python target을 보존했다. 양 actor의 읽힌 friction은 1.0, contact offset은 약 0.0001 m, rest offset은 0 m다. 원시 contact friction을 재료 마찰계수로 읽지 않는다. RSP thickness 필드는 보존했지만 PhysX 작동값이라고 해석하지 않는다. |
| 비교 자료 | 그래프는 두 이전 조건의 실제 저장 자세를 0, 0.1, 0.25, 0.5, 1, 5초에서 후처리한 것이다. 새 native 실행의 pose replay가 아니다. source 간극·facet 방향은 접촉 판정이나 cooked clearance가 아니다. |

## 저장 자세 비교

| 조건 | 시점 | 손바닥 source hull gap (mm) | 최대 좌표 오차 arm12 / finger21 / torso9 (°) |
|---|---:|---:|---:|
| Saved finger targets | 0 s | 2.129621 | 16.526690 / 2.686505 / 0 |
| Saved finger targets | 5 s | 9.894188 | 21.711862 / 0.567693 / 4.229168 |
| Initial finger targets | 0 s | 2.129621 | 16.526690 / 0 / 0 |
| Initial finger targets | 5 s | 5.392989 | 21.731453 / 0.071113 / 4.232301 |

전체 여섯 시점은 그림 114에 있다. x축은 `[0, 0.1, 0.25, 0.5, 1, 5] s` 순서의 **범주형 표본**이다. 점을 잇는 선은 표본 안내이며 시간 간격에 비례하지 않고, 사이의 연속 궤적이나 접촉을 뜻하지 않는다. 군별 최대 절대 좌표 오차는 실제 관절각의 좌표별 차이를 rad에서 degree로 변환한 값이며 SO(3) 오차가 아니다.

Saved 조건 손바닥 source-hull gap은 2.129621 mm에서 9.894188 mm로 증가했고, 초기 finger 조건의 종료값은 5.392989 mm다. finger 최대 좌표 오차는 종료 때 각각 0.567693°와 0.071113°다. 낮은 finger 오차가 더 좋은 기타 유지 결과를 뜻하지 않는다. palm 선택 facet의 inward alignment는 0.994174에서 0.979404/0.978361로 변했고 thumb 선택 facet은 시작에 −0.816388이었다. 해부학적 pad 정체가 검증되지 않았으며 이 값과 hull 근접성만으로 해당 면의 접촉 또는 지지 상실 원인을 정하지 않는다.

그림 115는 두 이전 조건의 저장 pose 중 step 0, 120, 1200에서 여섯 손 hull을 기타 좌표계 G의 CPU source geometry에 배치한 도식이다. 좌표와 단위는 G-local mm이고 기타 source 형상은 front/rear/side 표시를 위해 유한 polygon으로 그렸다. 모든 패널은 공통 범위와 같은 축 비율을 쓴다. Isaac Gym 장면 렌더, PhysX cooked 형상, 힘 벡터 또는 면 접촉 검증이 아니다.

## 그림과 실제 영상

### 그림 114 — 이산 source-hull 간극, 좌표 오차, facet 방향

![저장 자세의 여섯 범주형 시점별 palm source-hull 간극, 관절 좌표 오차와 thumb/palm 선택 facet 방향](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifacts_v3/support_loss_metrics.png)

왼쪽 패널은 `rows.metrics[LH:palm].hull_gap_m × 1000`의 mm 값, 가운데 패널은 `max_abs_coordinate_error_rad`의 arm12/finger21/torso9 값을 degree로 변환한 값, 오른쪽은 `inward_alignment_dot` 무차원 값이다. 선은 여섯 실제 표본을 안내한다.

### 그림 115 — 저장 손 hull과 세 기타 source polygon

![저장된 두 조건의 step 0, 120, 1200 실제 pose를 사용한 CPU source geometry 배치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifacts_v3/support_loss_source_geometry.png)

현재 fresh native 실행 영상 두 개는 별도 자료다. 각각 151 frame, 30 fps, 1280×720, 길이 5.033333 s이며 물리 구간은 step 0–1200의 5초다. 초기값과 영상은 [native initial values](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/initial_values.json>), [hands video](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/hands.mp4>), [whole-body video](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/whole_body.mp4>)에서 확인한다. 해당 실행의 시작 입력 재현 판정은 원자료 체크로만 기록했으며, 성능 gate는 아니다.

## 입력·출처와 생성 이력

- 승인된 결론과 파일 범위: [artifact brief v3](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_brief_v3.json>); 분석 원자료: [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/analysis.json>).
- fresh native 결과: [report.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/report.json>), [shape_properties.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/shape_properties.json>), [runner execution](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/execution.json>).
- 최종 산출물: [v3 artifact manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifacts_v3/artifact_manifest.json>), [v3 execution metadata](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_execution_v3.json>). Producer SHA `539308ba005250e8d12a1e9732e80b11df11ea7d7871bf2441f480cfda268603`; exit 0, 11.23134584305808 s, `native_calls: 0`, 10,679 sealed inputs with matching before/after SHA and two PNG outputs.
- 보존된 v1 첫 시도는 generic font-family 탐색 오류로 exit 1, PNG 0개, native call 0이다: [artifact_attempt_v1 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_attempt_v1/>). 보존된 v2는 exit 0, 11.918461 s, native call 0이었으나 첫 시각 검수에서 3D 축 라벨과 legend가 겹쳐 최종 산출물로 채택하지 않았다: [artifact_layout_v2 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_layout_v2/>). v3는 배치 수정 후 두 PNG의 시각 QA를 통과했다. 이전 실행과 산출물을 덮어쓰지 않았다.
- Analyzer는 [analysis_source.py](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/analysis_source.py>)에서 확인한다. Native runner 참조는 [readback source](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/runner_source.py>)와 [source reference](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/source_reference/run_seed2_support_warmstart.py>)에 보존됐다. 단계별 review와 보존 대조는 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/review.md>) 및 [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/final_verification.json>)에서 확인한다.

이 결과는 고정 root/하체 조건에서 측정한 source 간극·방향·오차의 범위를 기록한다. 접촉·지지의 반복성 및 기타 오차 기준을 포함한 전체 안정성 기준은 아직 판정되지 않았다. 계획과 색인은 [메인 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1502), [stability_adapter_2 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:839), [날짜별 산출물 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:507), [다음 미실행 진단 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_ARM_INITIAL_TARGET_PLAN.md:1)에서 확인한다.
