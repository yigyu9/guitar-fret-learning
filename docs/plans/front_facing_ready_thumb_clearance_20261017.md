# LH thumb3 소량 펴기 — 네 표본 source/제한 self 진단

2026-10-17. 새 `diagnose_left_thumb_clearance_v1/`와 본 leaf만 작성한다. 기존 V4/그 이전 기록·소비 source·A·모델·Root 결과를 수정하지 않는다. 실제 IK/main/새 source 쌍 생산/native/PPO는 독립 review·Root ACK 전0이다. baseline/압현/RH 안정 성공이나 생산 tracker를 만들지 않는다.

## 배경과 바탕

V4 fixed-e16/B64 및 B_armF32는16/23.05초 source 통과,27.683/28초 thumb3–guitar root0/1이 약1.085122/1.203464mm로 원1mm를 실패했다. ideal current-error는 source 통과해도 최종 명령 bounds를 실패했다. 원 V4 결과·Root before14561/after·code/freeze를 보존하고 성공으로 바꾸지 않는다.

새 가설은 V4 fixed-e16의 **이미 계산된** Larm command/B 응답을 고정하고 LH:thumb3(index55) 목표만 δ∈{0,−.01,−.02,−.03}rad로 조금 펴는 것이다. 새 IK를 실행하지 않는다. Rfinger21/다른 LH finger/압현 검지 목표·하체/기타/Root/gain은 그대로다. 원 native thumb3 POSITION PD는 K20/D5/cap4Nm이며 source의 다른 숫자20을 cap으로 오해하지 않는다.

원4시각3840/5532/6644/6720과 직전 held3836/5528/6640/6716을 사용한다.16 경계는 δ0, 이후 세 시각은 full δ다. 향후16..16.5 ramp/해제·닫힘 연속 factor는 별도 runtime 계획이며 이번 네 표본이 그 interior를 검증하지 않는다.

## 축과 native topology의 사전 중단 조건

원 XML thumb3 hinge axis/body-local jointpos와 `diagnose_native_topology_v1/native_v2`의 checkpoint0459 DOF frames55 origin/axis 및 checkpoint0000 native pose를 직접 대조한다. JSON/.npy dtype/shape/SHA·index/name55·jointpos0·axis unit·원 q/body 순서를 검사한다.

초기 native thumb3 R×XMLaxis와 saved world axis의 같은 방향 vector 오차≤1e−5를 대조한다. native body origin+R×XMLjointpos와 saved origin의 거리는 원값으로 기록하며, COM/body-frame 차이가 가능하므로 origin 차이만으로 hinge 불가라 단정하지 않는다. 초기 frame의 qref 정합/freshness가 확인되는 경우 native `anchorLocal=R_initial^-1·(frameOrigin−p_initial)`와 `axisLocal=R_initial^-1·frameAxis`를 현재 pose에 운반한다. XML jointpos0을 native body origin으로 대체하지 않는다. frame freshness가 미확정이면 선정 중단/selectionFalse이며 schema 숫자 통과만으로 freshness를 true로 승격하지 않는다.

원 topology V2 exit1/result 없음·actor_joint_count_names false를 보존하고 final_checks의 나머지22 true와 state before/after·physics0을 별도 확인한다. 이를 전체 topology 성공으로 부르지 않는다.

## 엄지 명령과 native-anchored 회전

최종 thumb command는 float32(oldHeld55+δ)다. 실제 thumb 예측에는 최종 명령 증분(new−oldHeld)을 더해 기존 actual−held 오차를 보존한다. B64는 thumb actual64, B_armF32 쪽은 thumb actual도 arm과 같이 F32로 round-trip하며 추가 잔차를 별도 기록한다. 양쪽에서 실제 적용 hinge각은 predictedThumb−originalActualThumb다.

먼저 V4의 wrist 공통 delta로 원 native hand pose를 복원한다. 신뢰된 초기 frame의 native local axis/anchor를 그 pose에 운반해 world anchor 주위로 회전한다. `p_new=anchor+RotDelta·(p_old−anchor)`, `R_new=RotDelta·R_old`다. local anchor가0일 때만 body-origin post rotation과 같아진다. thumb_pad/top 등 고정 descendant pose도 같은 world rigid delta로 이동시켜 연결부 상대pose를 보존한다. fixed child 이동은 추가 DOF 제어가 아니다. 전체 finger FK 절대 pose로 native 형상을 대체하지 않으며 원 fullfinger FK 오차표를 보존한다.

