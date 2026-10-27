# 새 OM 기타: 가슴·오른쪽 겨드랑이 초기 자세

초기 자세를 만들고 실제 Isaac Gym에서 세 조건을 각각 5초 실행했다. 기타 바디를 가슴·오른쪽 상완 사이에 가까이 두는 배치는 구현했지만, **지속되는 겨드랑이 지지 자세로는 아직 채택하지 않는다.** 종료 이동만 줄인 보정 조건은 회전이 커졌다. 이번 단위는 초기 자세 비교이며 연주 체크포인트·학습·왼손 철수는 실행하지 않았다.

## 초기 자세와 실행 조건

- 현재 OM 기타 형상·질량 조건을 유지한다. root와 하체는 기존 고정 모델이다.
- 기존 자세 대비 Chest의 world 전경을 18° 추가한다. Torso/Spine/Chest의 추가 world 전경 목표는 각각 4.5/11.25/18°다. 이는 누적 body 방향 변화이며 native scalar DOF에 각각 그 각도를 더한 것이 아니다. 실제 몸통 scalar 초기각의 최대 변화는 6.719752°다.
- 기타를 humanoid 앞 방향의 반대로 30mm 옮긴다(현재 world delta 약 `[0,−0.03,0]`m). 기타 초기 높이·회전은 유지한다. 기준 world p는 `[-0.2304154634,0.0917122737,0.7809729576]`m, quaternion xyzw는 `[-0.5,0.5,0.5,0.5]`다.
- 양팔 초기각을 조정해 왼손 손바닥의 기타 상대 초기 위치·방향과 오른손의 근접 준비 배치를 유지한다. 양팔 scalar 초기각 최대 변화는 0.222955rad(12.774°), 오른 손목 위치 변화는 21.216mm다. 손가락 초기각은 유지하고 목·머리는 초기 world 방향을 유지하도록 보정했다. 실제 지속 손 접촉을 보장하지는 않는다.
- 원래 passive strap은 ON, rest length 1.10184697196m를 유지한다. config의 `strap_enabled:false`와 달리 이 native runner의 실제 scene은 ON이며 attempt/초기값/route가 근거다. 기타 고정·강제 손 부착·실행 중 pose 덮어쓰기 없이 native POSITION PD로 제어한다.

![실제 Isaac Gym 초기 측면: 전경 상체와 가까워진 기타](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png)

위 측면은 실제 native 카메라 원본이며 현·스트랩 overlay가 없는 별도 측면 카메라다. 아래 전신 영상에는 스트랩 경로와 여섯 현 시각 overlay가 포함된다. 현은 물리 상호작용을 추가하지 않는다.

## 실제 5초 결과

변화는 각 조건의 자기 초기 guitar actor-root p/q에 대한 값이다. body 중심 이동이나 프렛 정확도와 동일시하지 않는다. 회전은 quaternion의 전체 SO(3) 각도다.

| 조건 | 종료 이동 | 종료 회전 | 최대 이동 | 최대 회전 | 2→5초 이동/회전 |
|---|---:|---:|---:|---:|---:|
| 추가 전경0, 초기 겹침을 줄인 기준 | 113.501mm | 4.395° | 113.505mm | 18.983° | 0.000208mm / 0.000020° |
| 추가 전경18°, 기타 뒤30mm, 보정 OFF | 114.259mm | 6.512° | 114.259mm | 9.752° | 0.015735mm / 0.002885° |
| 같은 초기값, PI+팔 target rate 보정 ON | 65.718mm | 21.416° | 82.446mm | 21.434° | 19.074mm / 16.954° |

기준/OFF는 2초 이후 거의 정지하지만 이미 약11.4cm 이동한 상태다. ON은 종료 이동이 줄어도 2→5초에 회전이 계속 변했다. 따라서 초기 기타 유지가 개선됐다고 종합 판정할 수 없다. 자연스러움 허용 영역의 정식 판정이나 반복 재현성 시험은 이번에 추가하지 않았다.

300개 제어 전 접촉 표본에서 기타 `G:body`와 오른 상완 `R_Shoulder`의 양의 raw lambda는 세 조건 모두0회, Chest는0/1/1회다. ON의 Spine는7회지만 지속되는 상완 지지와는 다르다. raw lambda는 N 단위의 측정 접촉력으로 해석하지 않는다. 접촉 query 표본만으로 모든 physics step의 비접촉이나 clearance를 인증하지 않는다.

