# 스트랩 없는 오른쪽 상완 지지 — 5초 유지 후보

**왼팔·왼손을 기타에서 떼고 스트랩을 실제로 끈 상태에서, 오른쪽 상완·가슴·오른 허벅지 접촉으로 기타를 유지하는 후보를 구현했다.** 같은 초기 조건의5초 Isaac Gym/PhysX 실행2회가 초기 상태·전체 trace·전신/손 영상 SHA까지 동일했다. 초기 정착 변화는 남으며 연주 중 강건성은 아직 검증하지 않았다.

| 최종 후보 측정 | 첫 실행·동일 조건 재실행 |
|---|---:|
| 초기 대비 바디 실제 source 형상 bounding-box 중심 이동 | 40.207mm |
| 초기 대비 actor-root 이동 | 53.017mm |
| 초기 대비 SO(3) 전체 회전 | 11.071° |
| 2→5초 바디 중심 추가 이동 | 0.073932mm |
| 2→5초 추가 회전 | 0.028843° |
| 오른쪽 상완–바디 접촉 관측 | 1187/1200 physics 끝점 |
| 그중 양의 raw lambda 관측 | 1181/1200 끝점 |
| 왼팔·왼손 / Head–기타 접촉 관측 | 각각0/1200 |
| 물리 진행 / 명령 / 영상 | 1200step·300control·151frame·5.033333초 |

body 중심은 OM63 collision hull 전체의 bounding-box 중심이며 질량중심이나 actor-root가 아니다. raw lambda 양수와 접촉 관측 횟수는 접촉력(N) 또는 지지 비중을 뜻하지 않는다. 60Hz 저장 query(step4..1196)에는 R_Shoulder·Chest·R_Hip 접촉이 관측되고 오른 손가락 접촉은 관측되지 않았다. 이 query만으로 매 physics step의 오른 손가락 무접촉을 인증하지 않는다.

## 초기 배치와 제어

기본 배치는 [V10](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V10.md:1)의 몸통 전경·허벅지 근처 기타와 떨어진 왼팔이다. 초기 상완 미세 간격 V14와 달리 현재 [V17](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V17.md:1)은 오른팔을 바꾸어 바디의 넥 쪽 위테두리에 접근한다. 초기 source full 상완 간격은0.088443mm, 접점G y=−0.230890m다. 이 값은 cooked/native 관통 깊이 또는 초기 무관통 인증이 아니다. 실제 모델의 R_Shoulder는 상완 캡슐이며 관절 중심점 자체를 뜻하지 않는다.

root/하체를 고정하고 기타는 자유 상태로 두었다. 현재 기타를 기준으로 오른팔12 EFFORT 관절만 유한 토크를 적용한다. source 상완 motor reference의 희망점은 기타 표면 안쪽8mm이며 stiffness3000N/m·상대 velocity damping80Ns/m·point-force 요청 norm cap40N이다. 실제 관절 effort는 원 native cap 안으로 제한하고 human gravity/posture 항을 더한다. 희망점/40N은 관절 제어 계산용이며 실제 물리 관통/측정 접촉력은 아니다. 다른69관절은 초기 목표 POSITION PD를 유지한다.

스트랩 OFF·strap force 호출0·기타에 직접 힘/토크0·checkpoint/policy 호출0이며 기타 attachment/런타임 pose 덮어쓰기를 하지 않는다. 생성 때 모델/상태/모드 설정을 마친 뒤, 위치 목표 제출은 상태를 바꾸지 않았고 POSITION69 exact readback300회·제어 owner/finite/cap·property/cache guard를 통과했다. 오른 EFFORT12의 POSITION getter는 actuator 명령으로 해석하지 않는다. 현재 상완 reference의 Jacobian×전체qdot 대응 최대 오차0.000836m/s는 이 점의 검증이며 전체 Jacobian/인체 중력 보정/접촉력을 인증하지 않는다.

초기 다른69각·기타 p/q는V14와 같고 오른팔 최대 초기 보정1.200000018rad(약68.755°)를 사용했다. R_Wrist_y 초기 모델 한계 여유0.000121593rad로 매우 작다. 몸통/머리 목표는 고정했지만 실제 DOF scalar 초기 대비 최대 변화는 몸통5.739°, 목·머리3.207°, 오른팔9.020°였다. 이는 body world/relative Euler 회전이 아니다. 오른팔 자세의 자연스러움과 strike 자유도는 별도로 개선·검증해야 한다.

