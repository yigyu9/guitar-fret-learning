# StabilityAdapter 2 메인 계획: 허용 범위 안에서 자유 기타 연주

정리일: 2026-10-10. 최신 사용자 결정·봉인 결과와 다음 작업을 기준으로 정리했다.
구현·설정·메인 설계는 `stability_adapter_2/`, 결과·로그·이미지·영상은 `docs/2026-10-12/stability_adapter_2/`에 저장한다.

전체 목표·우선순위·단계별 통과 조건은 [전체 연구 메인 계획](/home/ajou/yigyu/3/master_plan/README.md:14)을 따른다. 2026-10-10 사용자 승인으로 형상·물리 점검 → 자유 기타 단일 동작 → 제한된 안정화 학습 → 양손·곡 통합의 방향을 반영했다. 이 파일은 StabilityAdapter 2 실행 계획이며, 아래 과거 실험 기록은 당시 조건을 보존한다. 최신 실행 우선순위는 마지막의 「전체 연구 방향 반영」 절을 따른다.

## 1. 목표와 현재 상태

**humanoid 초기 자세로 자유 기타의 시작 흔들림을 줄이고, 사용자 허용 범위 안에서 fret·strike 연주를 수행하며 범위 이탈을 관절 제어로 보정한다.** 범위 안에서는 특정 초기 p/q로 정확히 복귀할 필요가 없고 작은 흔들림은 허용한다. WAIT → REACH → GRIP → TRANSPORT나 정지 대기를 필수 선행 과정으로 두지 않는다.

| 항목 | 현재 확인된 상태 |
|---|---|
| 환경·도구 | root/하체 고정·자유 기타·내부 충돌 환경, 초기 배치 진단, 정적 자세 조작, 실제 5초 녹화 구현 |
| 과거 안정화 | 일부 기존 자세에서 후기 변화가 작아지는 결과와 제한된 손목 보정 응답 관측. 실제 연주 성공으로 판정하지 않음 |
| 새 초기 후보 | 무스트랩·수평 넥·앞판 정면·오른손 비접촉의 실제 초기 배치와5초 비교 완료. 팔24 PI가 흔들림을 줄였으나 손바닥·검지·중지 실접촉 유지와 연주는 미완료 |
| 연주 연결·학습 | 2초 준비 후 frozen Strike/Fret 개별 native 연결과 원본 첫 done까지 녹화 완료. Strike 적시 타현1회 후 잘못된 타현으로 실패, Fret 압현0%·finger_back 실패. 양손 통합·전체 허용 범위 인증·보정 학습은 미완료 |
| 스트랩 비교 | 같은 시작·제어 조건에서 기존 고정 길이 ON/OFF 비교 완료. PLAY 계산 장력0N·압현0%로 지속 지지/연주 개선 미확인. 한 길이 결과를 스트랩 일반에 확대하지 않음 |

상세 기준은 [허용 범위·연주 계약](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:1)을 따른다.

## 2. 공용 모델과 fret·strike의 핵심 차이

| 항목 | 기존 fret·strike | 새 자유 기타 환경 |
|---|---|---|
| 기타 | 고정 root·중력 비활성 | 자유 root·중력·접촉. 무스트랩 기준과 기존 고정 길이 스트랩 ON 비교를 별도 시험 |
| 초기 자세 | 공용 좌식 자세, task별 손 자세·reset 처리 | 기타 후보에 맞춰 양팔·손 초기각을 선정 |
| 연주 action | fret 왼팔/손 30개, strike 오른팔/손 30개 | source 60개와 Thorax 6개를 이름 기준으로 연결 |
| 물리·관측 계약 | task별 PD·limit·후처리·history | 실제 자유 기타 환경과 차이를 검증한 뒤 연결 |

공용 모델의 질량·관성·관절 한계를 임의로 바꾸지 않는다. `G:pluck_range` 같은 연주 판정 영역을 가짜 지지면으로 사용하지 않는다. 고정 기타에서의 성능은 자유 기타 지지 성능과 구별하며, 기존 환경·체크포인트·공용 자산은 보존한다.

## 3. 환경 조건과 제어권

| 그룹 | 조건 |
|---|---|
| humanoid root·하체 | 완전 고정. 별도 fixed-lower 자산을 사용 |
| Torso·Spine·Chest 9관절 | 기준 PD 목표 유지, 움직임은 최소화. 실제 움직임은 측정 |
| 양쪽 Thorax부터 손가락까지 66관절 | 주요 제어 범위. 기존 한쪽 33관절 제한을 승계하지 않음 |
| Neck·Head | 현재 유지 목표 사용 |
| humanoid 내부 충돌 | 양손 및 비인접 팔–몸통 충돌 활성. 기존 연결부/importer 제외 조건 기록 |
| 기타 | 자유 물리 상태. 고정·강제 손 부착·지속 pose 덮어쓰기·목표로 끄는 인위적 힘 금지 |

몸통의 작은 목표 보정은 첫 배치·연주 검토 후 별도 설계한다. 66관절의 사용 권한과 학습 action 차원은 구별하고, 제어권·보정 제한을 정한 뒤 학습 구조를 결정한다.

## 4. 기타 허용 범위와 초기 배치

위치 기준은 **world 기타 actor-root**다. 바디 중심이나 기타 전체 형상의 경계로 바꾸어 해석하지 않는다.

| 항목 | 사용자 지정 범위 |
|---|---|
| 위치 X / Y | X [-0.50, -0.15] m / Y [-0.15, 0.15] m |
| 위치 Z | [0.65, z_chest] m. 초기 Chest 원점 높이 근사이며 기존 기록 약 0.883738 m, 환경 초기화 때 재확인 |
| 회전 | extrinsic Euler xyz X [45, 90]°, Y [50, 100]°, Z [135, 180]°가 만드는 회전 집합 |

회전 포함 판정은 허용 회전 집합에 대한 quaternion 동치·최단 회전 거리로 설계한다. Euler 특이점 때문에 단일 `as_euler()` 결과를 축별 비교하는 방식은 사용하지 않는다. 과거 30 mm/5° 임시 기준이나 넥 ±10° 비교 표본으로 범위를 축소하지 않는다.

우선 후보는 **넥 수평·줄이 있는 앞판 정면**이다. [저장된 실제 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/pose.json)의 q xyzw [-0.5, 0.5, 0.5, 0.5]는 범위 안의 xyz [67.5, 90, 157.5]°와 같은 회전이다. 새 실험 후보는 기타 root를 기존 후보보다25mm 올리고 양팔·손을 재배치했다. 실제 native 초기각·FK·손바닥 위쪽·수평/정면을 확인했고, 원본 형상 기준 기타–인체/비인접 손 교차0과 오른손 보수적 간격52mm를 확인했다. 이는 cooked PhysX 관통 인증이 아니다. 별도 실행 입력으로 보존하며 환경 기본값으로 자동 채택하지 않았다. [초기 설정과5초 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/README.md:1)를 따른다.

## 5. 최소 자세·지지 제약

- 환경 시작 시 기타–humanoid 및 비인접 인체 부위의 관통을 감지한다. CPU source 형상 검사와 실제 PhysX 초기 검사·접촉을 구별한다.
- 왼손 손바닥은 world +Z 위쪽 반구를 필수로 하고 +Z에 가까운 방향을 부드럽게 선호한다.
- 기울어진 넥 전체와 손 높이를 비교하지 않고, 손이 지지하는 **해당 넥 영역**의 상대 위치·면 방향을 평가한다. 손바닥과 지지면의 가까운 평행은 선호 조건이다.
- 최신 초기 배치는 손바닥 넥 아래면·엄지 뒷면·나머지 네 손가락 전면 접촉을 목표로 한다. 오른손은 기타와 비접촉 배치한다. 연주 중에는 운지에 따라 손가락 개폐를 허용하며 모든 손가락의 지속 접촉을 강제하지 않는다.
- 모델 관절 한계를 준수하고 2026-08-19 손가락 분포는 부드러운 자세 선호에 사용한다. 자료가 없는 어깨·팔꿈치·손목의 정상 분포를 임의로 만들지 않는다.
- 왼손 운지와 오른손 타현 공간, 손가락 개폐와 관절 여유를 확보한다. 기타를 유지해도 연주를 막는 배치는 채택하지 않는다.

세부 근거는 [자세 제약](/home/ajou/yigyu/3/stability_adapter_2/POSTURE_CONSTRAINTS.md:1)을 따르되 최신 사용자 조건을 우선한다.

## 6. 무스트랩 초기 조건과 이후 스트랩 비교

2026-10-09 무스트랩 초기 배치에서는 **스트랩 힘·표시 모두 OFF**로 했다. 길이 조절로 지지를 보완하지 않고 자유 기타를 왼손과 허벅지·몸통의 실제 접촉으로 지지할 수 있는지 확인했으며 오른전완을 대체 지지점으로 삼지 않았다. 이는 해당 시험 조건이다.

이후 사용자 요청으로 같은 Fret 손가락/준비 팔 목표 유지 조건에 기존 고정 길이 스트랩을 적용해 ON/OFF를 비교했다. 현재 전체 설계에서는 스트랩을 비교 변수로 두며, 새 시험마다 ON/OFF·길이·경로를 명시한다. 현재 비교는 길이 최적화가 아니고 무스트랩 성공도 인증하지 않았다. [고정 길이 비교 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md:1)를 따른다.

사용한 고정 길이 **1.1018469719600776 m**와 버튼·guide 경로·수동 cable 모델은 비교 이력으로 보존한다. 무스트랩 초기 배치의 계약과 검증은 [왼손 세 면 지지 계획](/home/ajou/yigyu/3/stability_adapter_2/LEFT_UNDERNECK_CONTACT_PLAN.md:1)을 따른다. 과거 무스트랩 자세의 후기 안정성은 새 수평 자세의 지지를 입증하지 않는다.

## 7. 연주 목표와 안정화 보정

현재 기타 좌표계에 맞춘 연주 목표에 제한된 관절 보정을 합쳐 **하나의 최종 PD 목표**를 제출한다. 서로 다른 제어기가 최종 목표를 덮어쓰거나 평활화를 중복 적용하지 않는다.

왼손 세 면의 목표 영역과 법선은 현재 기타 p/q에서 매번 변환한다. 이는 움직이는 목표의 좌표 계산이며 실제 접촉 유지 제어는 별도 검증한다. 허용 범위 안이라도 팔의 도달 범위·목표 변화율·마찰 한계 밖의 움직임까지 보장하지 않는다.

- 범위 내부: 초기점 복원 비용은 0으로 설계하고 fret·strike 오차와 자연스러운 자세를 우선한다.
- 경계 접근: 기타 속도와 경계 여유를 보고 필요한 보정을 부드럽게 추가한다.
- 범위 이탈: 초기점이 아니라 가까운 허용 상태로 복귀하도록 보정한다. 한 번의 경계 교차나 미세 떨림만으로 즉시 종료·초기화하지 않는다.
- 보정 제한: 관절 한계·변화율·보정 크기를 적용하고 최종 손 목표·연주 공간을 확인한다. 구체적인 경계 여유와 종료 문턱은 후속 시험에서 정한다.

새 초기 후보에서 상수 PD·현재 기타 회전을 따르는 손목 추종·팔24 PI 유지 보정을 각각5초 비교했다. 팔 PI는 초기 팔 목표±0.3rad/모델 한계와0.8rad/s로 제한하고 손가락·몸통 목표와 PD는 유지했다. 최대 이동62.4mm/회전15.5°,종료34.4mm/4.6°로 개선됐으며 2~5초의2초 상태 기준 최대 변화는1.85mm/0.30°였다. 위치151표본 중3개가Z하한을 최대0.66mm 벗어났고 전체 회전 허용 집합 판정은 미구현이다. 손목 회전 추종은 악화되어 채택하지 않는다. 팔 PI는 무연주 진단으로, 향후 fret/strike 목표를 초기각에 묶는 용도로 승계하지 않는다. 전체 범위 판정·접촉 보정·연주 합성 제어는 아직 검증하지 않았다.

## 8. fret·strike 연결과 학습 순서

기존 checkpoint의 관측 차원은 fret 420/strike 303, 각 action은 30개다. 관절 이름·limit·정규화·EMA·task 후처리·history와 실제 기타 frame/속도 변환을 대조한다. 대표 조사 checkpoint는 최종 성능 인증이나 선정 완료를 뜻하지 않는다.

1. 원래 고정 기타 태스크의 연주 성능·checkpoint 자격과 실행 자원을 확인한다.
2. 동결 fret·strike source 목표 60개와 Thorax 6개를 연결하고 최종 적용 목표에 맞춘 history를 검증한다.
3. 무학습 연결 → 단일 이벤트 → 이벤트 전환 → 짧은 phrase 순서로 자유 기타 연주 오차를 측정한다.
4. 연결 계약 오류를 먼저 해결한 뒤, 자유 기타의 물리 응답 차이를 보정하는 residual 학습의 관측·action·보상·종료 조건을 결정한다.

연주 정확도와 기타 범위 유지 성능을 함께 평가한다. 제어권과 보정의 관계를 검증하기 전에 PPO 설정이나 네트워크를 복사해 장기 학습하지 않는다. [연주 연결 설계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_ADAPTATION_PLAN.md:1), [목표 합성 계약](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_TARGET_BRIDGE_PLAN.md:1), [학습 평가 순서](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:1)를 참고한다.

## 9. 다음 작업과 검증 체크리스트

- [x] 고정 하체·자유 기타·내부 충돌 환경과 초기 배치 진단 도구 준비.
- [x] 물리 없는 자세 조작·후보 저장, 실제 초기값·스트랩 표시 5초 녹화 준비.
- [x] 수평 넥 정적 후보 촬영 및 사용자 허용 범위·연주 우선 설계 기록.
- [x] checkpoint 계약 조사와 CPU 최종 목표 합성 검사.
- [x] 무스트랩·오른손 비접촉·왼손 세 면의 기타 상대 목표 정의와 CPU 이동/회전 검증. 실제 접촉 제어는 미완료.
- [ ] 허용 범위 판정·경계 거리 구현: 회전 특이점·q와 -q·경계 안팎을 CPU 검사.
- [x] 수평 기타 후보의 양팔·손 초기 배치: native 관절 한계·손바닥 위쪽·원본 형상 교차·오른손 분리 확인. 실제 세 면 접촉과 연주 공간은 후속 검증.
- [x] 무스트랩·오른손 비접촉 조건의 자유 기타5초 비교: 상수목표·손목 추종·팔 PI 측정/영상 저장. 기타 유지 성공 인증과 실제 연주는 미완료.
- [ ] 현재 넥 기준 손바닥·검지·중지 접촉을 별도로 보정하고, 엄지·소지 중심 지지에서 운지 가능한 분산 지지로 개선. 포화127/300회와 손 접촉/연주 목표의 충돌을 함께 검증.
- [ ] 작은 손·팔 움직임과 안정화 보정 OFF/ON 비교: 연주 공간을 유지하는지 확인.
- [ ] 현재 기타 frame 기준 fret·strike 연결 후 실제 이벤트 정확도·타이밍과 범위 내 시간을 함께 평가.
- [ ] 필요성이 확인되면 residual pilot 학습과 동일 구간의 비교 평가.