OFF 종료 L_Shoulder_x의 초기 목표 대비 actual scalar 오차는 약17.929°, ON은6.687°였다. 목표 추종 일부가 나아져도 기타 회전이 나빠졌다. ON은 PI(Kp1,Ki1/s,몸통 residual±0.05rad/팔±0.3rad)와 팔 목표 변화율1→3rad/s를 함께 바꾼 비교이므로 PI 단독 효과는 분리할 수 없다. gain·solver·질량·초기 상태는 OFF와 동일하다.

ON의 151개 영상 시점에 현재 계산 및 직전 physics step commanded strap 장력은 모두0N이었다. 이는 장력 명령 기록이며 실제 힘 센서 측정값이 아니다. 다른 두 조건에는 같은 장력 시계열이 없으므로 동일한 세 조건 힘 비교로 쓰지 않는다.

![전경18°·기타 뒤30mm, 보정 OFF 실제 5초](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/lean18_back30_whole_body.mp4)

![같은 초기 자세, PI+팔 변화율 보정 ON 실제 5초](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/lean18_back30_hold_pi_whole_body.mp4)

[전신·손 영상6개 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/INDEX.md)을 제공한다. 물리5초/1200step, 영상30fps/151frame/5.033333초다. 환경 종료 뒤 정지 프레임을 늘린 결과가 아니다.

## 초기 값과 구현 위치

[실제 초기 값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v1/lean18_back30/initial_values.json:1)에 81개 관절 이름·q_ref·native 초기 상태·PD·실제 기타 자산·strap 초기 상태가 있다. [설계V4](/home/ajou/yigyu/3/stability_adapter_2/OM_AXILLA_INITIAL_POSE_PLAN_V4.md:1), [탐색 구현](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v4.py:1), [목표 보정 구현](/home/ajou/yigyu/3/stability_adapter_2/run_om_axilla_hold_correction_v1.py:18)을 새 파일로 보존했다. 기존 OM 자산·이전 결과·실행에 사용된 계획/소스는 수정하지 않았다.

정적 source capsule–convex 계산은 초기 Chest 간격3.216mm, 오른 상완 전체2.977mm/근위 부분2.988mm이며 source 겹침 검사를 통과했다. 이는 PhysX cooked clearance 인증이 아니다. 근위 지점은 capsule segment0..0.55 부분집합이며 물리 형상을 잘라 바꾼 것이 아니다. 소스 거리의 단위·검사 범위 및 초기 거절 후보는 search_v1..v4에 모두 보존한다.

## 검증과 다음 단위

- [x] source 탐색·독립 수치 검사·사전 검토 후 native3회/총3600step를 완료했다.
- [x] OFF/ON 초기 JSON 전체 exact, PD·mass·source audit 동일, 실행 입력핀 불변, 금지API0을 확인했다.
- [x] PI300개 제어 로그의 공식·잔차 한계·실제 제출 목표를 다음 trace 행과 exact 대조했다. 머리·손가락 residual0, 실제 최종 target은 모델 한계/변화율 제한을 통과한다.
- [x] 영상151frame와 native render 상태 불변151표본씩, 원본/보관6MP4 exact를 확인했다.
- [ ] 오른 상완·가슴 지속 지지와 연주 준비 안정성은 미달이다. 다음 단위는 오른쪽 전완의 바디 앞쪽 지지 위치와 가슴 지지의 조합, 관절 목표 추종 및 기타 회전 모멘트를 함께 진단한다. 현재 자세에서 허리 굽힘만 더 늘리지 않는다.

[분석 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/verification_v1.json:1)에 직접 원자료 수치와 검증 범위를 기록했다. HOLD leaf 계획 Markdown은 실행 attempt에 경로만 기록돼 사전 SHA 증거가 없다. 실행 controller Python/config는 사전 입력핀에 포함됐으며 현재 계획 파일 SHA는 실행 후 검증한 것임을 구분한다. 이 기록 보완을 위해 같은 물리 시험을 다시 실행하지 않았다.