## 영상과 초기 값

![초기 Isaac Gym 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side/media/initial_strings.png)

![처음부터5초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side/media/whole_body.mp4)

![손 근접 전체 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side/media/hands.mp4)

[후보 관절각·기타 p/q](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/search_v9/upper_arm_neck_side/candidate.json:1), [native 실제 초기값·PD·질량](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side/initial_values.json:1), [실행 config](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/search_v9/upper_arm_neck_side/config.json:1), [동일 조건 재현 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/support_candidate_comparison_v1.json:1).

## 이전 진단과 실패를 보존

| 완료 실행 | 종료 actor-root 이동 / 전체 회전 | 결과 |
|---|---:|---|
| native1 왼손 떨어뜨림 첫 배치 | 35.254mm /10.009° | 실제 왼손목 지지 발생, 목표 미달 |
| native2 왼손 높이 추가 | 28.130mm /6.486° | 실제 왼팔꿈치 지지 발생, 목표 미달 |
| native3 왼팔 뒤로·상완1mm | 489.943mm /99.562° | 왼팔0·상완0, 넘어짐 |
| native4 상완 preload/PI | 462.393mm /130.639° | 상완 접촉0 |
| native5 오른팔 PD 추가 | 462.505mm /106.208° | 상완 접촉0 |
| native6 현재 기타 point IK/PI | 477.357mm /108.661° | 상완 접촉0 |
| native7 몸통 전경/가슴 접근 | 306.010mm /50.005° | 상완0·Head 접촉, 잘못된 정착 |
| native9 human right EFFORT | 302.707mm /49.459° | 팔 제어 개선, 상완0·Head 접촉 |
| native10 미세 간격/상대 EFFORT | 432.659mm /120.114° | 상완53/1200이지만 넘어짐 |
| native11·12 넥 쪽 상완 | 53.017mm /11.071° | 왼팔/Head0,5초 유지 후보 동일 재현 |

native8은 첫 step의 기존 혼합 POSITION/EFFORT readback 또는 state-preservation 합성 assertion으로 물리0step 종료했다. 두 조건 중 어느 것이 원래 실패 원인인지 그 기록만으로 분리하지 않는다. 이후 right EFFORT getter와POSITION69/state 검증을 구분하여 실행했다. native8의1frame 약0.034초 파일은 정상5초 영상이 아니다. v6 후처리의 문자열Path 오류 역시 보존하고 새v7 이후 분석으로 보완했다. sourceV15 앞면 후보는 상완겹침21.807mm로, V16은 넥쪽 접점 미달로 거절했고 추가native는 하지 않았다.

전체 이번 phase 완료 native11회·13200physics step, 첫-step 실패1회(0step), material 읽기 검사1회(0step)다. 모델/원질량·기존 자산은 유지했다. imported/native actor friction 속성1.0은 material 읽기 확인이며 실제 solver effective coefficient나접촉력 인증이 아니다. 원 tiny visual marker6개 로딩 경고도 로그에 보존했다.

[실패 영상 모음1](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v1/README.md:1), [실패 영상 모음2](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/README.md:1), [구현 변경 경로·줄 번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/CHANGED_FILES.md:1).

## 다음 검증

이 후보는 같은 초기 조건에서5초 동안 넘어가지 않는 정지 지지 기준이다. 초기 정착40mm/11°를 줄이고 오른팔·손목의 자연스러운 strike 준비 자세를 확보한 뒤, 작은 오른팔 운동을 주어 상완/가슴/허벅지 지지 유지와 현재 기타 기준 fret·strike 수행을 별도 검증한다. 지금은 두 정책을 연결하거나 학습된 연주 성공을 선언하지 않는다. 초기 관통·runtime cooked 관통 깊이의 정식 인증도 별도다.

[초기·시간별 이미지 설명(footer 보완본)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v2/README_v2.md:1), [최종 후보 영상 모음](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/README.md:1).