각 단위는 계획 → 한두 기능 구현 → 검증 → 검토 순서로 진행한다. 범위 내 시간, 최대 이탈, 이탈 지속시간·복귀, 연주 오류, 보정 크기, 접촉·관절 상태를 함께 기록한다. 정적 이미지·작은 후기 drift만으로 새 자세의 지지나 연주 성공을 선언하지 않는다.

## 10. 도구·기록과 과거 이력

- 현재 도구와 진입점은 [CURRENT_FILES.md](/home/ajou/yigyu/3/stability_adapter_2/CURRENT_FILES.md:1)를 따른다. 자연스러운 배치를 고르는 정적 도구는 물리적 상호작용 없이 사용한다.
- 실제 물리 실험마다 초기 설정·관절각·기타 p/q·스트랩 힘/표시 ON/OFF를 기록한다. 체크포인트 시험은 최소2초 준비 후 원본 첫 done 또는 보호 중단까지 환경 시작부터 Isaac Gym 영상을 저장하며 고정5초 cap을 두지 않는다. 체크포인트 없는 자세/정지 시험은 약5초를 기본 관찰 길이로 두고 필요하면 별도 계획에 명시한다. ON 비교에서는 길이·경로도 표시하며 오류·중단은 partial로 구분한다.
- 결과 문서에 이미지/영상과 설명, 입력·로그·변경 파일의 절대 경로 및 실제 줄 번호를 남긴다. 작은 단위 검수와 원자료 보존 절차는 [EXPERIMENT_WORKFLOW.md](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:1)를 따른다.
- 과거 조건별 실험·재시도·완료 체크리스트는 메인 본문에서 분리했다. [정리 전 메인 계획서 전체](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/main_plan_cleanup_v1/PLAN_before_cleanup.md:1)에 원문을 보존하며, 옛 PLAN.md 줄 번호는 이 사본에서 확인한다.
- 과거 결과·영상·로그는 docs에 그대로 있다. 앞선 파일 정리에서 제거한 옛 코드/leaf 계획은 [압축 백업과 삭제 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/README.md:1)을 통해 별도 작업 사본으로 복원한다.


## 2026-10-10 현재 기타 기준 Strike 실제 연결 진단

원본 Strike10,000 체크포인트의303D 관측/목표/phase/detector를 재사용해 현재 수평·무스트랩 초기값에서 실제 연결했다. 원본 `stability_adapter/`·공용자산·체크포인트는 변경하지 않았다. 왼팔12는 기존 PI지원, 오른쪽 Shoulder~손가락30은 정책,나머지39는 초기 PD목표를 유지한다. 오른팔 초기각 유지 PI는 정책과 경쟁하지 않도록 적용하지 않았다. source EMA/pick-grip 후처리 뒤 native한계/0.8rad/s 최종 변화율 제한을 적용하고 실제 최종목표를history로 회신한다. root/하체고정·기타자유·strapOFF·금지force/state쓰기0·학습0이다.

기타만10mm/5°변환한CPU입력에서 관측과 actor출력이 모두 바뀌고, 장면전체 동일rigid변환은 관측약1.3e-6/출력약2.6e-7 차이로 유지됐다. 현world목표변환도약0.25µm 오차였다. 이는 현재G좌표 갱신 검증이며 물리적전이 성공이 아니다.

실제정책은49control steps/196physics steps/0.816667초에wrong_crossing_count_termination으로 실패했다. sourceepisode TP0/FP4/FN1/F1=0,종료피크–목표152.024mm다. 새 native_v2는같은49policy controls/관측/최종목표/history를exact재현했다. 종료후actor/PI/song/detector를 멈추고 마지막81 PD목표상수로만1200steps/5초를 기록했다.151frames/5.0333초전신·손영상이다. 이후구간은 연주평가가 아니다. 최종 기타이동44.061mm/회전11.768°,최대63.386mm/14.883°이며 후기안정을 정책연주성공으로해석하지 않는다.

첫native의제한된입력SHA를보완해native_v2 상위wrapper가import/초기화전에956입력SHA·소스사본을저장했고실행후변경0을확인했다. 소비된실패/계획/producer는보존했다. 결과보고서는계획과구현차이를명시한다: v2의196step종료native p/q표본은trace에없고clock/reason/policyinfo만남는다(192→200표본); 종료뒤q/qd/Gfinite·속도·root/하체고정·상수목표검사만하며 지속source기하안전monitor/상체posefinite검사는추가하지않았다. 원본explicit stiffness torque와현재nativeimplicitPD/변화율제한차이가있어 체크포인트일반성능을이번실패만으로단정하지않는다.

- [x] 원본current-G경로 확인/303D체크포인트ABI/CPU좌표변환검사
- [x] 실제정책49steps연결·실제최종goal-history연속성·학습/RMS보존
- [x] 종료원인/재현·초기값·5초물리영상·사전입력보존
- [ ] 다음소단계: 현재G의원본ready점근처에RH피크초기위치/원본pick-grip관절을맞추고,초기배치와PD/변화율차이를분리해재시험한다. 그뒤작은G위치/회전범위의타현일반화를검증한다. Fret 연결은왼손지지와연주제어권관계를먼저정한다.

[계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_LIVE_GUITAR_PROBE_PLAN.md:1),[5초기록구간계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TRANSFER_RECORDING_CONTINUATION.md:1),[최종실행진입점](/home/ajou/yigyu/3/stability_adapter_2/strike_probe_preserved_run.py:1),[결과분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/analysis/summary.json:1). 결과 README/독립검수는이번phase에서정리한다.


## 2026-10-10 현재 기타 기준 양손 준비 구현

현재 기타 pose 및 string marker에서 타현 준비점을 매 control frame 갱신한다. PREPARE에서는 왼팔12 기존 지지 PI, 오른팔12 bounded IK, 오른손21 원본 grip 목표를 사용하고 나머지36의 초기 PD 목표를 유지한다. 양손66 제어 범위는 유지하며 root/하체고정·몸통9 목표유지·자유기타·무스트랩·외부힘/부착/시작후 상태쓰기0이다. 준비 gate는 현재 넥 아래면 palm+최소1finger의 실제 positive raw lambda 접촉과 palm 위쪽, RH source ready50mm 이내/앞3mm/grip/noncontact를 6연속프레임 확인한다. 외부50mm gate는 원본 source10mm READY와 다르다. 잘 맞춘 초기값은 바로 통과할 수 있으며 WAIT→REACH→GRIP→TRANSPORT는 도입하지 않는다.

gate 통과 시 준비한 event/lane/current target geometry를 보존하고 실제 최종목표로 source EMA/history를 맞춘 뒤 frozen303D/30action Strike를 시작한다. PLAY에서는 왼팔12 지지, 오른쪽 Shoulder~손가락30 정책, R_Thorax3 준비목표유지를 합쳐81개 목표를 단일 제출한다. source/PD 목표는 native limit·0.8rad/s 안으로 제한한다. LH 지지 소실/피크 body 뒤면 이동/source done 시 마지막 목표 HOLD로 기록하고 실제 상태를 reset하지 않는다. 학습 update0이며 actuator 차이와 checkpoint 공식 G0 미인증은 유지된다.

오른팔 초기 탐색2후보 중1개가 source 교차0·검색 당시 목표점2.201mm를 통과했다. native task 초기화 후 lane 선택이 달라 실제 t0 ready거리33.712mm다. 동일 초기값/PD로 v1~v4 각1200steps·151frames/5.033초 전신/손 영상을 저장했다. 추가 RH PI는 기타 종료 drift를 줄였지만 RH 준비거리 last56.300→104.324mm로 악화해 채택하지 않았다. 최종 v4는 판정/target연속성 보완과 기본IK를 사용하며 v1 물리 trace를 exact 재현했다. 981입력 변경0·14계약검사·최종CPU13검사를 통과했다.

최종 v4는 palm조건1/300, finger298/300, 동시0, RH근접9/300으로 gate미충족·actor0이다. 준비 구현/5초 기록을 완료했으며 실제 양손 준비·PLAY 전환·타현 성공은 아직 검증하지 못했다. 다음 소단계는 현재 넥 기준 palm underside 실제 지지 확보와 오른팔 추종 잔여오차를 분리해 개선하는 것이다. 기존 source/result/leaf는 보존하고 수정된 판정/전환/미채택PI도 각각 별도 버전에 남겼다.

- [x] current-G 준비 helper·실제접촉 판정·연속6프레임 검사
- [x] RH 초기 후보 native audit·제한된 준비 IK 및 handoff target/history 보존
- [x] 4회5초 실제영상/초기값·분석·소스입력 보존
- [ ] 실제 palm+finger 지지와 RH 근접을 함께 확보하여 PLAY 전환 검증

[실행 계획](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_RELATIVE_READY_PLAN.md:1), [최종 제어 선택](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_READY_BASELINE_SELECTION.md:1), [최종 실행 entry](/home/ajou/yigyu/3/stability_adapter_2/preparation_preserved_run_v4.py:1), [결과·초기/종료 이미지·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/README.md:1), [분석 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/analysis/summary.json:1).


## 2026-10-10 준비 자세에서 Strike 실제 실행

사용자 요청에 따라 기존 엄격한 준비 runner를 보존하고 별도 연결 진단을 추가했다. 같은 초기값으로0~2초 current-G 준비 제어를 수행한 뒤 사용자 위치/회전 범위 안·LH finger/up·RH 앞쪽/grip/비접촉·ready80mm 근처에서 frozen Strike를 시작한다. 이는 이번 시험의 느슨한 진단 entry이며 기존50mm+palm6frame gate와 원본10mm READY는 변경하지 않았다. 회전 범위는 Euler 두 표현 및 +90°특이점 x−z로 검사하고 Z상한은 초기 실제Chest로 측정한다. PLAY중 범위/접촉은 기록하며 경계 복귀제어는 아직 없다.

실제2초에서5초까지303관측/30action 체크포인트를180control/720physics steps 실행했다. event/lane/current geometry·최종goalhistory를 보존하고 RH준비IK와 경쟁하지 않게 정책30+LH12PI+RThorax3준비목표+나머지36을81개 단일목표로 합성했다. 0~2초 native61표본/목표120개는 이전v4와exact이며 초기native/PD도exact다. 전체1200steps·151frames/5.033333초 전신/왼손근접 영상을 저장했고986입력 변경0·15계약검사·CPU11검사 및 전체300goal→history역산차0을 확인했다. 학습0·스트랩OFF·기타자유·root/하체고정·몸통9목표유지·외부힘/부착/상태덮어쓰기0이다.

이번 실행은5초끝까지PLAY이며 종료/HOLD는없다. 정책3초에서 인정target hit0/accepted release0, physical release1/miss8/wrong crossing1이며 마지막 running strike_f1=0이다. 원본 motor phase는READY(0)에 남았고 전체곡/episode종료지표는 미측정이다. 기타 최대59.579mm/46.151°·종료23.034mm/46.036°이며 정책180표본 중64개만 사용자범위 안에 있었다. LH palm75/finger180표본이어도 엄격준비전체조건은0이었다. 실제정책연결은 완료했으나 타현·기타안정화 성공으로 채택하지 않는다. 후속은 현재ready점 도달과 정책-현재PD/변화율 차이, 기타회전 및 범위복귀 보정의 영향을 분리하는 것이다.

- [x] 소비된원본보존·회전범위/진단시작 조건 구현 및CPU검사
- [x] 실제Strike180steps/3초 연결·현재G 관측 및history 연속성·전체5초 기록
- [x] 원자료분석·연결과연주성공 구별·새산출물 경로
- [ ] 원본READY 도달·인정타현·범위유지 성능 개선

[진단 계획](/home/ajou/yigyu/3/stability_adapter_2/PREPARED_STRIKE_CONNECTION_PLAN.md:1), [실행 entry](/home/ajou/yigyu/3/stability_adapter_2/prepared_strike_preserved_run.py:12), [정책 실행 구현](/home/ajou/yigyu/3/stability_adapter_2/run_prepared_strike_connection.py:24), [실제영상·이미지·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/README.md:1), [분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/analysis/summary.json:1), [타현pulse 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/event_analysis/summary.json:1).


## 2026-10-10 사용자 정정: 손바닥 접촉의 적용 범위

왼손 손바닥의 넥 아래면 접촉은 시작 시 안정성을 위한 초기 배치 목표다. 항상 접촉해야 하는 연주 제약으로 승계하지 않는다. 이 내용은 앞선 엄격한 palm+finger 준비 gate와 접촉 유지 과제를 향후 실험에 그대로 적용한다는 해석보다 우선한다.

- 초기 배치: 손바닥이 넥 아래면을 지지하는 자세를 선호하되, 실제 접촉과 시작 흔들림을 별도로 측정한다. 연주 진입 직전의 손바닥 접촉도 필수 gate로 강제하지 않는다.
- 연주 중: 운지와 기타 움직임에 따라 손바닥 접촉의 분리·재접촉을 허용한다. 손바닥 비접촉만으로 실패·중단·초기화하거나, 접촉을 만들기 위해 연주 목표를 덮어쓰지 않는다. 다른 손가락의 항상 접촉 조건으로 대체하지 않는다.
- 평가·보정: 기타의 사용자 허용 위치·회전 범위와 실제 fret/strike 성능을 중심으로 평가한다. 접촉 상태는 지지 변화의 보조 측정값이며, 접촉 소실만으로 보정을 발동하지 않는다. 경계 접근·이탈과 기타 움직임을 고려한 보정은 후속 구현 대상이다.
- 현재 구현: `run_prepared_strike_connection.py`는 이미 PLAY에서 접촉을 기록만 한다. 기존 엄격 runner·소비 소스·기록은 당시 조건의 재현용으로 보존한다. 이번 작업은 기준 정리이며 새 시뮬레이션이나 제어 코드 변경은 없다.

체크리스트: [x] 사용자 기준 기록 · [x] 최신 PLAY 경로와 대조 · [ ] 후속 실험의 진입/보상/종료 조건에 반영.


## 2026-10-10 지속 연주 작업: Strike 전달 진단 1차

사용자가 자율적인 지속 구현/실험을 요청했다. 현재 source READY 미도달과 오른쪽 어깨 목표-실제각 오차부터 분리한다. 동일 초기 후보로 PLAY 오른쪽30 목표 변화율0.8/3.2rad/s와 오른팔12 PD stiffness4배/damping2배를 작은3조건 비교한다. 기타·몸통·왼손·손가락·source 판정은 유지하고 손바닥 접촉 소실만으로 실패로 보지 않는다. 5초 영상/초기값/실행입력과 source 인정 타현/준비점/기타 범위를 기록한다. 이후 결과를 보고 current-G 보정·준비 정확도 개선 또는 학습 구조를 선택한다.

