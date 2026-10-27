# Quiet L_Wrist_z 목표 변화 — 두 실제 5초 응답과 Y/Z 저장 비교

## 실행 범위와 보존 조건

이번 phase의 새 물리 실행은 plus와 minus 각 한 번의 초기화, 각 1200 physics step(5.000초), 151 frame이다. 둘 다 CPU Isaac Gym trial을 완료했고 기록된 제약 위반은 0건이며 actor 추론과 학습 갱신은 0회다. 분석 `analysis.json`의 42개 검사와 별도 `body_motion.json`의 7개 검사가 모두 통과했다. baseline은 기존 저장 native자료로, 이번에 다시 초기화한 세 번째 조건이 아니다. 분석 집계는 새 초기화 2회/2400 step이다.

기준 quiet 초기자세, 초기 81관절 목표, 고정 root와 하체, 자유 기타, 공용 기타 world 목표, 절대 strap rest length 1.1018469719600776 m, body9의 KP×2·KD×√2, 손가락 목표와 기존 `L_Wrist_x` 1 Hz·±0.005 rad 진동을 유지했다. 시작 `L_Wrist_z` actual은 −0.2735629 rad, held PD target은 −0.4212334 rad다. `L_Wrist_z`에만 2.0~2.5초 동안 ±0.005 rad ramp를 적용하고 5초까지 held했다. Y축 목표는 추가 보정하지 않았다. 각 조건에서 fresh 15-gate가 실행되었다.

기준, plus, minus는 20개 공통 초기 필드가 같고 0~2초 상태 trace, 나머지 80관절의 1200개 목표, 첫 484개 전체 81관절 명령이 exact하게 일치한다. 첫 native 상태 분기는 step 485다. 공통 2초는 응답을 분리해 비교하기 위한 진단 구간이다. 이 실험은 연주 전제에 WAIT→REACH→GRIP→TRANSPORT 단계를 추가하지 않으며, 66관절 제어 권한도 환경에 유지된다.

## 기타 응답

| 조건 | 종료 위치 오차 (mm) | 종료 회전 오차 (°) | 후기 완전 1초 최대 위치 변화 (mm) | 후기 완전 1초 최대 회전 변화 (°) |
|---|---:|---:|---:|---:|
| 기존 저장 baseline (새 실행 아님) | 13.819696 | 2.918277 | 0.648625 | 0.115306 |
| L_Wrist_z +0.005 rad | 13.817638 | 2.895722 | 0.572182 | 0.104704 |
| L_Wrist_z −0.005 rad | 13.829543 | 2.946758 | 1.056584 | 0.171364 |

Plus는 기준 대비 종료 위치 오차가 0.002058 mm 줄었고 회전·후기 변화도 조금 낮았다. 위치 차이는 극히 작다. Minus는 종료 위치·회전 오차와 후기 변화가 모두 커졌다. 이를 성공 gate로 과장하지 않으며 미세한 진동만으로 실패를 판정하지 않는다. 분석의 ±0.005 rad 중앙차분 `L_Wrist_z` 응답은 world XYZ 위치 `[0.041140616, −0.051216781, 0.054055452] m/rad`, world 회전 로그 `[0.174925026, 0.135365343, −0.004841464] rad/rad`다. 접촉 상태에 의존한 이 국소 응답은 전역 Jacobian이나 제어기 이득 인증이 아니다.

![저장 baseline과 두 신규 trial의 기타 초기 world 위치·회전 오차, L_Wrist_z actual 및 post-step PD target, baseline 대비 기타 world 위치 거리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/artifacts/quiet_wrist_z_support_response.png)

도표는 실제 저장 series를 사용한다. 위치 오차는 초기 world 목표 대비 mm, 회전 오차는 초기 방향 대비 도(deg), 손목 패널은 `L_Wrist_z` actual rad와 post-step PD target rad, 우하단은 plus/minus 기타 world 위치와 저장 baseline의 거리 mm다. Actual은 1201 state `t=k/240 s`, 목표는 1200 post-step 표본 `t=1..1200/240 s`이며 command는 60 Hz held 제어다. 그림은 과학 도표이지 Isaac Gym 렌더가 아니다.

## 실제 장면과 5초 영상

아래 t0/t5 frame과 영상은 각 native trial에서 직접 저장된 실제 장면이다. PNG는 strap route 시각 표시를 포함하고, strap route는 천 mesh가 아니다. 영상은 각 151 frame/30 fps, 재생 길이 5.033333초이며 마지막 물리 표본은 5.000초다. 초기값, 실행 report, capture 및 videos 메타데이터 링크도 조건별로 함께 둔다.

### Plus

- [초기값·실제 초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/initial_values.json:1), [실행 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/report.json:1), [capture 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/capture.json:1), [영상 metadata/ffprobe](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/videos.json:1)

