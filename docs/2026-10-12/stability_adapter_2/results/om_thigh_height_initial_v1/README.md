# OM 기타: 허벅지 바로 위에서 시작하기

사용자 요청대로 초기 기타 높이를 낮췄다. 직전 높이와 양쪽 허벅지에 가까운 두 초기값을 비교했으며, **기존보다107.110mm 낮춘 후보를 다음 초기 높이 진단의 기준으로 추천한다.** 신규 실제 Isaac Gym 실행은2회/총2400physics-step이며 원높이 비교는 이전에 완료한 OFF 실행을 재사용했다. 연주·왼손 철수·반복 재현성은 이번에 시험하지 않았다.

## 초기 모습과 높이 기준

![낮은 후보의 실제 Isaac Gym 초기 측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/native_v1/thigh_gap3mm/media/initial_thigh_side.png)

기타를 허벅지에 가깝게 놓고 기존18°추가 world 전경을 유지했다. 낮아진 기타에 맞춰 양팔 초기각만 IK로 변경했다. 양손 palm의 기타 상대 초기 위치·방향을 보존했고, torso/head/fingers/root/lower 초기값은 그대로다. 몸통을 더 굽히거나 손을 강제 부착하지 않았다.

| 조건 | 직전 초기값에서 world z 하강 | 왼 Hip–바디 source 간격 | 오른 Hip–바디 source 간격 |
|---|---:|---:|---:|
| 원높이(이전 OFF) | 0 | 이번 표에서는 미재측정 | 101.803mm |
| 양Hip 최소8mm | 100.558mm | 8.000mm | 17.139mm |
| 양Hip 최소3mm — 다음 비교 추천 | 107.110mm | 3.000mm | 11.667mm |

간격은 현재 OM63개 convex piece와 인체 capsule의 **최근접 source 거리**다. world 수직 여유 높이나 PhysX cooked clearance와 같지 않다. ‘3mm’ 라벨을 오른 허벅지 위3mm로 읽으면 안 된다. 왼 허벅지가 먼저 가까워지므로 양쪽 최소값으로 결정했다. 오른 허벅지만8/3mm로 맞춘 최초 source2후보는 왼쪽과 겹쳐 거절했으며 search_v1에 보존했다. accepted source_v2는 전체 human–기타/양손/비인접 자기 겹침 검사와 모든 capsule–바디 간격 검사를 함께 통과했다.

추천 초기 guitar actor-root world p는 `[-0.2304154634,0.0917122513,0.6738634109]`m, quaternion xyzw는 `[-0.5,0.5,0.5,0.5]`다. 입력 candidate의 x/y/회전은 직전 OFF와 동일하며 native float32 위치 읽기에는 수십nm 수준 반올림 차이가 있다. 이 좌표는 바디 중심이 아니다. 실제 초기값은 [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/native_v1/thigh_gap3mm/initial_values.json:1)에 있다.

## 실제5초 경과

각 변화는 **각 조건의 자기 초기 actor-root p/q**를 기준으로 계산한다. 회전은 전체 quaternion SO(3) 각도다.

| 조건 | 종료 이동 | 종료 회전 | 최대 이동 | 최대 회전 | 2→5초 이동/회전 |
|---|---:|---:|---:|---:|---:|
| 원높이, 이전 OFF | 114.259mm | 6.512° | 114.259mm | 9.752° | 0.015735mm / 0.002885° |
| 양Hip 최소8mm | 41.009mm | 10.177° | 41.011mm | 10.178° | 0.000128mm / 0.000034° |
| 양Hip 최소3mm | 29.993mm | 7.202° | 29.993mm | 7.334° | 0.008658mm / 0.003372° |

추천 후보는 낮은 두 후보 중 종료/최대 이동·회전이 모두 작았다. 원높이보다 종료 이동은 약74% 감소했고 최대 회전도 작았지만, 종료 회전은6.512→7.202°로 조금 커졌다. world z의 종료 변화는−27.836mm다. 기타가 처음부터 완전히 정지해 유지된 것은 아니며, 초기 작은 이동 후2초 이후 거의 정착한 결과다. formal 허용 영역/연주 성공을 판정하지 않는다.

![추천 낮은 초기값의 실제5초 전신 경과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/native_v1/thigh_gap3mm/media/whole_body.mp4)

![같은 실행의 손 근접 경과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/native_v1/thigh_gap3mm/media/hands.mp4)

300개 제어 전 접촉 표본에서 추천 후보의 `G:body`–L_Hip/R_Hip 양의 raw lambda는292/294표본이었다. Chest/Spine/R_Shoulder/R_Elbow는0이었다. 이번 배치의 실제 받침은 주로 양 허벅지이며 지속 겨드랑이 끼움은 아니다. raw lambda는 N 단위 측정 접촉력으로 해석하지 않는다. 60Hz 표본이 모든240Hz physics-step의 접촉/비접촉을 인증하지 않는다.

추천 후보의 LH:thumb2/3 및 middle3는 바디 이외 기타 부품에 양의 raw lambda283/299/257표본이 있었고 LH:palm는0이었다. 부품 집계는 전용 넥면 판정과 같지 않으며 올바른 압현·지속 palm 지지를 뜻하지 않는다. 강제 손 부착은 없고 손가락 초기각은 직전과 같다.

## 제어·물리·검증

정상 native POSITION PD로81개상체 관절의 초기 목표를 유지했다. PI는 사용하지 않았다. gain/solver·원OMasset·각body질량(총4.648715728kg)/새COMI·root하체고정·내부충돌조건은 이전과같다. 최종301trace목표는각각q_ref와exact였다. 실제원strap은ON,원LA1.10184697196m다. config의strap_enabled:false와actualsceneON을구분한다. 두실행의151개영상시점에서현재계산/직전physics-step commanded장력은0N으로기록됐으며센서힘이아니다. 기타는중력과접촉으로움직이는자유물체다.

- [x] source V1 거절2개와V2통과2개·leaf계획·모든입력/실패를보존했다.
- [x] 독립사전검수와실제5초2회완료,각1200step/300controls/151frame를확인했다. PhysX는CPU physics 설정이고Isaac Gym native 카메라를사용했다.
- [x] body/head/finger/root/lower 초기불변,양팔만변경,기타x/y/q불변,PD/mass동일·모든native입력SHA·propertycache·금지API0·render불변을검증했다.
- [x] [검증 원수치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/verification_v1.json:1), [다음 진단 초기값 선택](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/recommended_initial_v1.json:1)을저장했다.
- [ ] 다음에는이낮은초기높이에서오른쪽전완–바디지지/왼손넥지지를진단한다. 현재겨드랑이지지나양손연주체크포인트성공은미확인이다.

기존실험/원본자산/소비소스는수정하지않았다. 초기너무높았던배치를내려낙하를줄인실험이며여기서안정화학습구조나정책은변경하지않았다.