- [x] 지속 작업 목표 등록·실험 계획 기록
- [ ] 새 runner 계약 검사·3조건5초 native 실행
- [ ] 실제 결과 분석·영상 문서·별도 검수
- [ ] 다음 단계 선택·구현·검증 지속

[계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TRANSFER_ITERATION_PLAN.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/`에 저장한다.


## 2026-10-10 지속 작업 경과: 1차 전달 비교와 준비점 일치

1차의깨끗한base_v2/rate/gain_v2는각1200physics·151nativeframes·5초/입력보존 검사를 완료했다. 인정target hit은모두0이다. rate3.2/gain1만원본source READY유지조건을통과해APPROACH가관측됐으나 policy범위안표본20/180으로기타유지가나빠졌다. gain4는174actor/APPROACH미관측·범위안7/174로채택하지않는다. 새baseline float64cap산술이과거scalar와미세하게다르므로이전실험의byteexact재현으로주장하지않고새3조건끼리비교했다. gain변경시점은환경생성후첫physics전이다.

첫base시도는PATH의ninja미노출로import단계에서실패했고PATH를보완해base_v2를실행했다. gain첫시도는전체physics5초를완료했으나다음runner의로그필드수정으로보수적전체sourceclosure가변경됐으므로검증실패로보존했다. gain_v2로같은조건을재측정해closure변경0을확인했다. 다른실행중기존A파일수정금지규칙을재개기록에명시했다.

원본ready점보다30mm G-z높은이전준비목표를제거한새alignment는5초동안최소17.061mm까지접근했지만10mm/grip6연속frame에는도달하지못해actor0이다. 기타최대회전7.095°로정책실행시험보다작지만연주성공은아니다. 다음에는같은새 runner에서오른팔초기PDgain4·준비반경0.6rad·갱신되는IK목표-실제각의0.5배목표보정을새조건으로시험한다. 다른부위PD/목표·기타자유조건/범위/source판정은유지한다.

원본과비슷한human관절torque+implicitdamping후보파일도별도작성/사전검수했으나미실행이다. SDK문서는EFFORTmode만tensoractuation이적용된다고명시하며해당POS0패턴의실제구동검증이없어채택/성공으로주장하지않는다. 기타/root외력을대신사용하지않는다.

- [x] 3조건실제5초·초기값·closure·원자료분석 완료(문서/독립최종검수진행)
- [x] 원본readyG stand-off0·actual10mm/6frame진입·요청goal기록 구현/사전검수
- [x] 첫alignment5초/actor0·17.061mm잔여오차 확인
- [ ] 보정된alignment조건5초 검증 후다음개선선택

[전달비교결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_final/summary.json:1), [준비점일치계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_ALIGNMENT_PLAN.md:1), [첫alignment분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/analysis_aligned/summary.json:1). 최신재개지점은 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/CONTINUOUS_WORK_STATUS.json`이다.


## 2026-10-10 지속 작업 경과: 준비점 일치 3조건과 정책 재진입

stand-off0의aligned/gain1/radius.3는준비거리최소17.061mm·기타최대7.095°이고,반경만.6으로넓힌wider는28.334mm/8.258°였다. gain4/radius.6/errorgain.5를함께사용한compensated는33.712mm/22.636°로악화됐다. 세조건모두1200step·151frame영상/closure변경0을확인했으나외부10mm/6frame진입gate를통과하지못해actor0이다. 정책을실행하지않은결과를Strike능력평가로해석하지않는다.

외부의정밀10mm준비를연주의필수선행조건으로채택하지않고,새aligned-play진단에서는ready_G 자체를준비목표로유지하면서기존2초/80mm진입조건으로정책을연결한다. 원본source의10mm/6frame READY는그대로이며실제정책이자연스럽게획득하도록한다. native_ready_streak은관측값으로남긴다. 초기팔반경.3/gain1/rate3.2/no-error보정으로시작한다. PLAY는frozenRH30policy/LH12support/RThorax3prepared/other36의단일81목표이며준비IK는경쟁하지않는다.

- [x] 전달3조건 독립검수PASS·실행소스사본/2540산출물봉인
- [x] 정밀준비3조건5초기록·분석완료(산출물/검수후정리)
- [x] stand-off0+느슨한진입의새runner문법/사전검수PASS
- [ ] 실제aligned-play5초평가 및다음제어보정선택

[정밀준비분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/analysis_three/summary.json:1), [aligned-play계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_ALIGNED_PLAY_PLAN.md:1). 무스트랩/자유기타/root하체고정/몸통목표유지·손바닥지속접촉불필수 조건은유지한다.


## 2026-10-10 지속 작업 경과: 시간 대기 제거

aligned-play는5초1200steps/151frames/closure변경0이지만actor0이었다. t2의currentready거리17.874mm·finger/up/front/grip/RHnoncontact는충족했으나기타rotation범위가false였다. 원본회전집합의한표현은xyz[-89.415,87.162,0.368]°이고등가표현[90.585,92.838,180.368]°가X/Z상한을조금벗어난다. 이값을다른Euler로잘못판정한것이아니며지정범위를좁히거나넓혀성공으로만들지않는다. source10mm외부정밀진입을필수로승계하지않으며실제조건충족시시작한다.

전체300control중113개가사용자범위안이었고초기~1.8초에준비기회가있었지만임의의2초비교시간하한이막았다. 새automatic-start진단은시간대기하한을없애고실제currentready25mm/범위안/finger/up/front/grip/RHnoncontact가충족되면즉시frozenStrike를연결한다. 외부25mm는이번근접진입조건이며원본source10mm/6frame·motorphase·detector·시간은그대로다. 손바닥지속접촉필수0·원본소스/영상보존.

- [x] aligned-play5초/actor0·범위로막힌진입원인분리
- [x] automatic-start 새runner/leaf/문법/독립사전검수
- [ ] 실제자동진입·sourceREADY/인정타현·기타범위5초검증

별도로POS0+tensoractuation의실제유효성은human-only81축/오른팔12 torqueON·OFF응답으로검증할후보를작성했다. source-like구동복원을API성공만으로주장하지않으며기타/root외력을허용하지않는다. 이실험은정상human관절PD구동의검증이며타현성능평가와구별한다.

[자동시작계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_AUTOMATIC_START_PLAN.md:1), [구동응답진단계획](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_PD_ACTUATION_PROBE_PLAN.md:1), [aligned-play실제분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/analysis/summary.json:1).


## 2026-10-10 지속 작업: 자동 시작 결과와 READY 보정

자동진입은0.816667s PLAY251actor/1200physics/151frames/15contracts/closure변경0이지만sourcephase0만관찰됐고인정targethit0/release2/miss10/wrong2였다. policy관측minready10.766mm,max기타46.861deg로아직연주실패다. 기준관절한계/actionmidhalf와기본RHkp/kd/armature는source와일치하지만현재기타/팔초기상태는원본과다르다. 범위를사후늘리거나sourceREADY10mm6frame를바꿔성공으로만들지않는다.

normalhuman관절actuation probe v1은래퍼중첩을잘못벗겨physics0에차단됐다. 실패소스/closure/초기프레임보존후새v2로재시도했다. v2의동일초기POS0오른팔12에서torqueOFF0/ON약10Nm명령의첫4step과전체152기록상태가exact였다. 두조건각5초/151frames/closureunchanged. 이CPU/POS조합에서tensor stiffness torque의실제적용근거가없으므로source-like hybrid후보를채택하지않는다. 제출torque는측정힘이아니다. 정상implicitPD를유지한다.

후속새READY-residual v2는frozenStrike의R9목표에currentG READY와실제pick위치기반FK변위오차에서구한±.15rad잔차를더한다. sourceREADY0에서만켜며APPROACH이후정책만쓴다. 원본phase/타현/songtime/weights/RMS/손가락21/Thorax목표/왼손지지/몸통/root하체고정은유지한다. 기타외력/고정/상태쓰기0. 작은합성목표잔차로source준비획득과실제타현이개선되는지검증하고학습구조는실측후정한다. 원v1예측점표현은미실행보존하고v2에서실제pick으로FK변위anchor를명시했다.

- [x] precision3조건검수/1742artifact봉인
- [x] aligned-play·automatic-start5초/분석/이미지·영상문서작성
- [x] POS0 actuation OFF/ON각5초·saved상태응답exact 확인
- [ ] measured-pick READY잔차native5초/원본sourceREADY·인정타현·범위평가

[자동진입결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/README.md:1), [구동효과원자료분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/analysis/summary.json:1), [READY 잔차v2계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_RESIDUAL_V2_PLAN.md:1). 목표는여전히실제연주와사용자기타범위유지이며손바닥지속접촉불필수다.


## 2026-10-10 지속 작업: READY 잔여 오차의 PI 비교

READY 비례잔차v2는5초/251actor/16contracts/closure1016변경0이나sourcephase0/targethit0이었다. minready10.439381mm로기준10.766370mm보다조금줄었지만원본10mm6회연속을얻지못했고max기타회전46.014401deg/범위119/300(정책73/251)이다. 보정최대.13892755rad/.15포화0개이므로상한확장이필요하다는근거는없다. 새후보는현재pick오차의R9 IKΔ를P로두고READY0에서만I+=.2*Δ를±.3rad적분하며최종P+I±.3/rate/modelantiwindup을적용한다. 다른phase에서는I를유지해policyjointbias만주고타현기하추적을추가하지않는다. 실제state/phase/성공판정/weights는수정하지않는다.

- [x] aligned-play/automatic-start 검수·590/594artifact봉인
- [x] POS0 OFF/ON 검수PASS·1182artifact봉인(효과근거없어hybrid미채택)
- [x] READY 비례잔차v2실제5초완료·분석/후속PI계획
- [ ] READY PI native5초·인정타현/사용자범위평가

[READY v2 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/analysis/summary.json:1), [PI 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_INTEGRAL_PLAN.md:1), [구동응답/실제영상문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/README.md:1). 자유기타/no strap/root하체fixed/selfcollision/몸통PD/손바닥지속접촉불필수·사용자범위고정 조건을유지한다.


## 2026-10-10 지속 작업: 원본 READY 획득과 다음 타현 경로

READY PI는5초/251actor/16contracts/closure1019변경0에서원본10mm6frame를획득해phase[0,1]/READYsuccess1이었다. minready3.240488mm,maxG8.991360deg/end5.300883deg·범위251/300(정책205/251)로기존READY P max46.014401deg에서개선됐다. 하지만targethit0/accepted0/miss10이다. physicalrelease1은READY중1.033333s의string3,target2/phaseviolation으로인정되지않았다. APPROACH첫1.266667s,그후entry5mm근처까지갔지만손이Gz+.15m로멀어졌다. 준비획득과연주성공을구별한다.

후속phase-target 잔차는원본정책R30을유지하며R9에현재기타의원본READY/ENTRY/EXIT 기하오차를같은boundedPI로더한다. APPROACH실제pick이원본entry_distance안에도달한것을읽어adapter waypoint만EXIT으로바꾼다. sourcephase/entry판정/타현detector/시간/weights는직접설정하지않는다. RECOVERY는원본clearance기하를따른다. 이는모델기반어댑터진단이며purecheckpoint성능평가아니다. 실제동작으로얻은타현/범위/타이밍을바탕으로학습방식을정한다.

- [x] READY P 검수/608artifact봉인
- [x] READY PI 실제5초/원본READY1/APPROACH까지확인
- [ ] phase-target boundedPI5초/실제인정타현·기타범위·timing평가

[READY PI 원자료분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/analysis/summary.json:1), [후속계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_PHASE_TARGET_RESIDUAL_PLAN.md:1). 동일free/no strap/fixedrootlower/몸통PD/selfcollision/접촉지속불필수/사용자범위고정이다. EFFORT마이크로작동확인후보는미실행으로보류하며지금은실제READY획득이확인된nativeimplicitPD를쓴다.


## 2026-10-10 지속 작업: 첫 인정 타현과 회복 문제

phase-target boundedPI는실제인정targethit1/physicaltargethit1/accepted1을2.483333s,string2에서얻었다(timing45.179844ms). sourceREADY1/phase0,1,2가실제원본판정으로진행했다. 그러나release5/wrong4/miss2/partialF1.25이며wrong-count source terminal2.666667s로policy를정지했다. 49PREPARE/111PLAY/140HOLD/1200physics151frames/16contracts/1025closure변경0이며HOLD에도물리5초는계속됐다. maxG44.171368deg/범위143/300(정책66/111)라목표연주유지는아직실패다.

후속orientation 잔차는원본phase별waypoints/READY/타현detector/시간/weights를유지하고currentG기준초기준비RHpick회전을soft5mm/rad로선호한다. source회복clearance_required는실제로true이며geometry5가이미release_lift점이다. 단순exit-depth에만눌렀다거나source에lift가없었다는해석은틀리다. 실제lifted/reachedfalse라손방향과contact/Grotation이그점을못따르는경과를분리한다. clearance점높이를20mm로바꾸는우회는하지않고실제움직임으로원본latch를얻는지본다. R9모델PD목표만boundedPI로보정하고기타/rootbody힘·상태쓰기는없다. 손바닥지속접촉필수0.

기존analyzer min_prepare가not_actor를모아HOLD까지포함한범위표기오류를찾았다. 원본producer/analysis를보존하고새analyzer_v2와analysis_phase_corrected에서PREPARE/PLAY/HOLD를분리했다. 실제native자료는재실행하거나수정하지않았다.

- [x] READY PI 검수·609artifact봉인
- [x] phase-target실제5초/first-hit1/원본wrongcross stop/교정분석·영상문서
- [ ] softorientation잔차5초/타현후clearance획득·기타범위·timing평가

[첫타현과실제HOLD영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/README.md:1), [후속계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_PHASE_ORIENTATION_RESIDUAL_PLAN.md:1). 원본source/실패source/initialcandidate/자유기타·no strap·root하체fixed·몸통PD·selfcollision·사용자기타범위는보존한다. 진행은계속active이며first-hit한번을완료로판정하지않는다.


## 2026-10-10 지속 작업: 회복 제어권 분리

모든phase의softorientation5mm/rad는5초/251actor/sourcephase0/READY0/hit0/miss10/범위52/300(정책6/251)/maxG45.290342deg로준비부터악화됐다. 최소ready6.379423mm가한번10mm안에들어왔다는것과6연속조건획득을혼동하지않는다. orientation후보는미채택하고첫실제hit를얻은position-onlyphase-target를기준으로돌아간다.

회복-priority후보는원본sourcephase0/1의policyR30+R9PI를완전히유지한다. sourcephase2에서만R9 신규정책목표보다원래currentGclearance작업점오차에따른현재PDgoal+0.5*IKdelta 증분목표를우선한다. 이때sourceREADY/APPROACH용I는동결하고finger21은계속정책이제어한다. 단일최종nativebounds/rate3.2/inversehistory과원본latch/detector/time/weights는그대로다. 임시회복제어권은normalhumanjointPD목표뿐이고기타/몸체외력·상태쓰기없다. 원래latch4mm/12frame·rearm/scheduledrecovery완료를실제움직임으로얻는지본다.

- [x] first-hit phase 검수·622artifact봉인(성공완료아님)
- [x] globalorientation실제5초·실패/영상문서·후속계획
- [ ] recovery-priority5초·인정타현/회복완료·기타범위평가

[orientation 실제결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/README.md:1), [회복우선권계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_RECOVERY_PRIORITY_PLAN.md:1). 자유기타/no strap/root하체fixed/몸통PD/selfcollision/손바닥지속접촉불필수·기타사용자범위고정/원본보존을유지한다. 학습은아직0업데이트이며실측성공과제어구조를확인한뒤선택한다.


## 2026-10-10 지속 작업: 실제 회복 완료와 회복 속도 비교

recovery-priority는원본인정hit1(2.483333s),clearance lifted2.883333s/reached및scheduled완료3.266667s,source2→1 3.35s를실제측정으로얻었다. 회복중release0이고전체maxG9.019638deg/범위229/300(정책126/182)로개선됐지만miss7/wrong4/source terminal3.85s라연주완료는아니다. 1200physics151frames/16checks/1032closure변경0/182PLAY+69HOLD+49PREPARE이고HOLD에서도물리5초계속이다.

다음은회복R9증분gain만.5→1.0으로높여실제clearance획득시간과후속인정hit를비교한다. phase0/1,최종모델한계/rate3.2,원본clearance4mm/12frame/rearm/시간/검출기/weights는유지한다. 학습0,사용자범위·freeG/no strap/root하체fixed/몸통PD/selfcollision·손바닥지속접촉불필수. 기타상태나원본phase를강제로바꾸지않는다.

[실제회복결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/analysis/summary.json:1), [속도단일변경계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_RECOVERY_SPEED_PLAN.md:1). 목표는active이며후속음표연주까지계속한다.

orientation raw 추가검수: native-before READY거리≤10mm는11개이며그중거리6연속도있었다. source는별도step후 at_ready AND grip_success로판정하므로거리표본만으로sourceREADY획득을인증하지않는다. 원본success0/phase0유지는확정이며앞선‘6연속조건’표현은원본복합판정을뜻한다.


## 2026-10-10 지속 작업: 회복 gain1 결과와 gain2 비교

gain1은source실제lifted2.783333/reached·scheduled완료3.15초로gain.5보다각0.1/0.116667초빨랐다. 하지만phase2→1은동일3.35초이고hit1/miss7/wrong4/partialF1.153846로후속인정타현없다. 원본시간표진행으로event4miss후event5접근을기다린경과다. 1200physics151frames16checks1035closure변경0/49PREPARE180PLAY71HOLD/maxG9.019638deg/범위238/300(정책132/180)/terminal3.816667이다.

다음gain2는회복증분한항목만1→2로높인다. 이전468correction성분에서2*delta최대.052046rad<framecap.053333rad였지만새actual응답은미검증이다. 원본latch/phase/시계/타현·범위판정은유지하며실제회복시각과음표대상방향을검증한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_RECOVERY_SPEED_V2_PLAN.md:1), [gain1분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/analysis/summary.json:1). 기존source/결과보존·학습0·목표active.


