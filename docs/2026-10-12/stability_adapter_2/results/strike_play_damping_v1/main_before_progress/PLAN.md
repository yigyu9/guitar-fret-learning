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
