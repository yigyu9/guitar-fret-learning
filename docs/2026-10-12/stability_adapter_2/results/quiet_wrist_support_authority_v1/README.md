# Quiet L_Wrist_y 양방향 목표 변화 — 두 실제 5초 응답

## 실행 조건과 비교 범위

기준선은 기존 `initial_middle3_alignment_v1`의 저장 native 자료이며, 이번에 새로 실행한 세 번째 조건이 아니다. 이번 phase에서 새로 수행한 것은 plus와 minus 두 조건으로, 각각 한 번 초기화해 1200 physics step(시뮬레이션 5.000초), 151개 프레임, 30 fps로 기록했다. CPU PhysX이며 두 조건 모두 constraint violation은 0이다. 새 actor 추론과 학습 업데이트도 0이다. [저장 분석 42개 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis.json:1)와 [두 실행의 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/plus/initial_values.json:1), [minus 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/minus/initial_values.json:1)을 보존했다.

초기 81각, 기타 world 초기 상태, 절대 스트랩 rest length 1.1018469719600776 m, PD 설정, 고정 root/하체, 자유 기타, body9의 KP×2·KD×√2, 기존 L_Wrist_x 사인 파형과 손가락 유지 목표를 그대로 뒀다. 시작 Wrist_y 실제각은 0.176372841 rad이고 원래 유지 목표는 0.036752470 rad이다. L_Wrist_y 유지 목표에만 2.0~2.5초 동안 ±0.005 rad를 선형 ramp로 더한 뒤 5초까지 유지했다. 다른 80개 목표는 모든 1200 step에서 기준과 exact였고, 처음 484개 81관절 명령 전체와 0~2초 native 상태·trace도 exact였다. 처음 달라지는 명령과 native state는 step 485다. 이 2초 공통 구간은 이번 응답을 비교하기 위한 진단 구간이며, 연주에 WAIT→REACH→GRIP→TRANSPORT를 필수 선행 과정으로 추가한 것이 아니다. 주요 66관절의 권한은 환경에 유지되고, 이번 시험에서만 L_Wrist_y 목표를 별도로 바꿔 held했다.

## 저장된 결과

| 조건 | 종료 위치 오차 (mm) | 종료 회전 오차 (°) | 후기 1초 최대 위치 변화 (mm) | 후기 1초 최대 회전 변화 (°) |
|---|---:|---:|---:|---:|
| 기존 기준선 (새 실행 아님) | 13.819696 | 2.918277 | 0.648625 | 0.115306 |
| Wrist_y +0.005 rad | 14.026170 | 2.931572 | 0.797051 | 0.123638 |
| Wrist_y −0.005 rad | 13.634644 | 2.907466 | 0.676770 | 0.124564 |

Minus의 종료 위치·회전 오차는 기준선보다 각각 약 0.185052 mm와 0.010811° 작았지만, 후기 1초 최대 변화는 두 값 모두 더 컸고 늦은 Wrist_y 목표 추종 오차도 기준선보다 커졌다. Plus는 종료 오차와 후기 변화가 모두 더 컸다. 이 작은 한 축 응답에서 위치와 회전의 일관된 동시 개선은 관측되지 않았으며, 큰 각도 또는 전체 Jacobian·feedback gain으로 외삽하지 않는다. [저장 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/series.json:1) 및 [analysis에 저장된 중앙 t=5 6×1 world 응답](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis.json:1)은 XYZ 위치 m/rad `[-0.005091727, 0.060890615, -0.018686056]`, world 회전 로그 rad/rad `[-0.088204570, -0.040931257, -0.109114467]`이다. 이는 ±0.005 rad의 접촉 의존 유한 차분이지 전역 미분 또는 제어기 인증이 아니다.

![저장 native 기준선과 ±Wrist_y 조건의 기타 오차, 실제각·PD 목표, 기준선 대비 위치 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifacts/quiet_wrist_support_response.png)

그림의 기준선은 이전 저장 실행이며 새 native 실행이 아니다. 각 실제각 시계열은 1201 상태 `t=k/240 s`이고 PD 목표는 1200 post-step 샘플 `t=1..1200/240 s`이다. 제어 목표는 60 Hz로 갱신해 그 사이 held 상태로 기록됐다. 오른쪽 아래는 이번 두 조건의 기타 world 위치와 기존 기준선의 차이다.