## 2026-10-10 지속 작업: 시간무관 조기 EXIT 보정 수정

gain2는원본hit1/clearance lifted2.55/reached·scheduled완료2.95/2→1 3.033333을얻었으나source terminal3.25로후속연주실패. READYwrong1+회복후nonhit3=wrong4/miss4/partialF1.2이며조기종료로관측기회가줄어F1상승을성능향상으로해석하지않는다. 1200physics151frames17아닌16checks1038closure변경0,49PREPARE146PLAY105HOLD/maxG9.019638deg/범위182/300(정책101/146).

원인후보중확인된구조오류는adapter가event1/2에서원본approach_open=false인데ENTRY거리가6mm안이면236.5/524.1ms일찍EXIT를계속지시한점이다. 새후보는그선택만원본시간helper(현재clock+effectiveeventtime+firstoffset+70mslead)로제한한다. source자체phase/clock/타현창/weights를변경하지않는다. source singlephase목표ENTRY와adapterEXIT전환은구별하며손접촉하중의인과는미입증. 기존회복gain2/목표한계·rate3.2/PI·fingerspolicy/freeG등은유지하고실제연주결과를다시확인한다.

[시간조건계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_EXIT_PLAN.md:1), [gain2원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/analysis/summary.json:1). 정상EFFORTprobe_v2는초기mode-readback독립검수까지만완료한미실행대안이다. 원본보존·학습0·목표active.


## 2026-10-10 지속 작업: 시간조건 결과와 정상 관절 EFFORT 응답 확인

timedEXIT는21개EXIT active명령모두원래approach_open이후이며5초1200physics151frames/17checks1044closure변경0/251PLAY/noHOLD/no terminal을얻었다. 원본READY1/인정hit1(event3,string2DOWN,2.783333s,timing−33.181908ms)/release3/miss9/wrong2이다. maxG9.074870deg/범위241/300(정책195/251)로5초정책은계속됐으나clearancelifted는4.583333에야참이고reached/scheduled완료0이라연주목표미완료다. 회복gain2는유지됐지만타현전다른상태와회복waypoint여서직전gain2효과와단순비교하지않는다.

다음소단계는sourceexplicit관절stiffness와nativepositionPD구동차이의미해결부분을정상humanEFFORT 첫4physics OFF0/ONbounded약10Nm로검증한다. 기존POS0probe는전체상태exact로토크응답근거가없었다. 미실행v1은보존하고v2는EFFORT nativeprops초기readbackexact를추가했다. 최초4physics후원래POSITIONPD를복원하고이후물리0–5초151frames를기록한다. 기타/몸체force와state쓰기guard는유지하며rawAPI허용은정상humanjointtensor한메서드뿐이다. massmatrix는readonly/native확인만하며제어에사용하지않는다. 학습0이며연주성공실험으로해석하지않는다.

- [x] timedEXIT 실제5초·원본시간선택·hit1/wrong2·회복미완료분석
- [x] EFFORTv2 AST3.8·독립사전검수/readback강화
- [ ] OFFON각0–5초실제모드·초기4step응답·복원·massmatrix·closure/영상확인
- [ ] 분석·문서·독립검수/봉인후연주보정제어다음설계

[시간조건실제자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/analysis/summary.json:1), [정상관절구동진단계획](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_EFFORT_ACTIVATION_PROBE_V2_PLAN.md:1). 원본freeG/no strap/fixedrootlower/몸통PD/selfcollision/손바닥지속접촉불필수/사용자기타범위는보존하고연속작업목표는active다.


## 2026-10-10 지속 작업: 정상 EFFORT 응답과 PLAY 감쇠 지연 비교

EFFORTv2 OFFON각1200physics151frames9checks1045closure변경0,초기states/goals/props/nativeEFFORTreadback/massmatrixexact. 실제첫4스텝(.016667s)ON−OFF RShoulder_z angle+.039242268rad/velocity+3.846986488rad/s,최대전체angle차.042840123rad이다. 정상jointtensor는EFFORT에서실제양의응답을보였고POS0무응답과구별한다. massnative1x81x81finite/대칭차4.47e−8/read-only며제어에쓰지않았다. requested10.000001907Nm는측정torque아니다. ON/OFF모두첫4후원래POSITIONPD복원/이후0명령·152savedstates·300commands를확인했다. 연주/학습실험아니다.

다음은nativePOSITION을유지하고PREPARE→PLAY에RShoulder/Elbow/Wrist9 damping만*.25로한번낮춰고감쇠지연가설을비교한다. stiffness/effort/mode/armature/Thorax/fingers/나머지props는유지하며원본source의시간·검출·gains/weights와사용자기타범위는보존한다. EFFORT모드를연주에직접채택하지않는다. timegateEXIT/RECOVERgain2/PI·rate3.2·실제history는직전시험대로다. PDproperties변경이실제state를쓰기하지않음과native전체배열readback을기록한다.

[정상구동응답](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis/summary.json:1), [PLAYdamping계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_PLAY_DAMPING_PLAN.md:1). timedEXIT검수·634artifact봉인완료이며회복미완료/곡미완료다. 모든단계보존·학습0·연속목표active.


## 2026-10-10 지속 작업: 준비 감쇠 보존과 실제 APPROACH 전환 비교

PLAYhandoff damping*.25는5초1200physics151frames20checks1048closure변경0이나READY0/원본phase0에서wrong4로1.0초terminal(11PLAY240HOLD49PREPARE)이발생했다. HOLD에서도자유물리/녹화5초계속이며평형성공아니다. 감쇠변경은채택하지않는다. 정상EFFORTactivation OFFON은1256artifact봉인완료이며연주성공아니다.

다음은timedEXIT의PREPARE/READY baseline nativePD를유지하고실제sourcemotor_phase1을처음관측한뒤R9damping*.25를한번적용한다. 원본READY확보전변경을피하며APPROACH·RECOVERactual지연과타현/회복을검증한다. sourcephase/clock/검출기/weights와사용자기타범위는그대로다. currentFK는native81/XML각축rotvec와초기native상대회전을사용하며Euler직렬아니다; rawnativeJacobian을미검증위치미분으로채택하지않는다.

[새단계계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_APPROACH_DAMPING_PLAN.md:1), [실제PLAYdamping분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis/summary.json:1). 이전소비source보존/학습0/연속목표active.


## 2026-10-10 지속 작업: 앞선 타현 인정과 회복 감쇠 복원

sourceREADY baseline을유지한APPROACH진입quarterdamping은READY1/실제hit1(event1string2DOWN1.35s,+44.484798ms)을얻었다. 하지만RECOVER중1.5/1.683333/1.7초에wrong3가추가되어1.716667초wrongcountterminal이다. 1200physics151frames20checks1051closure변경0/49PREPARE54PLAY197HOLD/region292/300(정책49/54),maxG7.095455deg이며clearance완료0이다. 조기 종료의 partial F1=0.2857은 향상 증거가 아니다. 낮은감쇠를회복까지유지한설정은미채택이다.

다음은sourceAPPROACH1에서만R9damping*.25, READY0/RECOVER2에서는baseline1로복원한다. 실제sourcephase만읽고원본clock/detector/clearance·weights와사용자범위는유지한다. 직접저장된81actual회전대조에서XMLBq arm8그룹max오차<.000039deg로관측궤적좌표정합성을확인했다;B를I로바꾸지않으며Jac미관측방향증명으로확장하지않는다. PLAYdampingnegative639artifact/EFFORTactivation1256artifact봉인완료. 학습0·연속목표active.

[단계계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_APPROACH_ONLY_DAMPING_PLAN.md:1), [직전타현·실패원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/analysis/summary.json:1), [현재좌표대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_fk_coordinate_audit_v1/analysis/summary.json:1).



## 2026-10-10 지속 작업: 실제 회복 완료와 조기 ENTRY 제거

APPROACH-only 감쇠는 첫음표(zero-based event0,타현후index1) hit1@1.35초를보존하고clearance lifted1.4/reached2.183333/scheduled완료2.366667을얻었다. 두번째geometry physicalhit는eventindex3@2.75초줄2DOWN이지만−64.536217ms premature이므로target_hit는추가없다. 실제타현판정1/physicaltarget2/geometryaccepted2/release6/miss3/wrong4/terminal3.066667/PREPARE49 PLAY135 HOLD116/5초1200physics151frames20checks1056closure변경0/범위287/300(정책125/135). 원본검출기에서geometryaccept와시간인정을구분한다.

다음은sourcephase1의originalapproach_open=false동안adapter ENTRY4 대신READY3를선택한다. source시계/phase/helper/±50ms윈도우/8msearlygrace와clearance및weights는유지하며첫hit·첫회복완료까지동일성을검증한다. 원본APPROACH시간조건이열린후ENTRY/실제entrylatchEXIT는이전대로다. 학습0·연속목표active.

표기정정: 직전APPROACH plan/main의‘event1’은첫음표를뜻했으나rawindex는0이고afterstepindex1이다. 소비된원본은보존하고이기록에서명확히정정한다. [시간조건ENTRY계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1), [회복복원실제자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/analysis/summary.json:1).


## 2026-10-10 지속 작업: 대기 목표와 실제 최종 관절 목표의 불일치

시간조건ENTRY의완료재실행은firsttimelyhit1/physicaltarget2(두번째−63.511612ms premature)/첫회복완료2.366667/wrong4/miss6/terminal3.683333을기록했다. 1200physics151frames21checks1059closure변경0/49PREPARE172PLAY79HOLD/범위241/300(정책162/172)이다. 첫시도native는exit143/94frames/no finally로부분기록보존하며성공판정에사용하지않는다.

closedphase1 READY3 선택만으로는목표가실현되지않았다. R9 최종목표−actual각차0.417–0.711rad와FK예측pickGz−74.6…−103.7mm(READYreference20.3mm;미래측정아님)가policyabsolutegoal+boundedPI의제어권충돌을시사한다. 다음은closedwindow R9만기존RECOVER증분follower로READY를따라가게하며I유지/finger21policy/openphase1policy+PI/원본시간·검출·사용자범위는그대로다.

[대기제어권계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_PRIORITY_PLAN.md:1), [완료재실행자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/analysis_retry_v1/summary.json:1), [중단기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/interrupted_run.json:1). APP-only651artifact봉인/FK16artifact봉인완료·학습0·목표active. Fret35000대안은현재왼손7관절profile불일치로단순인계하지않고[선행설계](/home/ajou/yigyu/3/stability_adapter_2/FRET_TRANSFER_FEASIBILITY.md:1)에정리했다.


## 2026-10-10 지속 작업: 대기 시작에서 이전 목표를 물려받는 문제

waiting-priority는 first hit0@1.35와 scheduled recovery2.366667을 유지했으나 sourcewrong4/terminal2.983333이었다. 실제5초1200physics151frames21checks1063closure변경0/49PREPARE130PLAY121HOLD/hit1/physical1/accepted1/release5/miss3/범위235/300(정책120/130)/maxG8.126144deg이다. 대기 시작의previousactuatorgoal은이미READY와다른방향인데localδq를누적했지만추가cross가발생했다. 이조건은미채택이다.

다음은닫힌source창 R9 목표만 actual_angles+local_IK_delta로재계산한다. 실제각을읽어PD목표기준으로사용하며state쓰기는없다. I유지·finger21policy·열린phase1/phase0policy+PI·기존RECOVER증분/PDschedule/rate/bounds/source시간및검출·사용자범위는유지한다. [대기 목표 재계산 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1), [직전 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/analysis/summary.json:1). 학습0·지속목표active.


## 오른쪽 어깨 목표 전달 진단

대기 actual-angle IK 시험은 첫 타현/회복을 유지했으나 이후 연결에 실패했다. 큰 어깨 목표/실각 차이를 분리하기 위해 [POSITION 목표 펄스 계획](SHOULDER_POSITION_GOAL_PROBE_PLAN.md)을 진행한다. 동일 초기 상태에서 OFF와각 shoulder 축 +0.02rad 4physics-step 뒤 초기 목표 복귀, 각각 실제5초를 기록한다. 원본 PD/중력/충돌/기타범위는 유지한다. 동적 연성과 target 해석은 분리하며 아직 원인을 확정하지 않는다.