| 시각 | 손 카메라 | 전신 카메라 |
|---|---|---|
| t=0.000 s | ![plus 시작 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/frames/hands/00000.png) | ![plus 시작 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/frames/whole_body/00000.png) |
| t=5.000 s | ![plus 종료 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/frames/hands/00150.png) | ![plus 종료 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/frames/whole_body/00150.png) |

![Plus 실제 strap 표시 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/hands.mp4)

![Plus 실제 strap 표시 전신 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/whole_body.mp4)

### Minus

- [초기값·실제 초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/initial_values.json:1), [실행 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/report.json:1), [capture 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/capture.json:1), [영상 metadata/ffprobe](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/videos.json:1)

| 시각 | 손 카메라 | 전신 카메라 |
|---|---|---|
| t=0.000 s | ![minus 시작 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/frames/hands/00000.png) | ![minus 시작 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/frames/whole_body/00000.png) |
| t=5.000 s | ![minus 종료 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/frames/hands/00150.png) | ![minus 종료 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/frames/whole_body/00150.png) |

![Minus 실제 strap 표시 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/hands.mp4)

![Minus 실제 strap 표시 전신 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/whole_body.mp4)

영상 파일은 [v16 영상 모음(166개)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v16.md:1)에도 등록되어 있다.

## 접촉·몸통 관측과 한계

세 기록에서 `LH:index3` 양의 raw lambda는 각각 1156 step, thumb3는 baseline/plus/minus 각각 587/597/547 step이며 `R_Hip`은 각 1200 step이다. Palm 양의 raw lambda 접촉은 0이다. Raw lambda는 힘(N), 연속 지지 또는 force closure 증명이 아니다. 실제각 최대 native 제한 초과는 모든 기록에서 0.000099949539 rad다. 몸통 9관절의 PD 목표는 held됐지만 `Spine_z` 실제 관절각 변화 최대는 baseline/plus/minus 각각 0.061757788/0.061759546/0.061762825 rad(약 3.54°)였다. 이는 몸통의 세계 SO(3) 회전각이 아니다. 세 조건 모두 기타 constraint violation은 없었다.

## Y/Z 저장 응답의 비교와 다음 단계

기존 v1 비교 helper는 Y inventory 안에 baseline도 있어야 한다고 잘못 가정해 계산 전에 `KeyError`로 종료했다. 실행 소스 사본, 사전 invocation, 입력 전후 SHA 기록과 failure 기록은 보존됐다. 이 경로에서 물리 실행이나 분석 rerun은 없었고, `comparison.json`도 생성되지 않았다. v2는 Y와 baseline 각각의 inventory를 정확히 확인하고 저장된 Y/Z 응답만 계산했다. [v2 비교 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_v2.json:1)의 6개 검사는 모두 통과했다.

6×2 world 응답 행은 XYZ 위치 m/rad와 world rotation log rad/rad이며 열은 `L_Wrist_y`, `L_Wrist_z`다. 비교 scale 0.03 m와 5°에서 rank 2, scaled column cosine −0.728127296, condition number 2.719646212를 얻었다. 이 두 열은 관측된 local 응답의 수학적 비교이지 전체 순간 Jacobian이나 feedback 안정성 증명이 아니다. 제한 least-squares 후보 `δY=−0.005`, `δZ=+0.005 rad`의 예측 종료 오차 13.635786789 mm/2.882135324°는 두 축을 함께 바꾼 native trial에서 측정한 결과가 아니다. 모델 출력으로만 기록한다.

다음 계획은 현재 기타 world 위치/회전 오차에서 60 Hz gradient 적분으로 Y/Z 목표 delta를 구하고 각도를 ±0.005 rad, 속도를 0.002 rad/s로 제한한다. κ=0.00242502989755426 rad²/s는 baseline `t2g_ref`에서 고정한다. OFF/ON 두 개의 새 5초 trial은 아직 구현·실행되지 않았다. 자연 연주, policy 호환성, 폐루프 안정성은 검증되지 않았다.

## 자료와 재현 기록

- [시계열 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/series.json:1), [저장 분석 42 checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/analysis.json:1), [body9 별도 진단 7 checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/body_motion.json:1)
- [기존 quiet baseline 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/initial_values.json:1), [Y축 저장 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis.json:1)
- [v1 실패와 입력 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_failure.json:1), [v2 계산 invocation](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_v2_invocation.json:1), [Root 확인 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/ROOT_VERIFICATION_NOTES.md:1)
- 분석은 1958 입력 경로/1957 full-closure 사본(직접 입력 1952), 영상 수집은 173 입력/172 선택 사본, 그림은 1959 입력/14 선택 사본을 보존했다. 선택 사본을 full closure로 혼동하지 않는다. 각 단계의 닫힌 로그·전후 SHA는 결과 폴더에 보존되어 있다.