## 실제 Isaac Gym 장면과 영상

아래 PNG는 각 조건에서 저장한 실제 t=0 및 시뮬레이션 t=5.000초 장면이다. MP4는 151 frame/30 fps이므로 파일 재생 길이는 5.033333초이며, 마지막 시뮬레이션 표본은 5.000초다. 그림과 영상은 스트랩 경로 표시를 포함하지만 스트랩 경로는 천 geometry가 아니다.

### Plus

| 시각 | 손 카메라 | 전신 카메라 |
|---|---|---|
| t=0.000 s | ![plus t0 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/plus/frames/hands/00000.png) | ![plus t0 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/plus/frames/whole_body/00000.png) |
| t=5.000 s | ![plus t5 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/plus/frames/hands/00150.png) | ![plus t5 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/plus/frames/whole_body/00150.png) |

![Plus 실제 스트랩 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/plus/hands.mp4)

![Plus 실제 스트랩 전신 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/plus/whole_body.mp4)

### Minus

| 시각 | 손 카메라 | 전신 카메라 |
|---|---|---|
| t=0.000 s | ![minus t0 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/minus/frames/hands/00000.png) | ![minus t0 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/minus/frames/whole_body/00000.png) |
| t=5.000 s | ![minus t5 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/minus/frames/hands/00150.png) | ![minus t5 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/minus/frames/whole_body/00150.png) |

![Minus 실제 스트랩 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/minus/hands.mp4)

![Minus 실제 스트랩 전신 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/native/minus/whole_body.mp4)


## 보존 및 독립 기록

분석은 1958개 입력 경로의 실행 기록을 보존했으며, analyzer 직접 입력 1952개와 full closure 1957개 사본·전후 SHA·닫힌 로그를 구분했다. 영상 수집 단계도 169개 입력과 168개 선택 사본의 전후 SHA 및 닫힌 로그를 기록했다. 그림 단계는 1959개 입력 해시와 14개 선택 입력 사본을 기록했으며, 선택 사본 수는 전체 원자료 closure 복사 수가 아니다. 기존 영상 158개는 바이트 그대로 보존했고, 네 신규 5초 파일을 추가해 v15 총 162개로 정리했다. 네 영상의 151 frame/30 fps와 5.033333초 재생 길이는 Root가 ffprobe로 다시 확인했다. 상세는 [Root 보존 확인 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/ROOT_VERIFICATION_NOTES.md:1)에 둔다.

## 접촉·한계와 다음 측정

세 기록에서 palm의 양의 raw lambda 접촉은 없었다. LH:index3는 각 1156 step, thumb3는 baseline/plus 587 step 및 minus 655 step에 양의 raw lambda가 기록됐고, R_Hip은 세 기록 모두 1200 step이었다. 이 값들은 solver raw lambda 샘플이지 N 단위의 힘이나 연속 지지·force closure 증명이 아니다. 실제 각도의 모델 제한 초과 최대값은 세 기록 모두 0.000099949539 rad로 같으며, 목표 범위 검사 통과와 실제각의 한계 완전 준수는 구분한다. 저장된 [body9 actual motion 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/body_motion.json:1)은 body9 유지 목표가 held여도 몸통 9관절 가운데 Spine_z의 실제 관절각 변화가 최대 약 0.06176 rad였음을 보여준다. 따라서 고정 root/하체와 PD 목표가 유지된 몸통을 혼동하지 않는다.

이 비교는 자연스러운 연주, source-profile 호환, 전체 손 지지, 폐루프 안정성을 인증하지 않는다. 다음 [L_Wrist_z authority 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_Z_SUPPORT_AUTHORITY_PLAN.md:1)은 다른 한 축의 제한된 응답을 측정할 계획이며 아직 구현되거나 실행되지 않았다. 자세·연주·정책 호환성은 별도 검증 대상이다. [root 보존 확인 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/ROOT_VERIFICATION_NOTES.md:1)을 함께 둔다.