## 관절 토크·damping 전달 후속 진단 준비

[EFFORT damping 계획](HUMAN_EFFORT_DAMPING_PROBE_PLAN.md)의 신규 구현은 사전 검수를 통과했고 아직 실행하지 않았다. 현재 POSITION 어깨축 비교를 먼저 마친다. 그 결과에 따라 EFFORT에서 damping0/원래값 유지와 토크OFF/ON을 첫4physics-step만 비교하고 각각5초 녹화를 진행한다. Property readback만으로 damping 작동을 주장하지 않으며 원본 source의 POSITION+토크 방식은 CPU에서 동등성이 확인되지 않았다. 전체 originalPOSITION gain 복원 뒤 같은 +0.05rad 목표를 유지하는 기존 v2 재현 조건이다. 자유 기타·관절상태쓰기금지는 유지한다.


## POSITION 어깨축 실제 반응 검사 완료

OFF/x/y/z 네 환경 각각1200physics/151frames 및native target81 exact를 확인했다. 초기state/PD도조건간같다. +0.02rad 첫4steps의해당축실각변화는 x0.001144283/y0.001002938/z0.000881344rad이며다른축의반응도있다. 새상대bodyrotation검사의stateFK오차최대0.000018329deg다. 이것은현재초기자세의작은목표반응이며축교환/큰지속tracking오차의단독원인인증은아니다. 산출물/검수는D의shoulder_position_goal_probe_v1에진행중이다. 다음은사전검수PASS된EFFORT damping OFF/ON 네조건이다. 학습업데이트는0이며원본음악성공기준은바꾸지않는다.


## 명시적 spring/native damping Strike 연결 준비

EFFORT damping 네조건각1200physics/151frames를완료했다. damping0 OFF/ON은기존152상태씩exact재현했고damping유지에서도토크반응이검출됐다. 결과문서/최종검수는별도진행한다. 이짧은관측을기반으로 [R9명시적spring Strike계획](STRIKE_EFFORT_DAMPED_ARM_PLAN.md)을진행한다. 다른목표/원본성공기준/기타범위는유지하며R9만제어방식을바꾼실제5초실험으로검증한다. PREPARE그대로·native소유권/토크한계/상태보존을검수하고실행한다. 학습0,전체연주성공아직없음.


## 실제각 기준 기타 위치 feedback 비교 준비

R9 EFFORT 연결5초는원본적시타현0/wrong1/miss10이며기타최대46.354°회전으로자연범위를크게벗어나미채택이다. 다음 [기타기준R9 PI계획](STRIKE_EFFORT_GEOMETRY_PI_PLAN.md)은READY/열린APPROACH에서만 PI기준을policy각→실제각으로바꾼다. Actor30출력을계산하되R9는기록/손가락21은실제제어하며위치feedback이팔9주제어를맡는다. 대기/RECOVER·힘제출·모든source성공기준·기타범위는같다. 사전검수후같은초기값실제5초로검증하고학습은아직0이다.


## 지속 실험: native POSITION + 기타 기준 actual-angle PI

EFFORTgeometry 5초 타현1/기타44.868°/범위3/251로 미채택. 다음 actuator 비교 설계: [STRIKE_POSITION_GEOMETRY_PI_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_POSITION_GEOMETRY_PI_PLAN.md). 소스/평가/기타범위 변경 없이 팔 PD 방식만 비교한다.


## 손 방향 선호 비교

actual-angle POSITIONgeometry도5초 기타45.021°/타현0으로 미채택. 앞선 안정적인 POSITION policy+PI rebase를 기준으로 soft 손방향 residual 한 요인을 추가한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_SOFT_ORIENTATION_PLAN.md).


## Native 속도 좌표와 회전 spring 후보

Softorientation도5초 타현0/기타45.290°로 미채택. 같은 snapshot 속도는child-frame XML Bv가 body angularvelocity차이를 잘 재현한다. force등가는 미인증이며 다음은 humanR9 spring error 한 요인 비교다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_BODY_ROTATION_SPRING_PLAN.md).


## 피크를 잡지 않는 손가락 굽힘 비교

회전spring5초도타현0/기타46.986°로미채택. Source geometry는pick경로에body침투를요구하지않지만ringmesh가먼저body면쪽에있다. 이전POSITIONrebase를기준으로middle/ring네hinge만+.2targetresidual 비교. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_FREE_FINGER_CURL_PLAN.md).


## READY 위치 유지의 증분 목표 비교

손가락4개+.2rad 조건은 적시타현0/물리타현1(약227ms일찍)/기타최대9.230°로음악성공미달이다. 다음에는 같은손가락조건에서READY와닫힌APPROACH의팔9를이전제출목표+2δ로통일한다. 열린APPROACH정책+PI와RECOVER는유지한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_INCREMENTAL_PLAN.md).


## 위치 목표의 속도 감쇠 비교

READY증분제어는기타최대7.095°이지만약382ms조기타현/적시0이었다. 다음에는READY·닫힌APPROACH·RECOVER의IK목표에현재기타기준피크위치차분속도보정(0.1초,최대5mm)만추가한다. 열린APPROACH정책과원본평가기준유지. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_WAYPOINT_VELOCITY_PLAN.md).


## 타현 구간 팔 제어권 비교

속도감쇠5mm는READY성공1/원본scheduledREC2회로진전했지만적시타현0/조기physical2회였다. 다음은열린APPROACH의팔9만policy+PI에서기타기준이전목표+2δ로바꾼다. Actor팔9기록용/손가락21실제제어와기존4개보정·원본성공기준유지. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_INCREMENTAL_APPROACH_PLAN.md).


## Source 종료 후 오른손 회수

기타기준팔제어는적시hit4/scheduledREC4회로진전했다. PLAY기타회전약3–7°지만3.633초종료뒤ENTRY목표고정HOLD에서pinky접촉과G43.829°가기록됐다. 다음은PLAYprefix를보존하고HOLD에서팔9회수·baselinePD복원만비교한다. Sourceclock/history·나머지72목표는고정하며기타외력은없다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TERMINAL_RETRACT_PLAN.md).


## UP·줄변경의횡방향준비

종료회수조건은hit4/REC4를그대로보존하고G최대7.095°로유지했다. 다음은openAPPROACH에서READYxy오차>4mm이고ENTRY미도달일때READY높이에서횡방향먼저접근한다. Sourceclock/phase/detector·miss판정유지. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_LATERAL_STAGING_PLAN.md).


## 횡방향 준비 도달 기억 비교

Lateral staging은적시4/physical5/wrong2로5초PLAY지속이지만UP준비도달뒤READY↔ENTRY전환이반복됐다. 다음은4mm횡방향도달을event/phase단위adapterlatch로기억하며원본clock/detector/6mmENTRYlatch를유지한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_LATERAL_LATCH_PLAN.md). 학습0·지속목표active.


## 원본 회복 완료 뒤 현재 음표 준비

Lateral latch는4hit유지/wrong4종료로미채택. 다음은원본scheduledREC/필요clearance완료뒤에만cachednext와달라진현재event의READYxy로clearance고도를유지해팔9를옮긴다. Source기하·phase·clock·detector는읽기전용이며baseline은5초PLAY인lateralstaging이다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_POSTCLEARANCE_PRESTAGE_PLAN.md).


## 열린 횡방향 준비의 팔 감쇠 비교

회복후currentevent준비는잘못된타현1/5초PLAY/UP physical시간창내이나적시성공추가0이었다. source위치조건감사중이다. 다음은열린lateralstaging만R9native감쇠baseline,ENTRY/EXIT·closed창quarter와모든목표/원기준유지. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_STAGING_DAMPING_PLAN.md).


## 2초 준비와 에피소드 종료까지 녹화

사용자 요청으로 최소 준비 시간을2초로 설정하고 기존준비조건을함께유지한다. 이후 원본full-song done까지실제영상을저장하며 정상/실패/시간초과종료를구분한다. 기존5초실험과제어소스는보존한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TWO_SECOND_EPISODE_PLAN.md).


## 2초 준비의 진입 회전 경계 진단

v1은2초에실제허용회전과0.028954°차이지만Euler box밖으로준비타임아웃이었다. v2는진입판정에만원래허용회전으로부터0.1°여유를추가하고원래strict box도별도기록한다. 위치범위/손조건/2초최소시간/원본성공판정은유지한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TWO_SECOND_BOUNDARY_MARGIN_PLAN.md).


## 현재 체크포인트 연결 실험의 시간·영상 기준

최소 2초 준비 뒤 손·준비 위치와 현재 진입 조건을 확인한다. 현재 Strike 진입점은 `python -m stability_adapter_2.strike_two_second_episode_v2_preserved_run --mode trial --candidate <candidate> --right-rate 3.2 --out <새 경로>`다. 영상은 환경 시작부터 원본 에피소드 종료까지이며 고정 5초 제한이 없다. 실제 실행에서 2.00초 연결, 3.55초 잘못된 타현 4회에 의한 실패 종료, 적시 타현 1회를 확인했다. 원래 회전 범위의 strict 결과와 진입 0.1° 물리 여유를 구분한다. 연주 완주는 아직 실패다. [결과·전체영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md).

- [x] 2초 준비와 종료까지 녹화 구현·사전 검수·실제 실행
- [x] 초기값·종료 frame·정상/실패 원인·가변 영상 길이 저장
- [ ] 2초 준비 상태의 연주 전환 보정과 원본 음악 성능 개선


## 왼손 Fret native 연결 소단계

사용자 요청에 따라 frozen Jazz1 Fret30을 현재 자유 기타의 왼손에 연결한다. 2초 물리 준비 뒤 source frame0부터 시작하며 첫 done까지 녹화한다. 첫 시험은 오른손 준비 목표 유지로 Fret 영향을 분리한다. source profile은 정규화/목표 범위에 적용하고 native XML hard limit 유지 차이를 명시한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_NATIVE_CONNECTION_PLAN.md).

- [x] 계약 조사와 readonly/단일 제어권 구현
- [ ] 사전 검수·native 실행·결과 검수

Fret v1 setup은 checkpoint chair 자산 지문 차이로 물리 생성 전 차단됐다. v2는 자산/구현 차이를 기록하는 자유 기타 전이 시험이며 goal/hand/profile/model/ABI 검증은 유지한다. copied-native tensor 사전 검사10항목 통과. [v2 계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_NATIVE_CONNECTION_V2_PLAN.md).


## 왼손 Fret 연결 실제 결과 및 다음 소단계

원본 Jazz1 fret_035000(420/30/6)을 새 readonly native view에 연결했다. 오른팔12 bounded hold·오른손21 초기 목표를 유지한 독립 시험이며 Strike actor는 OFF다. 준비2.00초 후 source frame0부터46제어를 수행했고2.766667초에 index/ring finger_back 원본 조건으로 실패 종료했다. 운지0, 지속 성공0/2, 기타 초기 t=0 대비 최대434.475mm/68.336°로 안정화 실패다. 영상은 종료까지84 frame/2.8초이며 5초 cap과 terminal 후 HOLD를 사용하지 않는다.

native 실행15검사·후처리17검사 PASS, 실행 중1143입력 SHA 불변을 확인했다. 이는 연결·기록 검증이며 연주 성공이 아니다. 원본 chair/thigh proxy 자산 부재와 구현10파일 차이, source profile 목표/정규화 대비 native XML 물리 한계 차이를 initial_values에 기록했다. 과거 초기 grip의 source-profile 충돌은 목표만 점진 변경하고 실제 q는 보존했다. 이관 실제 q의 profile 최대 초과는0.095522rad다.

- [x] 30축 Fret 단독 소유 및 원본 synergy/EMA/실패 판정 연결
- [x] 2초 준비→원본 첫 done까지 실제 영상·초기값·원자료 저장
- [x] 초기/이관/종료 이미지 설명 및 영상 모음
- [ ] 현재 기타 기준 왼팔 접근/지지 보정과 손가락 정책 제어의 합성 설계·단독 재검증
- [ ] 왼손 운지와 자유 기타 유지 확인 후 양손 동시 연결

다음은 왼팔의 원본 절대 목표를 현재 기타 기준 접근·지지 목표와 비교하고, 손가락21 정책을 덮어쓰지 않는 제한 보정을 설계한다. 허용 기타 범위/운지 성공 기준/실패 판정의 완화로 성공을 만들지 않는다. 학습 업데이트는0이다. [결과·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/README.md) · [실행 소스](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v3.py:27).


## 왼팔 지지 목표 유지·손가락 Fret 분리 시험

사용자 승인에 따라 준비2초까지는 기존 실행과 동일하게 진행하고, PLAY에서는 LShoulder/Elbow/Wrist9의 마지막 제출 목표를 유지하며 LH21에만 Fret을 적용한다. 실제 팔/기타 상태는 고정하지 않는다. 원본 actor30 요청과 최종 제출 목표를 따로 기록한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_FINGERS_ARM_HOLD_PLAN.md).

- [ ] 구현 검수·native 실행·동일 준비 구간 비교·결과 검수


## 왼팔 목표 유지·손가락 Fret 분리 시험 결과

준비2초의120제어·native 상태61표본·양쪽 카메라61frame SHA가 이전 Fret30 시험과 정확히 같다. PLAY에서는 왼팔9의 준비 마지막 목표를 유지하고 LH21만 Fret 요청을 적용했다. 실제 관절과 기타는 자유 물리 상태이며 스트랩/Strike actor/학습 업데이트는OFF다.

같은2.766667초의 t=0 대비 기타 변화는 이전434.475mm/68.336°에서72.743mm/9.855°로 줄었다. 그러나 전체12.916667초 최대73.190mm/50.248°, 종료48.097mm/50.248°이며5~10초에도 약46°의 다른 회전에 머문다. 위치 이탈 개선을 초기 회전 유지 성공과 혼동하지 않는다.655정책제어 뒤 index finger_back 원본 실패로 종료했고 운지0%, 지속 성공0/27이다.

- [x] 손가락21/준비 팔9/지지15/초기36 제어권 분리와 사전 검수
- [x] native17검사·후처리23검사 PASS, 실행 중1148입력 불변
- [x] 시작~첫 원본 done까지389frame 영상·초기값·원자료 저장
- [ ] 현재 기타 기준 왼팔 접근·지지 보정을 제한된 목표 보정으로 합성해 운지 도달 개선

다음 소단계는 고정 준비 팔 목표와 현재 기타 기준 손목/운지 목표의 간격을 먼저 측정하고, 손가락21을 덮어쓰지 않는 왼팔9의 작은 목표 보정을 설계한다. 손바닥 지속 접촉을 강제하지 않는다. 완주/운지 기준과 원본 실패 판정은 유지한다. [결과·전체영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md) · [제어 합성](/home/ajou/yigyu/3/stability_adapter_2/fret_finger_target_ownership.py:5).


