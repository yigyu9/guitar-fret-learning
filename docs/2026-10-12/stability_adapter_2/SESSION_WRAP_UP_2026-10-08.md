# StabilityAdapter 2 세션 정리 — 2026-10-08

## 지금까지 확인한 범위

이번 세션의 실험과 분석은 여기서 일시 정리한다. Root가 확인한 시점에 `-m stability_adapter_2`를 실행 중인 프로세스는 없었다. 사용자가 재개를 요청하기 전에는 방향을 논의하거나 선정하더라도 새 trial을 실행하지 않는다. 이 문서는 다음 단계 결정을 돕는 요약이다.

지금까지 확인한 조건은 다섯 가지다. Original baseline은 기존 quiet 조건에서 저장한 자료이고 이번 새 trial이 아니다. WristY−, WristZ+, current Y/Z feedback ON은 스트랩 힘을 켠 채 비교한 작은 보정 조건이며, no-strap OFF는 힘과 strap overlay를 끈 별도 진단이다. 비교는 같은 quiet 5초 동작 구간에 한정된다.

| 조건 | 5초 종료 위치 오차 (mm) | 5초 종료 회전 오차 (°) | 후기 완전 1초 최대 위치 변화 (mm) | 후기 완전 1초 최대 회전 변화 (°) |
|---|---:|---:|---:|---:|
| Original saved baseline | 13.820 | 2.9183 | 0.649 | 0.1153 |
| WristY− | 13.635 | 2.9075 | 0.677 | 0.1246 |
| WristZ+ | 13.818 | 2.8957 | 0.572 | 0.1047 |
| Current Y/Z feedback ON | 13.665 | 2.8893 | 0.694 | 0.1245 |
| No-strap OFF | 20.526 | 12.1452 | 0.336 | 0.0647 |

표의 각 수치는 해당 저장 분석 `summary`에서 읽었다. 위치오차, 회전오차, 후기 변동 중 어느 지표를 우선하는지에 따라 유리한 조건이 달라 한 가지 “최고 조건”을 고를 근거는 없다. WristY−는 스트랩 조건에서 종료 위치오차가 가장 작고, feedback ON은 종료 회전오차가 가장 작으며, WristZ+는 스트랩 조건에서 후기 변화가 가장 작다. No-strap OFF는 후기 변동만 작지만 초기에서 종료까지 기타 회전오차가 약 12.145°다. 후기 창의 정숙함만으로 초기 자세 유지에 성공했다고 해석할 수 없다.

원 baseline과 WristY− 분석은 [quiet wrist support 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/README.md:1), WristZ+ 분석은 [quiet wrist Z 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/README.md:1), feedback ON 결과는 [Y/Z feedback 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/README.md:1), no-strap 결과는 [no-strap 현재 자세 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/README.md:1)에 있다. 각 수치의 분석 원본은 각각 [Y 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis.json:1), [Z 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/analysis.json:1), [feedback 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/analysis.json:1), [no-strap 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/analysis.json:1)에서 확인할 수 있다.

## 공통 조건과 해석 범위

스트랩을 사용한 비교는 absolute strap rest length `1.1018469719600776 m`, root와 하체 고정, 자유 기타, 몸통 9관절 held PD 목표, Thorax부터 손가락까지 66관절 제어가 가능한 환경을 유지했다. 시작 뒤 pose를 덮어쓰거나 기타를 고정하거나 손을 강제로 붙이지 않았다. Body9 목표를 held한 사실은 실제 몸통 좌표가 고정됐다는 뜻이 아니다. 기록된 `Spine_z` 단일 관절좌표 변화는 약 `0.06176 rad`였으며 세계 몸통 회전량이 아니다.

Current feedback ON은 2초 공통 구간 뒤 기타의 현재 world 위치/회전 오차를 이용해 Y/Z 손목 목표를 60 Hz로 조정했다. 보정 범위는 축별 ±0.005 rad, rate 제한은 0.002 rad/s였다. 5초 종료 위치·회전오차는 baseline보다 조금 줄었지만 후기 1초 변화는 조금 커졌다. 최대 초기 위치오차는 baseline과 같은 `14.608483313 mm`다. 이 결과는 해당 quiet 조건에서만 확인된 작은 변화다.

