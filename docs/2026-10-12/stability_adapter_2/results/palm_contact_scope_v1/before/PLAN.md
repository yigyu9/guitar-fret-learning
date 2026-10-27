# StabilityAdapter 2 메인 계획: 허용 범위 안에서 자유 기타 연주

정리일: 2026-10-09. 최신 사용자 결정과 다음 작업을 기준으로 정리했다.
구현·설정·메인 설계는 `stability_adapter_2/`, 결과·로그·이미지·영상은 `docs/2026-10-12/stability_adapter_2/`에 저장한다.

## 1. 목표와 현재 상태

**humanoid 초기 자세로 자유 기타의 시작 흔들림을 줄이고, 사용자 허용 범위 안에서 fret·strike 연주를 수행하며 범위 이탈을 관절 제어로 보정한다.** 범위 안에서는 특정 초기 p/q로 정확히 복귀할 필요가 없고 작은 흔들림은 허용한다. WAIT → REACH → GRIP → TRANSPORT나 정지 대기를 필수 선행 과정으로 두지 않는다.

| 항목 | 현재 확인된 상태 |
|---|---|
| 환경·도구 | root/하체 고정·자유 기타·내부 충돌 환경, 초기 배치 진단, 정적 자세 조작, 실제 5초 녹화 구현 |
| 과거 안정화 | 일부 기존 자세에서 후기 변화가 작아지는 결과와 제한된 손목 보정 응답 관측. 실제 연주 성공으로 판정하지 않음 |
| 새 초기 후보 | 무스트랩·수평 넥·앞판 정면·오른손 비접촉의 실제 초기 배치와5초 비교 완료. 팔24 PI가 흔들림을 줄였으나 손바닥·검지·중지 실접촉 유지와 연주는 미완료 |
| 연주 연결·학습 | 체크포인트 계약 조사와 CPU 목표 합성 검사 완료. 새 후보에서 범위 판정·실제 연주·보정 학습은 미완료 |

상세 기준은 [허용 범위·연주 계약](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:1)을 따른다.

## 2. 공용 모델과 fret·strike의 핵심 차이

| 항목 | 기존 fret·strike | 새 자유 기타 환경 |
|---|---|---|
| 기타 | 고정 root·중력 비활성 | 자유 root·중력·접촉, 최신 초기 배치에서는 스트랩 OFF |
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

## 6. 최신 무스트랩 조건

2026-10-09 최신 사용자 요청에 따라 새 초기 배치에서는 **스트랩 힘·표시 모두 OFF**로 한다. 길이 조절로 지지를 보완하지 않는다. 자유 기타를 왼손과 허벅지·몸통의 실제 접촉으로 지지할 수 있는지 확인하며 오른전완을 대체 지지점으로 삼지 않는다.

이전 고정 길이 **1.1018469719600776 m**와 버튼·guide 경로·수동 cable 모델은 비교 이력으로 보존한다. 최신 계약과 단계별 검증은 [왼손 세 면 지지 계획](/home/ajou/yigyu/3/stability_adapter_2/LEFT_UNDERNECK_CONTACT_PLAN.md:1)을 따른다. 과거 무스트랩 자세의 후기 안정성은 새 수평 자세의 지지를 입증하지 않는다.

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
- 실제 물리 실험마다 초기 설정·관절각·기타 p/q·스트랩 힘/표시 ON/OFF와 시작부터 약 5초의 Isaac Gym 영상을 저장한다. ON 비교에서는 길이·경로도 표시하며, 오류·중단은 partial로 구분한다.
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