## 준비 팔 유지·Fret 손가락 제어의 스트랩 ON 비교

사용자 요청으로 직전 초기 자세·제어권·2초 준비를 유지하고 기존BASE의절대길이1.1018469719600776m 스트랩을 첫 물리step부터 적용한다. 길이/관절각/gain최적화는 이번 변수로 추가하지 않는다. native초기상태exact검사·수동장력기록·전신/양손실제route영상·첫 원본done·no-strap공통시간비교를 검증한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_FINGERS_STRAP_PLAN.md:1).

- [ ] 사전검수·native실행·비교분석·결과검수


## 고정 길이 스트랩 ON·Fret 손가락 비교 결과

직전과같은초기상태/2초준비/팔9목표유지/손가락21정책에BASE절대길이1.1018469719600776m·기존13점수동장력법칙만적용했다. 첫실행은마지막저장1.9초뒤exit139로중단했다. 동일소스·물리설정에Python faulthandler만켠재시험은원본검지finger_back실패까지완료했으며첫segfault원인은미확정이다.

완료시험은2초연결/103actor제어/892물리step/3.716667초/113frame(영상3.766667초),운지0%,지속성공0/4,목표완료false다. 장력양수는0.170833~0.195833초의7step뿐(최대32.365N),PLAY전구간0N이었다. 실제초기route1.073577m/최종적분직전0.967969m로rest보다짧아기존길이는현재자세에서지속지지를제공하지못했다.

같은2.766667초에는OFF72.743mm/9.855°→ON66.212mm/8.924°로작게줄었으나3.7초에는OFF24.473mm/47.569°→ON51.306mm/49.441°로악화됐다. ON전체최대69.082mm/51.500°,종료68.456mm/51.500°다. OFF12.916667초와ON3.716667초의전체값은같은길이비교가아니다. 현재길이적용의일관된안정화/운지개선은확인되지않았으며스트랩일반의불가능판정은아니다.

- [x] 사전9검사·native24검사·후처리26검사 PASS
- [x] 실행중1156입력불변·초기상태exact·240Hz수동장력기록
- [x] 스트랩표시전신·양손전체영상·첫crash부분영상보존
- [ ] 현재기타기준왼팔접근/지지보정으로운지도달개선

고정길이조건을유지하며길이최적화는하지않았다. 후속길이비교는현재자세route변화를검토해별도변수로진행한다. 기타poseservo/손부착/상태덮어쓰기/학습은추가하지않았다. [결과·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md:1).

## 전체 연구 방향 반영 — 2026-10-10

전체 연구에서는 정지 안정성을 중간 성과로 두고 **허용 범위 안의 자유 기타에서 실제 압현·타현 성공**을 목표로 한다. 초기 기타 p/q 대비 변화만으로 성공·실패를 결정하지 않는다. 범위 판정·음악 성공·관절/접촉 검증을 별도로 기록한다. 스트랩 ON/OFF는 비교 변수이며 현재 한 길이의 실패를 모든 스트랩 조건에 일반화하지 않는다.

형상·재질 개선은 넥 단면, 손바닥·손가락, 허벅지 접촉과 실제 적용 물리 설정부터 점검한다. 필요한 수정은 공용 원본을 보존한 별도 버전으로 진행하고 checkpoint/기준 성능 영향을 재검증한다. 피부·의복·목재 시각 표현은 별도 개선이다. 실제 줄 변형·타현 반력·음향 합성은 메인 범위에 추가하지 않는다.

다음은 현재 기타 기준 왼손 손목·목표 프렛의 오차와 접촉면을 시각화하는 소단계다. 원본 고정 기타 checkpoint 성능·전이 계약 차이도 확인한다. 측정 근거에 따라 손가락21 정책을 보존하는 왼팔9의 제한된 접근 보정을 설계하고 한 음 압현·유지를 평가한다. 준비 팔 목표를 영구 유지하거나 손바닥 지속 접촉을 강제하지 않는다. 단일 동작 → 이벤트 전환 → 짧은 구절 → 곡 순서로 확대한다.

- [x] 전체 연구 메인 계획에 목표·단계별 통과 조건·제어권·평가/비교군 반영.
- [ ] 다음 소단계 계획에 원본 성능 확인 범위, 목표 프렛/손목 좌표·단위·오차, native 접촉 진단과 시각화 출처를 명시.
- [ ] 접근 오차 시각화 후 제한된 팔 보정 OFF/ON으로 한 음의 압현·유지 검증.
- [ ] 한 번의 타현·이벤트 전환 검증 후 보정 학습 권한과 작은 pilot 설계.
- [ ] 짧은 구절·곡 통합에서 음악·허용 범위·자연스러움·물리 상태를 함께 평가.

현재 root/하체 고정·몸통 PD 목표 유지·Thorax 이하66관절 권한·자유 기타 조건을 유지한다. 제어권·보정 제한과 최종 목표/history 계약 검증 뒤 학습 구조를 결정한다. 체크포인트 시험은 최소2초 준비 후 원본 첫 done까지 시작부터 녹화하며 실패·부분 기록을 완주로 표시하지 않는다. 이번 반영은 문서 변경이고 물리 실행·자산 변경·학습 업데이트는 없다. [변경 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/research_direction_update_v1/README.md:1).

## 현재 소단계: 연주 자세·목표 오차 진단 (2026-10-10)

- [x] 저장 native 실행의 시간/좌표/420D 목표 ABI 조사 및 [세부 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_POSTURE_DIAGNOSTIC_PLAN.md:1) 작성.
- [x] 기존 스트랩 ON 재실행에서 기타 넥/앞판/몸통 상대 배치·양팔 관절 여유·현재 프렛 목표를 함께 표시.
- [x] 수학/시간 정합 및 입력 보존 검증, 실제 native 원본과 PNG 대조. 의미 검증6개·문법 검사 통과,113표본의 최대 네 손끝 정합 오차7.797e−8m.
- [x] 결과 문서·독립 검수·변경 색인 및 최종 봉인. [이미지·설명과 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/README.md:1), [변경 파일·실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/FILE_INDEX.md:1).

이번 단위는 저장 자료 후처리이며 새 물리 실행·제어·학습은 없다. 자연스러운 자세의 선호 문턱은 아직 설정하지 않고 사용자 허용 범위를 유지한다.

## 팀원 자세 판정표 시각화 (2026-10-10)

- [x] 원자료 보존 및 [표시 계획](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VISUALIZATION_PLAN.md:1) 작성. 현재 설정·허용범위 변경 없음.
- [x] 바디 중심 위치 후보·회전 분리 구간의 개념도와96개 판정 표본 그림 생성. 범례 겹침을 수정한 별도 v2가 최종 그림이며 첫 producer/산출물은 보존했다.
- [x] 원자료/PNG 정합·입력보존·독립 검수·이미지 설명 및 변경 색인 기록.

## 팀원 자세 후보의 현재 환경 적용 검증 (2026-10-10)

- [x] 원본 재현 입력 누락과 재구성 가정을 명시한 [검증 계획](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VALIDATION_PLAN.md:1) 작성.
- [x] 현재 기준/보고 기준/중앙 후보 native 배치·원본 형상 검사와 가능 조건의5초 자유 기타 측정.
- [x] 초기값·실제 영상/이미지·설명·독립 검수와 변경 색인 기록.

세 번의 독립 native 실행을 완료했다. 각 실행은 1,200 step/5초이며 전신·손 카메라가 각각 151 frame을 저장했다. 같은 humanoid 초기각·무스트랩·기존 팔24 PI에서 현재 수평 배치는 30Hz 저장 표본 최대 62.438mm/15.540°, 종료 34.364mm/4.620°였고, 2초 대비 후기 최대 변화는 1.852mm/0.298°였다. 보고 기준·중앙을 재구성한 배치는 왼손 raw contact가 관측되지 않았다. 각각 0.8833/0.5875초에 G:body–ground 접촉 후 낙하했으며 표본 최대 변화는 1381.178mm/122.985°, 1306.791mm/154.357°였다. 후기 정지는 연주 위치 유지와 구별한다.

초기 원본 convex 기타–인체/의자 교집합은 0건이며 실제 native 초기q·한계·Pelvis/bodycenter readback도 세 조건 모두 통과했다. 이것은 cooked 관통·자연스러움·연주 성공 인증이 아니다. 원 팀원 초기각·p/q·pivot·041000 run 식별이 없어 현재 각도에 좌표 가정을 적용한 전이 진단이다. 원 판정의 반증이나 6축 영역 전체 검증으로 확대하지 않는다. 기존 허용범위는 유지한다. 다음은 원본 입력을 확보·대조하고 기타 후보와 왼손 초기각을 함께 설정하는 작은 배치 시험이다. [결과·이미지·전체5초영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/README.md:1).

## 사용자·팀원 범위의 실제 장면 비교 (2026-10-10)

- [x] 좌표 변환·무물리·표시 의미를 명시한 [비교 계획](/home/ajou/yigyu/3/stability_adapter_2/ENVELOPE_NATIVE_COMPARISON_PLAN.md:1) 작성.
- [x] 세 자세의 정면/측면 native 렌더와 두 위치 범위·바디 중심·넥 방향 표시.
- [x] 실제 상태·입력 보존·이미지 설명·독립 검수와 변경 색인 기록.

새 Isaac Gym 정적 환경을 세 개 생성하여 초기값을 읽고 적분 없이 정면/측면을 렌더했다. physics step0/학습0, native 상태 exact 대조·렌더 전후 불변·입력SHA 검사를 통과했다. 파랑은 각 실제 회전에 종속된 바디 중심 위치범위이고 노랑은 현재 Pelvis로 옮긴 팀원 바디 중심 후보여서 단순 포함 관계가 아니다. 현재/보고 기준 회전은 사용자 회전범위 안, 중앙 조합은 밖이다. 세 점 판정이며 전체6축 조합·접촉·동적 유지 인증이 아니다. [실제 장면·설명·파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/README.md:1).


## 바디 중심 기준의 화면·수치표 (2026-10-11)

- [x] 기존 제어 경계를 유지하는 [표시 계획](/home/ajou/yigyu/3/stability_adapter_2/BODY_CENTER_VIEW_PLAN.md:1) 작성.
- [x] 공용 양방향 좌표 변환과 실제 세 자세의 body-center 수치표·6이미지 생성.
- [x] 변환·표시·입력 보존 검증, 독립 검수와 결과 설명·파일 색인.

표시용 body-center local[0,-.4,-.0217]m를 기존 native 값과 대조하고 world↔actor-root 변환 helper 및 Pelvis RFU 표시를 추가했다. 바디 중심은 질량 중심이 아니다. 원점 marker를 제외한 정면/측면6PNG와3자세 수치표는 저장된 Isaac Gym t0 이미지 후처리이며 새native/physics/학습0회다. 수평 기타에서 사용자 바디 중심 범위는 골반 기준 오른쪽[-10,25]cm/앞[0.83,30.83]cm/위[5.80,29.17]cm다. 실제 중심은 오른쪽16.9585/앞24.5012/위10.8973cm다. 모든 회전의 공통 고정 box가 아니며 기존 actor-root/회전 경계는 유지한다. helper는 기존 runner에 아직 연결하지 않았다. 이후 표시·결과표는 이 기준점/RFU와 해당 q를 명시하고 내부 명령은 역변환한다. [그림·전체 표·파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/README.md:1).


## 사용자·팀원 범위 나란히 표시 (2026-10-11)

- [x] 같은수평q·동일native장면 비교 [계획](/home/ajou/yigyu/3/stability_adapter_2/BODY_CENTER_SIDE_BY_SIDE_PLAN.md:1) 작성.
- [x] 정면·측면 각각 사용자/팀원 범위 단독 두panel 그림 및 수치·보존 검증.
- [x] 독립 검수·설명·파일색인 기록.

같은 수평 기타의 저장 native프레임을 양쪽에 배치해 하늘색 사용자/노란 팀원 위치box를 분리표시했다. 정면·측면 각각의 좌우에 같은카메라·crop·배율을 적용하고 RFU범위/폭/동일실제중심을 기록했다. body-center영역 확대이므로 측면의 머리 상단은 일부crop된다. 이회전의 조건부 위치비교이며 새native/physics/학습0,기존경계·제어·과거원본은유지한다. [두panel이미지·설명·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/README.md:1).

## 현재 기타 기준 Fret 실시간 진단 (2026-10-11)

- [x] 기존 무스트랩 baseline의 제어를 유지하는 [진단 계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_LIVE_DIAGNOSTIC_PLAN.md:1) 작성.
- [ ] 좌표·시간 정렬·읽기 전용 검사와 사전검수.
- [ ] 준비2초~첫 source done 전체 실행·바디 중심/위치범위/현재 목표/실제 접촉 표시.
- [ ] baseline 제어 비교·실패 원인 분석·영상·독립 검토·보존 봉인.

이번에는 보정 제어를 추가하지 않는다. 위치box 이탈과 초기 대비 회전/넥 고도는 별도 측정하며 전체 회전 허용집합 판정은 보류한다.

현재기타 Fret 진단 v1과 동일재시험은 native 카메라 파일저장 호출에서 각각0.866667/0.833333초 마지막완전frame 뒤 exit139로 중단했다. 물리평형/목표종료가 아니며 원인은 미확정이다. 입력 불변 대조 및 두partial영상/로그를 보존했다. [v2 계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_LIVE_DIAGNOSTIC_V2_PLAN.md:1)에 따라 같은native RGBA를 복사한 뒤 외부 PNG저장으로 변경하고 물리·제어·진단은 유지한다.

v2도1.0초 마지막완전frame 뒤 native `get_camera_image`에서 exit139로 중단했다. 파일writer만의문제로 확정할수없으며 원인미확정·fresh full 진단 미완료다. [저장전체실행 진단 계획](/home/ajou/yigyu/3/stability_adapter_2/SAVED_FRET_DIAGNOSTIC_PLAN.md:1)에 따라 이전완료된 실제389frame/12.916667초의 native영상·trace·checkpoint 관측을 같은step으로 맞춰 분석/전체표시영상을 생성한다. 준비목표는 미측정, 마지막접촉은 미측정, 선은depth없는투시표시다. 새physics/제어변경/학습 없이 원본과실패부분영상은보존한다.

## 저장 전체 Fret 기록의 진단 완료 (2026-10-11)

- [x] 실시간관측 구현·좌표/목표할당5검사·사전검수. fresh시험3개는native camera API crash로 full live 미완료이며 전부보존.
- [x] 기존완료native389frame/3100step/12.916667초를 새physics 없이 전신/양손전체진단영상으로 생성.
- [x] 10후처리검사PASS: 동일step/손끝1µm이하정렬·동일고정camera sourceSHA·공통prefix31frame×2view RGBA exact·입력불변.
- [x] 독립결과검토·설명/색인·최종보존봉인.