최종13 명령(Larm12+thumb3)의 native bounds/qref±.8/principal<160도·finite/F32, 다른92/zero8 exact를 확인한다. arm4×3과 thumb scalar의 principal을 구분한다. actual 반사실의 bounds/zero8 qref 잔차는 기존 false와 변화를 따로 기록하며 실제 건강 성공으로 바꾸지 않는다. actual의 다른92는 원 actual, 제출 target의 다른92는 oldHeld 원본을 유지한다.

## source와 설계 여유

모든 δ에 대해 네 시각×두 정밀도에서 다음을 AND한다.

- 원 LH 전체 active1602쌍 source g≥−1mm. thumb3 외1513쌍도 전부 검사하며 source vertices/body pose가 δ로 바뀌지 않았는지 확인한다. inactive thumb_pad는 원 mask를 보존한다.
- thumb3–physicalG89의 worst g≥−.9mm. .9mm는 새 thumb 설계 여유이며 원 global1mm를 완화한 값이 아니다.
- V4 strict desired IK fit과 fixed-e16 model/native wrist 목표 추종≤1mm/.5도, 최종 명령13/ownership/두 정밀도 조건을 유지한다. 새 source 성공으로 기존 wrist/command 실패를 숨기지 않는다.
- δ0은 V4 source passed/failed·최악 pair/g를 재현해야 한다. g 비교 허용1nm는 재현 수치 비교용이며 source1mm/.9mm 판정에는 epsilon을 더하지 않는다.

선택은 모든 조건을 만족한 δ 중 |δ|가 가장 작은 하나다. 한 개도 없으면 selected=None이다. δ16=0이므로 초기 경계 자체가 여유/self 기준을 못 만족하면 후반 thumb 조정으로 덮지 않는다.

## thumb3 대 나머지53 source의 제한 self 범위

원 primary108로 full human54 source를 만들고 thumb3 shape와 나머지53을 전부 열거한다. 각 pair의 실제 filter AND, XML 활성/명시 exclude, 같은 고정 component/parent-adjacent를 **분리 기록**한다. required는 filter상 활성·명시exclude 없음·nonadjacent인 pair뿐이다. adjacent는 해부학 연결부의 이번 예산 비적용이며 native 자동 adjacent collision 정책이 꺼져있음을 증명하는 것이 아니다. 전체 native self정책/신체 전체 self 인증을 주장하지 않는다.

required pair는 source1mm를 검사한다. AABB/cache/face·closest 후보를 먼저 쓰고 부족할 때만 frozen refinement를 재사용한다. 상대가 capsule이면 capsule을 첫 shape로 바꿔 원 helper의 지원 형식을 유지하고 projection 방향/shape 이름을 명시한다. 새 Cartesian Minkowski fallback은 **조합≤1024**로 제한한다. 3D facet 상한을 적용한 projection 행렬은 약2.1M원소 이하(배열당 약16MiB)이며 범위 밖/solver 실패는 uncertified/selectionFalse다. 큰 self-hull을 억지로 만들지 않는다.

원 before required-self가 이미 부족하거나 uncertified이면 독립적으로 남기고 새 thumb 결과로 숨기지 않는다. 모든 δ의 selection을False로 유지한다. 음수 g나 부족 certificate를 cooked 실제 침투 깊이로 단정하지 않는다. excluded/inactive/adjacent의 이유와 53개 coverage를 보존한다.

## 봉인과 최소 CPU

V4 frozen code/result/input-before·Root before/after/log/review/ACK와 원 native8/source14/core30·원29/models108/실제 consumed helper, topology checkpoints/.npy/원source·Root 실패proof·본 code/leaf/CPU를 선택 before SHA로 닫는다. 새 A glob와 전체 조상 재분석은 하지 않는다. 전체 raw나 파일을 새로 생성하지 않는다.

- [ ] 원 metadata 실제 schema를 고정하고 code/expected before를 작성한다.
- [ ] 최소 CPU에서 axis55 실제 수치 정합과 topology 실패 보존, full54/53분류·형상 배치/PD20·5·4, native local hinge의 합성 회전/고정child·다른92/zero8/F32/경계·self 제한/원source 문턱 반례만 검사한다. 실제 source pair 생산과 IK는 금지한다.
- [ ] axis 실패 시 중단·보고한다. 통과 시 code/CPU/leaf를 동결해 독립 review/Root ACK를 기다린다.
- [ ] Root만 새 output으로 네 δ/네 시각/두 정밀도 source 진단을 실행한다. 추가 IK는 없다.
- [ ] source/여유/self 실패를 보존하며 이후 native/ramp/finite POSITION 동적 시험은 별도 계획·검수로 진행한다.

`actual_dynamic_tracking_validated=False`, `actual_health_certified=False`, `full_period_certified=False`, `native_self_policy_certified=False`, `cooked_penetration_certified=False`, `final_adoption_eligible=False`와 새 native/PPO0을 유지한다.