No-strap OFF에서는 strap force와 표시 overlay를 껐다. 비활성 진단값으로 LA가 기록되어 있어도 실제 strap force가 작용했다는 의미는 아니다. 후기 변화는 작았지만 초기보다 기타 회전이 약 12.145° 달라졌다. 힘 OFF의 안정된 후기 구간을 초기 자세 유지나 strap-on 조건의 대체로 볼 수 없다.

스트랩을 쓴 손 지지 비교에서는 Palm 양의 raw lambda 접촉이 관측되지 않았지만 index/thumb 접촉 기록은 있다. Raw lambda는 뉴턴 단위의 지지력이나 force closure 증명이 아니다. 실제 관절 한계 초과는 여러 strap 조건에서 약 `0.0001 rad` 관측됐다. Source-shape 검사 통과는 PhysX cooked 형상의 동적 침투가 없다는 인증이 아니다. 이번 비교는 각 5초 quiet 동작이며 fret/strike actor 목표 전환, 학습, 자연스러움 또는 정책 호환성 검증을 포함하지 않는다. 해당 구간의 actor inference와 training update는 0이다.

## 실제 화면과 영상

현재 feedback ON의 저장 series를 그린 그림은 실제 화면 렌더가 아닌 과학 도표다. 네 패널은 초기 world 위치·회전 오차, feedback 보정 delta, baseline 대비 기타 위치거리를 표시한다.

![Current feedback ON 실제 저장 series 기반 과학 도표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/artifacts/quiet_wrist_yz_feedback_response.png)

아래 이미지는 current feedback ON의 실제 Isaac Gym native `t=5.000 s` 손 camera frame이다.

![Current feedback ON, t=5.000 s 실제 손 camera frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/frames/hands/00150.png)

Current feedback ON hands/whole-body와 no-strap force/overlay OFF hands/whole-body는 아래의 실제 native MP4다. 각 영상은 151 frame/30 fps(재생 5.033333초)이며 마지막 simulation 표본은 5.000초다. 과학 도표는 실제 Gym 장면 렌더가 아니다.

![Current feedback ON 실제 hands-camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/quiet_wrist_yz_feedback_v1__native__on__hands.mp4)

![Current feedback ON 실제 whole-body-camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/quiet_wrist_yz_feedback_v1__native__on__whole_body.mp4)

![No-strap force/overlay OFF 실제 hands-camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/hands.mp4)

![No-strap force/overlay OFF 실제 whole-body-camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/whole_body.mp4) 전체 기존 영상은 [VIDEO_INDEX_v17, 총170개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v17.md:1)에 정리되어 있다.

기록별 보존 확인은 current feedback ON [25 checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/final_verification.json:1)과 [1618-file inventory](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/artifact_inventory.json:1), WristZ [27 checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/final_verification.json:1)과 [3676-file inventory](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/artifact_inventory.json:1), no-strap [24 checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/final_verification.json:1)과 [566-file inventory](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/artifact_inventory.json:1)에 있다. WristY 결과는 [42개 분석 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis.json:1)로 기록되어 있다.

원 video collection wrapper는 최종 metadata 작성 인자 오류로 exit 1을 남겼지만 네 MP4와 index는 생성되어 보존됐다. 별도 read-only recovery는 9개 검사를 통과했다. Collector의 실제 exit status와 wall time은 저장되지 않아 null이며, 이 사건은 simulation 실패가 아니다. 세부는 [feedback 결과의 collection 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/README.md:1)에 정리되어 있다.

## 추후 재개를 위한 제안

미세한 quiet 자세 오차를 더 최적화하는 자동 반복을 곧바로 재개하기보다, 먼저 실제 영상을 함께 검토해 허용할 자세와 손의 연주 공간을 정하는 것이 낫다. 그 다음 fret/strike checkpoint의 목표, 관측값, history, 현재 hold 목표 사이를 어떻게 연결할지 설계하고, 짧은 새 5초 연주 목표 전환을 OFF/ON으로 비교한다. 그 결과 잔차가 남을 때 residual learning을 검토할 수 있다. 사용자가 정의한 성공 수치나 자연스러움 범위가 아직 없으므로 새 기준을 임의로 정하지 않는다.

별도 대안으로 [startup slow/fast feedback 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_STARTUP_FEEDBACK_PLAN.md:1)이 있다. 아직 구현·실행하지 않은 계획이며, 선택되기 전 자동으로 진행하지 않는다. 현재 Y/Z quiet feedback의 유지구간 결과가 startup이나 연주 목표에도 유효하다는 증거는 없다.