원본제어는준비2초/왼팔9마지막목표유지/손가락21Fret/스트랩OFF다. 2초손목목표벡터155.197mm·약지marker87.617mm, 8초다른goal의약지46.73mm, 전체손목벡터155.197~221.632mm다. 같은goal의오차감소로해석하지않는다. 사용자위치box밖53/389표본·최대15.005mm(2.7초worldZ하한이탈), 초기대비최대회전50.248°다. 전체회전집합/자연스러움/관통안전판정은하지않았다. 원본은검지finger_back 실패·지속0/27·episode_success=false다.

현재기타를따라목표를갱신해도고정왼팔목표로는접근이부족하다. 다음에는native camera 반복조회오류를해결한뒤왼팔9의현재기타손목/프렛접근목표보정OFF/ON을비교하고손가락21정책의제어권은유지한다. 손바닥지속접촉을강제하지않는다. [전체영상·분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/README.md:1).

## 현재 기타 기준 왼팔9 보정 구현·비교 완료 (2026-10-11)

- [x] 손가락21 Fret 정책·단일 최종 PD 목표·실제 제출값 history·원본 첫done를 유지하는 왼팔9 보정 구현/독립 검수.
- [x] raw COLOR만 복사하는 native camera로 fresh OFF 전체12.916667초/389frame. 기존baseline 제출목표/정책출력/sourceinfo/전체native상태 exact.
- [x] v1 직접source wrist anchor 추종 ON 전체5.633333초/170frame. 같은218goal/time 손목오차 평균14.861mm·258marker 평균19.359mm 감소했지만 공통구간 기타최대이동73.190→267.200mm·box초과171.025mm·검지finger_back실패. 안정화 개선 아님.
- [x] v2 준비2초 실제 손목–기타 관계 추종, 준비목표±0.1/초기목표±0.3/native·0.3rad/s. ON 전체11.133333초/335frame, 원본wrong_press실패·압현성공0%·지속0/21·goalfinished/episode_success=false.
- [x] 같은11.133333초 최대회전47.863→19.408°로 감소, 최대이동73.190→126.888mm·box초과68.363mm로 악화. 같은post2초 상대손목오차 평균52.902→49.746mm/최대62.413→55.841mm로 소폭 감소. 같은548goal/time source손목오차 평균3.354mm·646marker32.480mm 증가. 압현/자연스러움/전체회전집합 인증 아님.
- [x] v1 원 분석의 helper/ABI/BASE/폰트 보존누락을 새verified경로의 실행전1899입력SHA로 보완. v2는실행전2229입력SHA로 분석. 원본분석은보존, 분석16검사PASS, 학습0.
- [ ] 허용위치box 밖에서는 지지목표가 떨어지는 기타를 계속 따라가지 않도록, 현재기타 기준 추종과 범위복원 목표를 분리해 제한된 팔 보정 비교.
- [ ] 준비자세의 wrist_G=[0.060837,-0.021318,-0.100343]와 첫source목표=[0.075,0.112313,-0.0227]의155.2mm 간격(주로넥방향/앞뒤)을 줄이는 연주 준비자세 검토. 준비 마지막 목표의FK손목과실제손목도114.85mm 달라 free-space 역기구학만으로 접촉 중 움직임을 보증할 수 없다.

손목추종과기타안정화는별도목표다. 단순추종만으로기타를허용범위에복원하거나압현하는것은확인되지않았다. 다음에는현재기타의허용범위이탈과연주준비오차를각각측정하고목표각수준에서작게보정하며, 손가락21제어권·팔보정의우선순위와합성은하나의PD명령으로유지한다. 기타고정/추가힘/상태덮어쓰기/손부착/손바닥지속접촉을추가하지않는다. 회전감소만으로범위안정화성공을판정하지않는다.

[직접 접근 비교·전체영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/README.md:1) · [지지 관계 추종·전체영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/README.md:1) · [v2 제어](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_support_v2.py:7).


## 손바닥·엄지 지지 소단계 완료 (2026-10-11)

- [x] 기존 자세 보존, 왼팔·엄지·손가락 초기각의 source 접근 탐색과 겹침 검사.
- [x] 기존 / 초기 자세만 변경 / 접촉점 추종 / 자세 유지+접촉점 추종의 실제 Isaac Gym 5초 비교.
- [x] 초기값·양손/전신 영상·접촉 원자료·네 조건 분석 및 입력 보존 검사 기록.
- [ ] 현재 기타 추종과 허용범위 복원 목표를 분리하고, 연주 준비 오차와 제어권을 함께 설계한 다음 비교.

선택 자세는 기준 대비 최대0.019987315rad(약1.145°)의 초기 관절각 변경이다. 자유 기타·무스트랩·root/하체 고정·몸통 PD 유지·self-collision 조건에서 손바닥/엄지의 동시 양의 raw solver 응답은 기존0%→초기 자세만22%→접촉점 추종73.67%→자세 유지 결합44.33%였다. 하지만 최대 actor-root 이동/초기 대비 회전은 각각62.96mm/13.63°,62.80mm/13.70°,96.22mm/16.24°,63.30mm/13.76°로 안정화 개선은 확인되지 않았다. 마지막 조건은 기존과 거의 같은 수준이다. 접촉 증가가 악화의 원인이라는 인과 결론은 내리지 않는다.

위 최대값은30Hz 자세 표본, 접촉 비율은60Hz 제어직전300표본이다. 접촉 pair/raw lambda는 정확한 면·뉴턴 힘·미끄럼 없는 지속 지지를 증명하지 않는다. 기존 world actor-root 위치box와 초기 대비 회전을 측정했으며 팀원 body-center 허용범위나 전체 자연스러운 회전집합은 이번에 인증하지 않았다. 준비 안정화 개선을 요구한 소단계 Fret 연결 gate는false로, checkpoint 실행/학습은0회다. 이 gate는 이번 후보 채택 조건이며 자연스러운 연주의 최종 성공 기준을 새로 엄격하게 바꾼 것이 아니다.

다음 설계는 기타가 허용범위 안에 있을 때 작은 흔들림을 따라가는 지지 목표와, 밖으로 나갈 때 복원하려는 목표를 분리한다. 손바닥·엄지를 계속 같은 지점에 강제로 붙이지 않는다. Fret21손가락(엄지5 포함)과 안정화17관절의 중복 제어권은 정책 목표에 제한된 잔차를 더하는 단일 최종 PD 목표로 먼저 설계해야 한다. 이번 초기각 기준 엄지 제어기를 그대로 Fret과 동시에 쓰는 것은 구현하지 않았다. 운지 목표와 준비 손목의 기존155mm 오차도 별도 해결 대상이다.

실행8회 중 카메라SIGSEGV3회는 부분 기록으로 보존했고,5초 완료5회 중 실행 중 분석기 수정으로 입력SHA가 실패한 baseline_v3는 비교에서 제외했다. 정식 네 조건은 모두 입력 불변·1200물리step·151frame·native 제약 검사를 통과했다. 기타 고정/추가 힘/손부착/시작 후 pose 덮어쓰기는 없다.

[실험 결과·이미지·전체 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/README.md:1) · [제어 합성](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_posture_support_v1.py:37).


## 왼손 공동 학습 정책 설계 제안 (2026-10-11)

현재 권장 후보는 왼쪽 Thorax부터 손가락까지 33관절이 지지와 압현을 함께 학습하는 정책이다. 기존 Fret 동결+잔차는 비교 조건으로 남긴다. 앞서 기록한 17관절 지지 보정과 Fret의 엄지 제어를 동시에 적용하지 않는다. 양팔·양손 66관절을 사용하는 최종 범위는 유지한다.

Actor와 Critic은 각각 두 층의 256-unit ELU MLP로 시작하는 제안이다. Actor는 33차원 관절 목표 행동, Critic은 가치 1개를 출력하며 PPO를 후보로 둔다. 관측 차원은 아직 확정하지 않았다. 전체 native81 실제 관절 상태, 현재 기타 기준 손 관계, 음악 이벤트와 압현 유지 상태, 양측 접촉과 측정 마스크를 입력 후보로 정의했다. 관절 한계와 변화율 제한을 거친 왼손33 목표를 held48 목표와 합쳐 81D PD 명령으로 한 번 제출한다.

기타가 허용범위 안에 있으면 초기점 복원 비용은 0으로 두고, 압현 유지·해제·전환과 경계 이탈/복귀를 함께 평가한다. 지속적인 손바닥 접촉은 요구하지 않는다. 첫 비교는 자유 기타·무스트랩·root/하체 고정·몸통 목표 유지 조건이며 실제 몸통/오른팔 움직임을 관측한다. 네트워크 크기·PPO·보상 가중치의 효과는 검증 전이다.

- [x] 관측·행동·네트워크·제어권·평가와 체크포인트 활용 조건을 설계 문서로 분리.
- [ ] 관측 manifest와 회전 허용집합 판정을 CPU에서 구현·검증.
- [ ] 네트워크와 단일 PD 제출 구현 후, 무학습 행동의 실제 5초 시험.
- [ ] 자원과 음악 clock/종료 계약을 확정한 뒤 한 압현 조건의 짧은 PPO pilot.

이번 단계는 문서와 설계 그림 작성이며 새로운 물리 실행·학습·환경 설정 변경은 없다. [설계 원문](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:1) · [그림과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/README.md:1).


### 왼손 공동 정책 문서 단계 마감

- [x] 설계 원문·그림·설명·메인 연결·실제 행 색인 대조 완료.
- [x] 독립 검수 완료: Critical/Warning/Suggestion 없음. 물리 성능·학습 성공 검증과 구분.
- [x] 기존 11,498개 코드/legacy/직전 실험 파일 보존 확인, 네 메인 안내 문서는 기존 내용 뒤에만 추가.

관측 구현·네트워크 구현·학습은 후속 단계로 남긴다. 동결 초안의 문서 마감 체크박스는 원문 보존을 위해 수정하지 않고 이 기록으로 완료를 추적한다. [검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/review.md:1) · [보존·문서 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/final_verification.json).


## 전체 상체81·512→256 설계 정정 (2026-10-11)

사용자 정정에 따라 StabilityAdapter의 행동 범위는 하체를 제외한 전체 상체81관절이다. Torso/Spine/Chest9, Neck/Head6, 왼쪽33, 오른쪽33을 하나의 Actor가 제어한다. root와 하체는 fixed-lower를 유지한다. 이전 왼손33 pilot·held48·최종66 확장 제안은 이 버전으로 대체하되 이력은 보존한다. 몸통·목/머리의 작은 움직임은 soft 자세 선호와 변화율 비용으로 유도하며, 별도 고정 목표 채널을 남기지 않는다.

Actor는 관측D→512ELU→256ELU→평균81, 별도 Critic은 D→512ELU→256ELU→value1로 설계한다. 프로젝트 Fret/Strike의 fusion MLP도512→256을 사용한다. 관측 차원·학습 설정·속도 한도는 구현 전 미정이며 PPO는 후보다. 출력은 native 한계/rate 제한을 거쳐 단일81D PD 목표로 제출한다. 전체 제어권을 유지한 채 음악 과제 난이도를 압현부터 양손 연주까지 올린다.

- [x] 저장된 native81 이름/순서 및 기존 모델 은닉층 확인.
- [x] 새 설계에 상체 전체 제어권과512→256 기록.
- [ ] 관측·행동 manifest와 회전 허용집합 구현/검증.
- [ ] 네트워크·단일PD 제출 구현 및 실제 행동 시험, 이후 짧은 PPO pilot.

이번 작업은 설계 문서 정정이며 새 물리 실행·학습·gain/자산 변경은 없다. [v2 상세 설계](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:1) · [그림과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/README.md:1).


### 전체 상체v2 문서 단계 마감

- [x] 상체81 제어권·512→256 원문/그림/설명 대조와 독립 검수 완료. Critical/Warning/Suggestion 없음.
- [x] 기존11,522개 파일 보존 확인, 네 메인 문서 기존 내용 뒤에만 기록 추가.
- [x] README 원문행 표기64–76→64–73 한 곳 정정, 수정 전 설명과SHA 보존.

설계 원문은 동결했으며 문서 마감 체크박스는 이 기록으로 완료를 추적한다. 구현·행동 시험·학습은 후속 단계다. [변경 파일](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/CHANGED_FILES.md:1) · [검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/review.md:1) · [보존·문서 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/final_verification.json).


## 부위별 움직임·보상 후보 v3.1 (2026-10-11)

전체81관절 Actor/Critic512→256 설계를 유지한다. 고정root/하체는 행동/움직임보상에서 제외한다. 몸통9 목표는 native∩초기기준±5°의 최초후보로 정하며 실제q±2°/Chest상대각3° 내는 자세비용0이다. 목표한도는 실제각보장/강제고정이 아니다. Neck/Head는 약한시선선호, 양측Thorax~손가락66은native범위와 음악/안정화목표로 움직인다. 많이움직이는자체를보상하거나 팔/손을초기각으로복원하지 않는다.

연속초당계수후보는 압현유지+2.00·접근정렬+0.50·타현경로+0.25·머리시선+0.01, 기타이탈−2.00·몸통자세−0.30·몸통속도−0.05·오압현−1.00·비허용접촉−0.20·native한계접근−0.05·목표변화−0.01이다. 무차원품질/비용을먼저계산하고Δt를곱한다. 완료/해제+0.50·인정타현+1.00·오타현/누락−1.00은고유이벤트에1회이며Δt를곱하지 않는다. 원본source총보상을다시더하지 않는다.

- [x] 움직임/보상/단위/마스크·완료/해제/crossing이벤트후킹조건 구체화.
- [x] 26개순수수식·합성계약검사와 저장native81에서후보한계계산. 실제reward/detector구현시험과구분.
- [ ] native신호/시선축/비허용접촉목록·회전허용집합 구현검증.
- [ ] 부위별한계/탐색분포·실제5초행동시험, 종료horizon계약과보상분포검사뒤PPO pilot.

최초v3수식검사입력을보존하고 v3.1에서이벤트후킹과world시선좌표를정정했다. 새환경변경/물리/학습0이다. [최신보상설계](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:12) · [수식검사/함수그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/README.md:1).


### 움직임·보상v3.1 문서 단계 마감

- [x] 부위별범위/보상식·26합성검사·293함수표본·이미지/설명·실제행색인 대조 완료.
- [x] 독립검수 완료: Critical/Warning/Suggestion 없음. 실제신호/물리/학습인증과구분.
- [x] 기존11,549개파일 보존 확인, main네개 원문뒤기록추가. v3초안/첫검사입력·출력도보존.

동결원문의문서마감체크박스는이기록으로완료를추적한다. 보상구현/신호매핑/행동시험/학습은후속단계다. [변경파일과실제행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/CHANGED_FILES.md:1) · [독립검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/review.md:1) · [보존·문서검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/final_verification.json).


## 현행 보상 정리 v4 — 프로젝트 계획 대조 (2026-10-11)

[보상 설계 v4](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:14)가 v3.1의 집계/음악 의미/종료 제안에 우선한다. 상체81·Actor/Critic512→256·고정root/하체·몸통9의 작은 목표/실제움직임 선호·Thorax~손가락66 native 권한은 유지한다. 과거 master_plan의66권한/residual/몸통목표유지 문구는 해당 당시 조건이며 최신 전체상체 설계를 축소하지 않는다.

1차는 실제 crossing 시 sounding fret/readiness와 원본 인정 hit·고유 wrong crossing이다. 유지/필요한 해제/간섭·early release/gesture·timing은2차 음악 예산, 접근/자세/약한시선은3차 예산으로 분리한다. 전체2·3차 폭0.450·β는 최소1차 검사점/required hit 손실4/m_max보다 작도록 고정한다. 이 비교는 다른1차/기타 비용이 같은 undiscounted 경우이며 PPO 전역 최적성을 보장하지 않는다.

기타 내부 비용0/외부 거리 비용을 유지하고 학습용 cap과 raw 이탈 로그를 분리한다. 긴 hold는 eligible 길이로 정규화하고, 유효 프렛/현 내부 접근 plateau·개방현/REST·무해한 추가압현·실제crossing 시각 판정을 명시했다. 원본 assigned-finger 지표/teacher/source 종료 계약은 보존한다.

- [x] 프로젝트 계획8개 이상 대조·3계층 수식·고정 분모/예산·음악 의미 정리.
- [x] 42개 합성 산술 검사 pass. 실제 detector/geometry/tracker/PPO 시험과 구분.
- [ ] sounding-state/현재G/SO(3)/시선·접촉·시간 신호 및 행동 제약의 native 매핑.
- [ ] fatal M_cross 상한·최악잔여 예산·γ/ledger/종료 계약 봉인. 미확정이면 pilot 금지.
- [ ] 무학습5초 행동/짧은 이벤트, 항별분포 확인 후 paired PPO pilot.

새환경변경·물리실행·학습0. 이전 leaf/실험은 보존한다. 결과 문서·비교 이미지·독립 검수·실제 줄 색인은 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/`에 저장한다.


### 보상 정리 v4 문서 단계 마감

- [x] 프로젝트 계획 대조·42합성 산술 검사·320예산 꼭짓점·수식 비교 이미지/설명·독립 검수 완료. 실제 detector/physics/PPO 시험과 구분.
- [x] 11,756개 기존파일 보존 확인, 네 main 원문 뒤 추가 기록. 이전 그림/설명/producer도 발표 SHA와 exact 대조해 보존.
- [x] 정음 하한/실패 상한·β=1/N_F=1 표기 정정 후 원자료·최종 이미지 대조 완료.

동결 leaf의 마감 체크박스는 이 완료 기록으로 추적한다. [설명·비교 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/README.md:1) · [변경 파일/실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/CHANGED_FILES.md:1) · [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/review.md:1). 보상 환경 연결·SO(3)/sounding-state·종료 계약·native 행동 시험·학습은 후속 단계다.


### v4 보상 학습 유인 감사 완료 — 구현 준비와 구분

- [x] v4 및 원본 음악 판정/PPO 소스 대조, 합성 수치와 actual source CPU 유지 tracker 검사.
- [x] 동일54/60 유지율의 최장dropout1/6을 원본이 성공/실패로 구별함을 재현.
- [x] 예산 거래·곡 길이 희석·60Hz 가정 할인·기타 cap 비교, 설명 이미지와 독립 검수.
- [ ] 후속 구현: 판정/시간/종료 계약표 → 유지 반례를 닫는 v5 후보 → native 항별 신호 → 짧은 paired PPO.

판단은 **구조는 좋지만 필수 유지의 학습 유인·할인/ledger·실제 음악/안전 신호 연결은 미완료**다.1차 hit 보호식이2차 유지 대3차 자세/접근의 우선순위까지 보장하지 않으며, 원본 유지 평가와 평균 U가 다른 실패를 구별할 수 있다. 보상 항 추가보다 계약/반례 정리를 먼저 한다. 기존 v4·가중치·환경 변경0, 새 물리/학습0.

[감사 계획](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4_PLAN.md:1) · [감사 보고서](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:1) · [결과·그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/README.md:1). 동결 계획의 체크 완료는 이 기록으로 추적한다.


### 물리 환경 기본층 v1 완료 — 상체81·초기화·관측·단일 제어권

- [x] 저장 candidate_1의 기타 p/q·상체81 q와 native POSITION PD를 새 장면에 재현한다. root/하체/의자 fixed, 기타 free, 스트랩 OFF.
- [x] 물리 원시 상태와548D 기반 관측을 구분하고 G 상대 위치/속도·회전6D·직전 최종 목표·동결 기준·시간 manifest를 저장한다.
- [x] 상체81 단일 목표 소유권, 몸통9 native∩초기±5°, 부위별 목표 rate,60Hz 제어/240Hz 물리, 준비2초 clock을 구현한다.
- [x] CPU9 검사와 neutral/small_motion 각각 새 Isaac Gym native5초 실행을 완료한다. 각1200 physics/300 control/301 상태·관측/151프레임×2view; native initial exact·readback/rate/finite/fixed state·금지 호출 없음·입력 보존 확인.
- [ ] 초기 지지 보정: 초기 실제 q와 하중을 지탱할 PD 목표를 별도로 교정한다. neutral에서도 기타 최대111.790mm/19.486° 이탈, 작은 목표 움직임은113.778mm/19.888° 이탈한다. 기존 위치 box 밖 표본은 두 조건 모두288/301이다. 현재 배치는 안정성 성공으로 채택하지 않는다.
- [ ] 음악 canonical event·유효 압현/sounding fret·crossing/hit/dropout/rearm·SO(3) 허용 집합·종료/ledger 계약을 연결한 뒤 최종 Actor 입력D와 reward/학습 API를 확정한다. GPU 벡터 reset과 PPO는 미구현이다.

[초기·상태·제어 계약](/home/ajou/yigyu/3/stability_adapter_2/ENVIRONMENT_FOUNDATION_V1.md:13) · [548D 계약 코드](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:106) · [현재 native 실행층v2](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:11) · [결과·이미지·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/README.md:1).

보상 없는 물리 기본층이며 최종 음악 학습 환경 완성이나 학습 성공이 아니다.5초는 관찰 시험 길이이고 음악 horizon을 제한하지 않는다. 몸통/머리/팔/손가락 목표 변화율은 실제 q 변화율 제한이 아니다. 접촉은60Hz 표본의 native body-pair raw 정보로 넥 pad 지지·관통 없음·접촉력N 인증과 구분한다. guard v1/scene v1/runner v1은 소비 이력 보존, 현재는guard v2/scene v2/runner v2와공통contract v1이다. leaf 계획의 완료 체크는 이 main 기록으로 추적한다.


### 양손 연결 필수 요구 — 2026-10-12

- [x] 새 환경의 최종 학습/평가에 Fret와 Strike를 모두 포함하도록 명시한다. 단독 시험은 진단용이며 양손 연주 성공으로 대신하지 않는다.
- [x] 단일 자유 기타 장면·준비2초 후 단일 score clock·상체81 단일 제출자·crossing 시 압현 공동 평가와 기존 checkpoint 동결쌍 비교를 기록한다.
- [x] 원본 canonical compiler로02_Jazz1-200-B_solo의42개 event/60Hz를 CPU에서 검증한다. 입력 SHA 불변 확인.
- [ ] 현재 물리 기본층에 실제 양손 목표/관측/detector/ledger와 checkpoint 비교 경로를 구현·검증한다. 초기 지지 보정과 음악 horizon 연결이 선행 작업이며 현재 runtime 연결은 미완료다.

[양손 연결 요구·구현 순서](/home/ajou/yigyu/3/stability_adapter_2/DUAL_MUSIC_CONNECTION_SCOPE_V1.md:13) · [입력 검사/설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_connection_scope_v1/README.md:1). 공동 정책은 상체81/512→256을 유지한다. 기존 Fret/Strike는 동일 곡/ABI/소유권 검증 후 동결 비교/유효한 교사 후보로 사용하며 가중치를 자동 이식하지 않는다. 이번 정리는 물리/추론/학습 실행0이다.


### 양손 음악 runtime 1차 구현 결과 — 2026-10-12

- [x] 소비된 leaf 계획 DUAL_MUSIC_IMPLEMENTATION_V1.md의 초기 지지 목표 보정을 별도 실행한다. 초기 실제 q/기타 p·q는 reference와 exact, gain·body/head 목표·root/하체·스트랩OFF 유지. median 실제각 오차를 이용한 arm±0.15/finger±0.05rad 정적 PD 요청이며 상태 덮어쓰기가 아니다.
- [x] 기존 neutral0을 재사용하고 preload0.5/1.0을 각각 native5초 실행한다. 최대 이동111.790→75.331→46.306mm, 최대 회전19.486→13.910→9.179°. core 위치 상자 최대 초과34.335→11.262→0mm. 최소 최대 초과량 기준으로1.0을 선택했으며 SO(3)/접촉/장기 안정 인증은 아니다.
- [x] PREP2초/60Hz score/240Hz 물리를 공통 시계에 연결한다. source별 tensor-only 목표 요청/후처리/evaluator만 사용하고, 하나의 owner가81 목표를 한 번 제출한 뒤4물리 tick을 진행한다.
- [x] Fret035000(420D→30)과 Strike010000(303D→30)을 실제 같은 장면에서 동시에 동결 추론한다. 두30채널은 중복 없으며 나머지21 목표는preload를 유지한다. 전체81 제어 API와 공동81 학습 정책은 구분한다.
- [x] 원본 goal-independent 압현 셀/최고 sounding fret와 독립240Hz pick detector를 연결한다. 실제 zone_allowed·방향·순서·±50ms·dwell0.1초·재무장8물리frame을 검사한다. 공동 crossing 압현은 보수적 endpoint bracket 진단이며 진짜 subframe pressure/연속 유지 증명은 아니다.
- [x] 548물리+420Fret+303Strike+28공동 진단=1299 후보 관측을 실제 로그로 기록한다. 중복/history를 포함한 비교 관측이며 최종 학습 ABI 확정이 아니다.
- [x] 12개 CPU 반례, 새 native3회/총3324물리step과 실제6개영상, 소스/금지 호출/제출 목표·rate/시계 검사를 수행한다. v3 Ninja import 실패는 물리·추론0이며 로그/소스 보존, 경로 문제를 해결한v4에서 실제 연결했다.

**동결쌍 연주 실패:** 환경3.85초(준비2+연주1.85)에 Fret의 기타-local 손목 위치 X 안전 상자가3제어frame 연속 위반되어 첫source done으로종료했다. 이는 손목 관절각 한계 종료가 아니다. Strike는 아직done이아니며 곡 완주도 아니다. 공동4event 정산/성공0·wrong_string crossing1. 기타 최대403.605mm/63.992°로PLAY 중 초기 지지를 잃었다.

Fret history 역변환은 source action_scale/clip으로 최대0.662462rad(PLAY0.637462) 재구성 오차가 발생한다. physical548의직전최종목표는정확하지만 원본source history와항상같다는주장은하지않는다. source관측의native COM 선속도 상속과 physical548의body-origin 선속도 변환 차이도기록한다. 초기지지/현재기타자세가훈련context와달라 source동등성·교사유효성은미인증이다.

- [ ] 현재기타 기준의공동 제어와source표현범위/지지자세 호환성을정리하고, teacher목표를무조건복사하지않도록학습구조를구현한다.
- [ ] SO(3)허용집합·연속 유지/dropout·fatal ledger·reward v4와 종료 계약을닫고 최종Actor D/상체81/512→256을확정한다. PPO/GPUvectorreset/학습은이번에하지않았다.

현재 entry는 [run_dual_music_v4.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v4.py:26), 새 owner는 [dual_music_scene_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_music_scene_v1.py:23), 공동 음악진단은 [dual_music_clock_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py:34)이다. v1~v3와 실패/후처리v1은 소비 이력으로 보존한다. [결과·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:1) · [실행집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v1.json:1). leaf 체크 갱신은 이 main 기록으로 추적한다.


#### 입력 계약 검증 마감 — 2026-10-12

현재 entry는 [run_dual_music_v5.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v5.py:26)이다. Strike checkpoint document/goal·grip SHA 및 원본 action/observation 순서 검사를 추가했다. 추가4CPU검사와같은조건native재실행에서v4/v5 controls·trace·초기값·240Hz음악판정이exact일치해같은3.85초Fret 실패를재현했다. 이전v4도실제입력SHA가일치했으며원본은보존한다. 마감집계는고유CPU16검사/새native4회/4248물리step/8영상/두pair각111추론tick/학습0이다. [집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v2.json:1) · [guard검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/contract_guard_v5_verification.json:1) · [후처리보존예외공개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/PROVENANCE_NOTE_V2.md:1).


### 상체 공동 학습 구조 1차 구현 — 2026-10-12

Actor739→512→256→81과 별도 Critic739→512→256→1, 원 latent 행동을 기록하는 tanh Gaussian/PPO, terminated·truncated를 분리한 GAE, rollout 곡 진행 연결, model/Adam/RMS/RNG/ABI 불변 저장을 구현했다. body9/head6/arm24/finger42 모두 출력하며 기존 PD와 목표 변화율/몸통±5°/root·하체 고정/기타 자유/strapOFF를 유지한다. 평균0 행동을 검증된 preload1.0 절대 목표에 대응하는 anchor codec으로 초기화했다. 기존 Actor 가중치/행동 복사는 없다. 관측에는 현재 기타 기준 손 상태, 원본 압현 셀, pick detector/rearm 메모리와 양손 음악 목표를 넣는다.

- [x] CPU22반례: Actor/Critic 실제 갱신, 끝점·경계 codec, 포화 likelihood, 종료/절단 bootstrap, checkpoint 복원/덮어쓰기 거절, 재무장0/7frame과 미종료 rollout 연결 검증.
- [x] native 평균5초+같은checkpoint복원·탐색5초, 총2400physics/4영상. 평균 trace는 preload100_v2와 exact, 최대46.306mm/9.179°. 탐색81전채널 표본, 최대57.114mm/9.960°. 각9event 성공0이며 학습·연주 성공이 아니다.
- [x] 실제 초기상태·고정 하체·관측·목표/rate·금지 API0·SHA 보존 대조와 독립 코드 검수.
- [ ] 실환경 PPO 최적화는0회. SO(3)허용집합, 연속 유지/dropout, fatal 일정 정산/할인, distal press pad, reward v5 측정/mask를 닫은 뒤 scalar reward 환경 API를 연결한다. 현재 --train은 장면 생성 전에 막는다. 739D는 이번 버전의 계약이며 보상 ledger 추가 때 새 ABI가 필요하다.

[이번 계획](/home/ajou/yigyu/3/stability_adapter_2/JOINT_LEARNING_IMPLEMENTATION_V1.md:1) · [정책](/home/ajou/yigyu/3/stability_adapter_2/joint_policy_v1.py:50) · [PPO](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:60) · [실제 entry](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:18) · [이미지·영상·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/README.md:1).

실제 정의 위치: [JointPPO](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:64), [native main](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:17).
