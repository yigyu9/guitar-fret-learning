# StabilityAdapter 2 작업 계획과 새 채팅 인계

2026-10-06 시작한 별도 실험이다. 현재 목표는 **humanoid 초기 자세로 자유 기타의 시작 흔들림을 줄이고,
사용자 허용 범위 안에서 실제 Fret·Strike 연주를 수행하며 범위 이탈을 관절 제어로 보정하는 것**이다.
Root/하체 고정·내부 충돌·개별 체크포인트 연결·종료까지 native 녹화를 구현했다.
양손 통합·안정화 보정 학습·지속 연주 성공은 미완료다. 스트랩은 시험별 ON/OFF 비교 변수다.

메인 실행 계획은 [허용 범위 안에서 자유 기타 연주 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1)을 따른다.

2026-10-10 [연주 자세·현재 프렛 목표 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/README.md:1)을 추가했다. 저장된 스트랩 ON native 실행의113표본에서 넥 기울기·앞판 정면 각도·Chest 상대 배치·양팔12관절씩의 signed 한계 여유·현재 목표를 함께 표시한다.2초 대비 종료 앞판 각도는3.68→51.49°였고 종료 active 손끝 목표 오차는 검지106.88/약지78.74mm였다. 목표가 바뀌므로 한 음의 동일 목표 오차 변화로 단정하지 않는다. 종료 actor-root 위치가 범위 안이어도 연주 성공은 확인되지 않았다. 허용 회전 집합 판정·자연스러움 문턱·보정 제어·학습은 이 진단에 추가하지 않았으며 새 물리 실행은0회다.

전체 연구의 목표·우선순위·단계별 통과 조건은 [전체 연구 메인 계획](/home/ajou/yigyu/3/master_plan/README.md:14)을 따른다. 2026-10-10 반영한 방향은 자유 기타의 허용 범위 유지와 실제 압현·타현을 함께 달성하는 것이다. 초기 p/q 복원 중심의 아래 과거 기록과 달라지는 부분은 최신 전체 방향과 [현재 실행 목표](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:8)를 우선한다. 다음 소단계는 현재 기타 기준 왼손 손목·목표 프렛 오차와 접촉면을 시각화하고, 제한된 팔 보정으로 한 음의 압현·유지를 검증하는 것이다.

최신 봉인 결과는 [Fret 손가락/팔 목표 분리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md:1)와 [기존 길이 스트랩 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md:1)다. 두 시험의 압현 성공률은0%이며 스트랩 ON의 PLAY 계산 장력은0N이었다. [Strike 2초 전환 시험](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md:1)은 적시 타현1회 후 원본 실패로 종료했다. 체크포인트 시험은 최소2초 준비 뒤 원본 첫 done 또는 보호 중단까지 녹화한다. 아래 기록은 해당 당시 조건·진입점·미검증 상태를 보존한 이력이며 현재 실행 지시는 이 요약과 메인 PLAN을 우선한다.

**현재 실행 조건(사용자 변경): 하체 완전 고정.** 오른발 움직임을 없애기 위해
양쪽 Hip/Knee/Ankle/Toe 24 joint를 별도 모델에서 제거했다. root와 다리는 고정,
상체/양팔/양손은 기존 제어, 기타는 자유 상태다. 현재 진입점은
`python -m stability_adapter_2.run_self_collision --out <새 출력 경로>`이며
이후 자세·strap 탐색은 `SelfCollisionEnvironment`를 사용한다. 기존 dynamic 하체 실행
코드는 과거 결과 재현을 위해 보존한다. [구현·검증 계획](LOWER_BODY_FIXED_PLAN.md)과
[결과·전체 영상](../docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/README.md)을 따른다.

사용자 요청의 [허벅지·왼손 초기 지지 접근](THIGH_PALM_INITIAL_SUPPORT.md)도 비교했다.
왼쪽 Wrist3+Elbow_x와 기타 생성 위치 약1.1mm 보정으로 초기 source 간격을
약2µm까지 줄였지만 실제 LH:palm 접촉은 없고 실행 직후 손이 떨어진다.
후보를 안정 자세로 채택하지 않으며 [결과·시각화](../docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/README.md)를 따른다.
재현용 진입점은 `python -m stability_adapter_2.run_thigh_palm_support --candidate clear_2um --physics-steps 24 --out <새 출력 경로>`다.

현재 사용자 요청에 따라 [humanoid 내부 충돌](SELF_COLLISION_PLAN.md)을 활성화했다.
양손 및 비인접 팔–몸통 충돌을 허용하고, 연결부/동일 손의 기존 importer 제외는 유지한다.
새 기본 경로의0.1초 검증에서 LH:palm–RH:index1 접촉9행과 양의 raw lambda6행을
확인했다. 하체/root는 고정이며 손–기타 충돌도 허용한다. 이 기능 확인은 기타 안정화
성공이나 모든 형상 관통 제거를 뜻하지 않는다. [결과·시각화](../docs/2026-10-12/stability_adapter_2/results/self_collision_v1/README.md)를 따른다.
이전 `run_fixed_lower`와 `run_thigh_palm_support`는 self-collision OFF 이력 재현용으로 보존한다.

이전 사용자 방향: 하체 진단/관절 표현 비교를 보류하고 상체·양손 초기 자세와
스트랩 길이로 기타 안정화를 진행한다. C02 하체 초기각과 기타 +5mm 목표를 유지한
[초기 조합 탐색](POSE_STRAP_SEARCH.md)을 따른다. 하체 운동은 물리와 로그에 남으며
탐색 순위의 하체 자세 항목만 제외한다.

초기 자세·스트랩 33회 native 비교와 승인된 ±0.3rad 손 지지점 접근 탐색을
진행했다. source hull 손–넥 거리를 64.026mm에서 0.800~3.270mm로 줄였고,
Thorax에 따라 늘어난 경로의 절대 LA도 함께 비교했다. 하지만 0.5초에 팔이 처지며
손–넥 간격이 다시 커졌고 왼손 native 접촉은 없었다. 초기 조합은 최종 채택하지 않는다.
[지지점 접근 기록](HAND_SUPPORT_INITIAL_POSE.md)과
[관절 자세 유지 보정 제안](JOINT_HOLD_RESIDUAL_PROPOSAL.md)을 다음 검토 지점으로 둔다.
사용자가 목표각 보정 OFF/ON 비교를 승인했고 24관절의 제한된 PI 목표 보정을
구현했다. 1초 팔 편차 20.997→14.314°, 기타 오차264.207mm/48.065°→
196.035mm/33.994°로 개선됐지만 왼손 접촉0·큰 이탈·보정 포화가 남았다.
기타 오차 feedback/FK 작업조건 rejection/변화율 제한은 아직 없으며 학습을 시작하지 않는다.

승인된 양팔 초기각 범위의 후속 [오른팔 초기 접근 비교](RIGHT_SUPPORT_INITIAL_POSE.md)도
진행했다. 오른팔12만 조정한185개 정적 검사와4개0.1초 native 비교에서
RH palm–body 초기 간격을 줄였지만 어깨 접촉과 기타 오차 증가가 나타났다.
후보를 채택/연장하지 않는다. 왼손 위치 feedback은 사용자 확인 전이다.

[어깨 접촉 전후의 source 관측](RIGHT_SHOULDER_GEOMETRY_AUDIT.md)에서는
후보의 초기 어깨–body 간격도35.395→0.787mm로 줄었음을 확인했다.
두 contact 행의 signed field는 직전 저장 상태의 query와 가까웠다.
같은 step의 실행 후 pose와 접촉 field를 곧바로 동일시하지 않는다.
새 제어나 hard gate는 추가하지 않았다.

[어깨 여유 회복 초기각 비교](RIGHT_CLEARANCE_POSE_COMPARE.md)에서는10개 fresh
초기검사 중3후보와 기준을0.1초 실행했다. 두 후보는 어깨 접촉과 오차 악화,
나머지는 기준과 거의 같은 오차 및 손 접촉0이었다. 후보를 채택/연장하지 않는다.
기존 초기각 승인 범위의 비교이며 목표·LA·PD·제어/gate 변경은 없다.

[오른팔 distal 초기각 비교](RIGHT_DISTAL_INITIAL_POSE.md)에서는 어깨/Thorax
초기각을 유지한65개 source 검사와4개 짧은 native 비교를 완료했다.
가장 가까운 손 배치에서 기존 승인 PI를 재사용한6회 OFF/ON 진단의1초 기타 오차는
143.646mm/35.962°→121.298mm/29.759°였다. 오른엄지 접촉이 잠시 관찰됐지만
큰 이탈/LH접촉0/포화가 남아 안정 자세로 채택하지 않는다. 다음에는 같은 초기각의
절대LA를 비교하며 새 controller/gain은 추가하지 않는다.

[같은 초기각의 고정 스트랩 비교](RIGHT_DISTAL_STRAP_COMPARE.md)에서는 초기 법칙
장력0/5/10/20N에 해당하는 절대LA를 비교했다. 짧은8회와후기진단4회에서
5N은 이동/회전 tradeoff였고 두 오차 동시 개선은 없었다. 1초로 연장하지 않으며
0N을 진단 기준으로 유지한다. 초기 손 접촉을 위한 더 작은 각도 조합을 다음에 검사한다.

[더 작은 오른손 초기각 비교](RIGHT_DISTAL_FINE_INITIAL_POSE.md)에서는37개 source 검사와
10회 native 진단을 완료했다. Elbow_x+0.01/Wrist_x−0.005rad 추가 배치의1초PI ON은
76.099mm/14.184°로 이전121.298mm/29.759°보다 줄었다. 엄지 contact는0.667초까지
관찰됐으나 이후 소실·큰 drift·LH접촉0/포화가 남는다. 후보2를 다음 진단 기준으로만 유지한다.

[손목 X 유지 비교](RIGHT_WRIST_RETENTION_COMPARE.md)는7개 source/13native를 완료했다.
+0.0025rad 후보는0.5초만 개선되고1초는84.746mm/16.983°로 이전보다 악화됐다.
새 손목각은 채택하지 않으며 기존 fine c02·고정LA를 진단 기준으로 유지한다.
다음에는 접촉 소실 관측과 작은 Elbow 초기각을 비교하고 새 제어는 확인 전 추가하지 않는다.

[팔꿈치 유지 비교](RIGHT_ELBOW_RETENTION_COMPARE.md)는 5개 초기 입력 검사와 10회 native를
완료했다. Y +0.005rad는 0.5초만 개선됐고 1초에는 118.323mm/29.068°로
기준보다 악화됐다. 새 팔꿈치각을 채택하지 않고 fine c02·고정 LA를 유지한다.
유망한 1초 후보가 없어 새 OFF 비교는 하지 않았다. 다음은 작은 Elbow_y 음수 초기각의
source 검사이며 새 제어 구조는 사용자 확인 전이다.

[팔꿈치 Y 음수 비교](RIGHT_ELBOW_Y_NEGATIVE_COMPARE.md)는 5개 초기 검사와 4회 native를
완료했다. −0.00125rad만 source gate를 통과했고 0.5초는 35.238mm/4.910°로
기준보다 조금 컸다. 이번 계획에 따라 1초/OFF는 실행하지 않았으며 후기 성능은 미측정이다.
기존 fine c02·LA·PI를 유지한다. 다음에는 이미 source를 통과한 음수 후보 중
1초를 측정하지 않은 조건의 후기 동작을 직접 비교한다.

[음수 후보 후기 직접 비교](NEGATIVE_POSE_LATE_DIAGNOSTIC.md)는 fresh 초기 검사4개와
15회 native를 완료했다. Wrist_x −0.005rad는0.5초에는 조금 나빴지만1초ON은
73.660mm/13.502°로 이전76.099mm/14.184°보다 작았다. 같은 초기각 OFF는
144.260mm/36.310°였다. 이 설정을 다음 진단 기준으로만 쓰며 큰 drift/포화/LH0이
남아 안정·연주 성공은 아니다. 다음에는 이 초기각의 고정 strap 길이를 함께 비교한다.
이전 preload 시험은 더 이전 초기 자세였으며 새 제어는 사용자 확인 전이다.

[개선된 손목 자세의 스트랩 비교](WRIST_POSE_STRAP_COMPARE.md)는 초기5기록과
12native를 완료했다. 같은 자세의 초기 법칙 장력5/10/20N은1초 이동·회전을 모두
악화시켰다. 새 길이는 채택하지 않고 Wrist_x−0.005rad와0N LA를 진단 기준으로 유지한다.
20N에서 후기 몸통–기타 접촉도 관찰됐다. 다음은 기존0–5N 사이 preload1/2N 비교다.
기타 오차 feedback과 학습은 아직 추가하지 않았으며 안정·연주 성공은 아니다.

[작은 초기 스트랩 장력 비교](SMALL_PRELOAD_COMPARE.md)는3개 fresh 초기 검사와
0/1/2N의 ON9native를 완료했다. 1N은0.1/0.5초에 조금 줄었고1초79.222mm/15.028°,
2N은120.773mm/30.086°로0N73.660mm/13.502°보다 악화됐다. 새 길이는 채택하지
않으며 OFF를 추가하지 않는다. 다음은 같은0N 길이에서 오른손목 X 음수방향의
작은 추가 초기각을 기존 승인 범위 안에서 source부터 검사하는 것이다.
기존 PI/PD/목표/몸통·손가락·C02하체를 유지하며 안정·연주 성공은 아니다.

[오른손목 음수 추가각 비교](RIGHT_WRIST_NEGATIVE_EXTENSION.md)는3개 초기 검사와
9native를 완료했다. 기준에서−0.0025/−0.005rad 더 조정한1초 오차는
114.479mm/27.196°,124.274mm/31.129°로73.660mm/13.502°보다 악화됐다.
기존각·LA를 유지하고 새 OFF를 추가하지 않는다. 다음은 현재각±0.00125rad의
중간 조건 검사다. 기존 승인 범위·PI/PD/목표를 유지하며 안정·연주 성공은 아니다.

[손목 기준각 주변 비교](RIGHT_WRIST_LOCAL_COMPARE.md)는3초기검사와9native를 완료했다.
±0.00125rad의1초 오차117.748mm/28.362°,119.008mm/29.302°도 기준보다 컸다.
기존각/LA를 유지하고 OFF를 추가하지 않는다. wrist X의 더 작은 세분화는 보류하며
다음은같은 손목각/LA의 Elbow_x−0.0025/−0.005rad 초기 조합 검사다. 기존 제어/
물리/목표를 유지하고 안정·연주 성공은 아니다.

[같은 손목의 팔꿈치 X 조합](RIGHT_ELBOW_WRIST_COMBO.md)은3초기검사와ON9native를
완료했다. −0.0025/−0.005rad의1초119.344mm/28.970°,119.010mm/28.633°는
기준보다 커 기존각/LA를 유지하고 OFF를 추가하지 않는다. 오른쪽 distal의 작은
세분화는 보류하고 다음에는같은 오른팔/LA에서 왼팔꿈치·왼손목 한축씩±0.025rad
초기 조건을 기존 승인 범위에서 source부터 검사한다. 새 제어/학습은 확인 전이다.


[왼팔 distal 초기각 비교](LEFT_DISTAL_INITIAL_COMPARE.md)는9초기검사와ON18native를완료했다.
3조건은source 음수pair로거절했고기준+5후보의1초이동·회전은모두악화됐다.
기존각/LA를유지하고OFF를추가하지않는다. LH:palm source query0.072963mm조건도
native LHcontact0이며1초포화212·큰drift가남아안정성공은아니다. 다음은같은오른팔/LA에서
측정된LH source경계방향의단일축각을기존승인범위안에서fresh검사하는것이다.
기존목표/PI/PD/solver·source/LH조건을유지하고새제어/학습은확인전이다.


[왼손 형상 간격 경계 비교](LEFT_PALM_BOUNDARY_COMPARE.md)는8초기검사와18ON/6OFF를완료했다.
Wrist_x−0.0125의1초ON73.268255mm/13.439339°는기준보다소폭작았고같은초기각OFF는
144.267967mm/36.395296°였다. 이왼손목각과기존오른팔/LA를다음진단기준으로만유지한다.
큰drift/속도·LH0·ON포화212가남아안정성공은아니다. 다음은이fullpose의0/1/2N초기법칙장력
고정LA비교이며이전strap결과를승계하지않는다. 기존목표/PI/PD/solver·gate를유지하고
새제어/학습은확인전이다.


[새 왼손목의 스트랩 비교](LEFT_WRIST_STRAP_COMPARE.md)는3fresh검사/ON9native를완료했다.
1/2N초기법칙길이는1초118.622890mm/28.826878°,120.835674mm/30.129771°로0N보다컸다.
새길이/OFF를추가하지않고왼손목X추가−0.0125rad·LA1.1010801317960974m를진단기준으로유지한다.
LH0·ON포화212·큰drift/속도가남아안정성공은아니다. 다음은같은조건의3초후기정지측정이며
WAIT전제나새controller/목표/gate/학습이아니다. 초기q/PD/solver/제어/기타목표는유지한다.

[동일 설정 3초 진단](QUIESCENT_3S_DIAGNOSTIC.md)은720 steps와이전1초raw prefix 일치를 확인했다.
최대251.150465mm/81.526863°, 종료236.386968mm/77.801738°로초기 기타 상태 유지에 실패했다.
종료 속도가 낮아져도 목표와 크게 다른 자세이며 LH접촉0·포화692/720 samples가 남는다.
현재 초기각/LA/PI는 진단 기준이며 안정 자세로 채택하지 않는다. 다음에는 손 작업공간 위치와
관절 보정의 관계를 설계 검토하고, 새 제어 적용은 사용자 확인 후 진행한다.

[손 위치 계측](PALM_FRAME_AUDIT.md)에서 왼손 source 중심 이동1초138.278mm/3초144.535mm와
링크 원점과의 차이를 확인했다. 초기 CPU Jacobian shape와 상태 조회 불변성은 통과했으나
frame/COM/DOF 미분은 미검증이다. [현재 기준 제안](PALM_POSITION_CURRENT_PROPOSAL.md)의
fresh 초기FK 대조를 먼저 하고 새 위치 제어/변화율 제한은 사용자 확인 후 적용한다.

[초기 FK 대조](PALM_JACOBIAN_FK_CHECK.md)는23 fresh 초기화·rollout0으로 완료했다.
raw Jacobian은 관절 위치 좌표의 미분과 달랐고, 현재 초기각의 SO(3) tangent 변환과
native COM 기준 source 중심 보정 후 최대 오차는0.274299mm/rad였다.
이는 현재 초기 자세의 결과이며 runtime 검증·기타 안정성 성공은 아니다. 다음은 동일 승인
PI 실행의 Jacobian/속도 계측이며 새 위치 제어·변화율 제한은 확인 후 적용한다.

[Runtime 계측](PALM_JACOBIAN_RUNTIME_CHECK.md)도 동일 승인 PI의0.1초 prefix를 재현했다.
Refresh 후 COM 속도 대응 최대 오차는LH1.500569mm/s/RH1.371527mm/s였고,
refresh 전 cache는 직전 값이었다. 다음 [위치 보정 비교안](PALM_POSITION_COMPARISON.md)은
현재 초기각 기준 PI/변화율 제한 PI/왼손 위치 보정의3조건이며 사용자가 비교 진행을 승인했다.

[저장 Jacobian의 선형 범위](PALM_TASK_AUTHORITY.md)도 분석했다. 초기 손 위치 복귀에
필요한 세 축 변위는 기존 보정 box의 각 독립 선형 범위 안에 있지만, 동시달성/FK/물리
안정성 인증은 아니다. 추가 native/새controller 실행은 없고 중요 제어 확인을 기다린다.

[왼손 초기 source 간격 관찰](LEFT_EARLY_SOURCE_DIAGNOSTIC.md)에서는 저장된 첫0.1초의
QP palm–neck hull 간격0.545306→29.787930mm를 확인했다. 선택 시점의 위쪽 proxy/
국소 넥 아래 조건이 유지돼도 LH native contact 행은 없었다. Source query와 실제 지지를
구분하며 이 관찰 자체에는 새제어/물리 실행이 없다. 이후 사용자가 위치제어 비교를 승인했다.

승인된 [3조건 비교](PALM_POSITION_COMPARISON.md)는 새 bounded 위치 목표 계산과
양팔0.02rad/update 제한을 구현했고 순수 수치8검사·독립 코드 검수·3회0.1초 native를 완료했다.
기존 PI 구현과5배열 prefix를 재현했다. 왼손 중심 이탈48.561/48.836/47.474mm에 비해
기타 전체 상태는세조건에서 같았고 최대6.874mm/1.520°·양손 contact0이었다.
작은 계산 잔차를 실제 위치 유지 성공으로 보지 않는다. 기존초기q/LA/PD/물리/root와
몸통9/손가락42/C02하체 목표·주요66 연결을 유지했고 학습/기타p/q feedback은 없다.
0.5/1초나 새gain/box는 이번 소단계에 추가하지 않았다. 결과는
[palm_position_compare_v1](../docs/2026-10-12/stability_adapter_2/results/palm_position_compare_v1/README.md)에 둔다.

후속 사용자 승인: 기타 +5mm를 유지한 하체 유효 초기각의 기준 ±0.05rad 탐색과
개선 후보 최대 3개 짧은 비교를 진행한다. [계획](LOWER_INITIAL_POSE.md)을 따른다.
이는 초기 배치의 제한된 예외이며 주요 action은 기존 상지66개로 유지한다.

하체 탐색과 3개 native 비교 완료: C02에서 0.1초 기타 오차가 7.174mm/1.591°로
줄었지만 초기 발 음수 gap과 116.689° 실제 leg body 방향 편차가 남았다.
성공으로 채택하지 않는다. [결과](../docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/README.md).

최신 사용자 승인: 하체 초기각·기타 회전·절대 스트랩 길이를 유지하고 기타 초기 Z만
+5mm 올려 실제 시험한다. [실제 시험 계획](GUITAR_Z_TRIAL.md)을 따른다.
기존 정적 제안은 하체 초기각 보정 대신 기타 초기 Z 소폭 상승을 우선 비교하는 것이었다.
[정적 비교 계획](GUITAR_Z_PREVIEW.md)의 +0/+2/+5/+10/+15mm는 원본과 같은 기타
p/q를 쓰는 기존 비교 원칙의 명시적 예외 후보다. 새 설정으로 +5mm를 선언한 trial만
올린 초기 위치를 유지 목표로 고정하며 원본 pose와의 차이도 기록한다. 기본 H0는 유지한다.
아래 동일 p/q 규칙은 이 예외 외의 기존 실험에 적용한다.

실제 H0/+5mm 각 0.1초 비교 완료: 초기 source 허벅지 겹침은 해소됐으나,
양쪽 모두 0.05초 무릎–넥 접촉과 약 7.32° 기타 회전이 남았다. +5mm는 초기
배치 후보이며 정지 안정성 성공이 아니다. 17개 테스트와 H0 과거 물리값 재현 검사를
통과했다. [원자료 비교](../docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/comparison.json).

## 기존 실험과의 구분

`stability_adapter/`는 WAIT → REACH → GRIP → TRANSPORT를 통해 기타를 복원하는
기존 방향이다. 기본 환경과 왼쪽 33관절 제어 연결을 구현했으며 기존 코드·계획서·
검증 결과는 그대로 보존한다. 새 실험을 위해 수정·삭제하거나 기존 계획서를 대체하지 않는다.

`stability_adapter_2/`는 접근·운반을 연주의 필수 선행 과정으로 두지 않는다.
기타는 공용 시작 위치·회전에서 출발한다. 양손 초기 배치·물리 제어와 스트랩 길이를
검토하되, 안정화하기 쉬운 다른 기타 자세로 목표를 바꾸지 않는다.
고정 해제 순간부터 초기 목표 대비 위치·회전 오차를 측정한다.
공용 humanoid H0·S0는 진단 기준선이다. 초기 humanoid 자세는 허용된 관절 범위에서
변경하고 스트랩 초기 길이/장력과 조합해 선정한다. 그다음 같은 초기 조건에서 feedback
OFF/ON을 비교한다. 기타 목표 p/q는 모든 후보에서 같고, 원본 스트랩 경로·수식은 유지한다.
초기 상태 조합의 입력·정적 검사·native 비교는 구현했으며 최종 조합은 미선정이다.
기타 오차 feedback은 아직 구현하지 않았다.

## 지켜야 할 물리 조건

- 사람 root/Pelvis는 고정한다. 기타 root는 자유롭게 두고 중력과 실제 접촉으로 움직이게 한다.
- 양쪽 Thorax부터 손가락까지 66관절을 주 제어 범위로 둔다.
  Torso/Spine/Chest 9개 관절은 먼저 기준 자세 PD 목표를 유지한다.
  작은 몸통 목표 보정은 초기 장면 검토 후 정하고 실제 drift를 별도로 측정한다.
  몸통을 영구 고정하거나 매 프레임 관절 상태를 덮어쓰지 않는다.
- 기타 고정, 손과 기타의 강제 부착, 매 프레임 기타 pose 덮어쓰기,
  목표 자세로 끌어당기는 인위적 힘은 사용하지 않는다.
- 원본 스트랩 연결점·몸 주변 경로·물리 수식을 출발점으로 삼는다.
  길이는 초기 연주 자세에 맞춰 조정하되 장력·길이 변화·지지 효과를 기록한다.
- 스트랩은 먼저 초기 길이를 조정하고 실행 중에는 고정하는 경우를 검증한다.
  고정 해제 후 동적 길이 조절도 별도 후보로 비교하되 적용 여부는 확인 후 정한다.
  동적 조절은 능동 스트랩 구동을 가정하므로 속도·범위·장력·에너지 기록이 필요하다.
  이를 정책이 직접 제어할지 여부는 물리 검증 후 결정한다.
- 초기 손 위치는 기타의 초기 pose를 유지할 수 있는 물리 지지 후보로 검토한다.
  fret·strike 동작을 계속 막는 grip은 최종 연주 후보로 채택하지 않는다.
  손·넥·몸통이 관통해서 안정적으로 보이는 배치는 허용하지 않는다.
- 공용 자산의 실제 질량·관성·충돌 형상과 관절 한계를 확인한다.
  기존 실험의 질량 보정·제어 gain·자세 변경은 검증 없이 승계하지 않는다.

## 단계별 작업과 검증

### 1 기준 장면과 새 계획 확정

공용 모델, fret·strike 환경의 시작 자세와 원본 스트랩 비교 결과를 출발점으로 삼는다.
기타의 초기 위치·회전을 기준 목표로 기록하고, 양손 배치와 스트랩 길이 후보를
실제 장면으로 보여준다. 기준 기타 목표는 유지하며 제어 범위와 동적 스트랩 조건은 확인한다.

검증 기준은 배치·단위·좌표계·출처가 확인되고, 초기 접촉과 관통을 구분할 수 있는 것이다.
정지 안정성의 수치 허용 오차는 장면의 크기와 측정값을 보고 정한다.

### 2 자유 기타의 정지 안정성

새 기본 환경을 최소한으로 구현한다. 초기 목표에서 자유 기타로 시작하고,
양손 기준 자세 유지·초기 스트랩 길이 선택·양손 피드백 제어를 순서대로 비교한다.
필요하면 길이 피드백 제어와 양손·스트랩 공동 제어 후보를 추가한다.
고정 해제 직후부터 위치·회전 오차, 속도, 길이·장력·접촉을 기록한다.
기타 pose를 직접 교정하거나 떨어진 자세를 새 목표로 삼지 않는다.

검증 기준은 초기 목표 대비 최대·평균 위치/회전 오차와 속도를 줄이면서,
낙하·지속 회전·관통·과힘 없이 연주 가능한 상태를 유지하는 것이다.
초기 순간, 과도 응답, 후반 유지 구간을 구분하며 최종 허용 오차는 실측 후 합의한다.

### 3 작은 손과 팔 움직임에 대한 안정성

물리 관절 제어로 작은 팔·손 움직임과 손가락 개폐를 적용한다. 지지에 사용하던
손가락을 움직일 때 기타가 무너지는지, 오른손·몸통 접촉이 움직임을 방해하는지 확인한다.
안정화에 필요한 grip이 fret·strike 동작을 막지 않는지도 검토한다.

검증 기준은 정지 상태뿐 아니라 시험 움직임 중에도 기타 자세·속도·접촉이 허용 범위를
유지하는 것이다. 이 시험을 통과해도 실제 곡 연주 성능이 검증된 것으로 보고하지 않는다.

### 4 연주 연결과 학습 설계

앞선 검증 후 연주 제어와 stability adapter의 역할을 정한다. 최종 연주에는 상체·
양팔·양손의 관절을 사용할 수 있어야 하므로 기존 왼쪽 33관절을 전체 시스템의
고정 제한으로 삼지 않는다. 관절별 제어권 또는 연주 목표각과 안정화 보정량을 합치는
규칙을 정해 하나의 최종 목표각만 물리에 전달한다.

관측·행동·네트워크·보상·종료·학습 방식은 이 역할에 맞춰 이후 결정한다.
기존 단계 보상이나 PPO 구성을 먼저 복사하거나 환경 검증 전에 장기 학습을 시작하지 않는다.

## 계획·구현과 결과 저장

- 메인 계획서는 `/home/ajou/yigyu/3/stability_adapter_2/PLAN.md`에 둔다.
- 새 코드와 설정은 `/home/ajou/yigyu/3/stability_adapter_2/`에 작성한다.
- 후속 구현 계획·설계도 `stability_adapter_2/`에 둔다.
- 검증 결과·분석·로그·영상·산출물 정리는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/`에 모은다.
- 각 작업 결과는 [이미지·영상과 설명을 포함한 누적 결과 문서](../docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md)에
  새 단계로 추가한다. 이미지로 담기 어려운 움직임은 영상으로 저장하고 조건·설명·수치·판정·미검증 항목을 함께 남긴다.
  실제 장면 캡처와 측정 그래프를 구별하며 이전 결과와 실패 기록은 보존한다.
- 공용 모델·자세·gain 데이터와 기존 코드의 검증된 계산을 참고하되 기존 패키지 전체를 복사하지 않는다.
- 이번 문서는 새 실험의 출발 범위다. 기존 계획서는 비교 실험의 기준으로만 보존한다.
- 작은 기능 하나를 구현하고 검증한 뒤 다음 단계로 진행한다.
- 변경한 파일의 절대 경로·실제 줄 번호, 역할, 검증 결과와 남은 결정 사항을 알려준다.

## 진행 체크리스트

- [x] 별도 실험 디렉토리와 작업 범위 문서 생성
- [x] 공용 장면·연주 시작 자세·스트랩 설정 비교와 CPU 자산 로드 감사
- [x] 초기 기타 위치·회전 유지 목표로 상세 계획 수정
- [x] CPU 기본 환경·66관절 목표·몸통 목표 유지 및 native 제어 응답 검증
- [ ] 초기 자세와 스트랩 후보를 렌더하고 상세 검증 계획 확정
- [ ] 자유 기타 정지 안정성 검증
- [ ] 작은 손·팔 움직임에 대한 안정성 검증
- [ ] 연주 연결과 관절별 제어권 설계
- [ ] 필요한 정책과 학습 구조 결정

## 첫 CPU 환경 구현

`environment.py`는 root 고정 사람·자유 기타·고정 의자·원본 경로 스트랩을 만든다.
`control.py`는 관절 이름으로 양쪽 66관절을 선택하고 초기 목표각에 보정량을 더한다.
몸통 9개 목표와 나머지 관절 목표는 기준값으로 유지한다. `strap.py`는 COM 기준
경로점 속도와 장력·양끝 힘·guide 반작용을 계산한다. `config.json`은 공용 자산과
원본 스트랩 값을 지정한다. 초기화 후 `step()`에는 pose/state 재주입이 없다.

현재 backend는 **CPU native POS solver PD**다. 공용 kp/kd/effort cap을 쓰지만
공용 tensor hybrid PD와 같은 수치적 actuator는 아니다. native POS에서 별도 effort가
무시된다는 검수 결과를 반영했다. 실제 토크·포화와 GPU 제어는 아직 검증하지 않았다.
66관절 target은 환경 인터페이스이며 RL action 차원을 확정하지 않는다.

프로젝트 루트에서 새 결과 디렉토리로 실행한다. 이미 report가 있으면 덮어쓰지 않는다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.run_initialization \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/새_run_ID
```

같은 환경변수로 `python -m unittest discover -s stability_adapter_2/tests -v`를 실행하면
순수 검사 4개와 CPU native 계약 검사 2개가 실행된다. native 검사는 목표 변경의 실제
관절 응답과 offset-COM 회전체의 점 속도를 확인한다.

v3의 초기화 검사는 통과했으나 0.1초 뒤 기타 오차는 65.315mm·7.318°였다.
자세 유지 성공이 아니며, 초기 장면 렌더·접촉·양손 지지 배치부터 확인해야 한다.
GPU/렌더는 현재 NVIDIA 드라이버 통신 실패로 미검증이다.
실행 로그·실패 이력은 [결과 정리](../docs/2026-10-12/stability_adapter_2/README.md)에 있다.

## 새로운 채팅에 입력할 프롬프트

프로젝트 루트는 `/home/ajou/yigyu/3`입니다. 먼저 프로젝트 지침과
`stability_adapter_2/README.md`를 읽고 이 문서를 출발 기준으로 삼아주세요.

기존 `stability_adapter/`와 관련 계획서·산출물은 수정하거나 삭제하지 말고 보존해주세요.
새 실험은 `stability_adapter_2/`에서 진행합니다. 가장 중요한 목표는 humanoid 초기 자세와
스트랩 초기 설정을 함께 조정해 시작 직후 기타 변화를 줄이고, 이후 제어로 초기 기타 p/q에서
벗어난 오차를 보정·유지하는 것입니다. 기타 초기 p/q는 모든 비교의 같은 목표로 유지합니다.
WAIT → REACH → GRIP → TRANSPORT를 연주의 필수 선행 과정으로 구현하지 않습니다.

공용 모델·시작 자세·원본 스트랩 비교와 CPU 로드 감사는 완료했으므로 상세 계획서를 먼저 읽어주세요.
초기 배치 시각화 → 자유 기타 기준선 → humanoid·스트랩 초기 상태 조합 선정 → 오차 보정·유지 →
필요시 동적 스트랩 후보 비교 → 작은 손·팔 움직임 검증 순서로 진행합니다.
동적 길이 조절의 적용 여부와 구동 제한은 구현 전에 확인하며 학습 구조는 이후 결정합니다.
기타 고정·강제 손 부착·지속적인 pose 덮어쓰기는 사용하지 않습니다.

사람 root는 고정하고, 양쪽 Thorax부터 손가락까지 66관절을 주 제어 범위로 둡니다.
Torso/Spine/Chest는 먼저 기준 목표를 유지하며 작은 보정은 초기 장면 검토 후 정합니다.
최종 연주에는 상체와 양팔·양손을 사용할 수 있어야 합니다. 기존 33관절 제어와 기준 자세
유지를 그대로 승계하지 말고 연주 제어권·안정화 보정의 관계를 따로 설계해주세요.
기존 코드는 참고만 하고 필요한 부분만 최소 구현해주세요. 네트워크·보상·학습 구조는
환경 검증과 역할 분담 후 결정하며, 검증 전에 장기 학습을 시작하지 마세요.

메인 계획서는 `stability_adapter_2/PLAN.md`이며 구현·설정·구현 설계도 `stability_adapter_2/`에 둡니다.
검증 결과·분석·로그·영상과 산출물 정리는 `docs/2026-10-12/stability_adapter_2/`에 둡니다.
각 작업 완료 후 `VISUAL_REPORT.md`에 이미지 또는 영상과 그 설명·조건·수치·판정을 새 단계로 누적해주세요.
작은 단계별로 계획 → 구현 → 검증 →
검토 순서로 진행하고, 변경 파일의 절대 경로와 실제 줄 번호를 알려주세요.
제가 VS Code에서 확인하며 설계에 참여하겠습니다. 목표나 제어 범위를 바꾸는 결정은
먼저 확인해주세요. 계획서를 바탕으로 한두 단계씩 구현·검증·검토해주세요.

## 최소 자세 제약

[자세 제약 제안](POSTURE_CONSTRAINTS.md)을 따른다. 사용자는 초기 왼손 손바닥의
위쪽 반구를 필수로 하고 +Z에 가까운 방향은 부드럽게 선호하는 기준을 확인했다.
나머지 후보와 실행 중 위반 기준은 장면 검토 후 정한다. 새 runtime 제약은 아직 적용하지 않았다.

## 초기 겹침 검사

[초기 상태 진단 계획·검증](INITIAL_STATE_DIAGNOSTICS.md)을 따른다.
`run_initial_overlap.py`는 현재 H0/S0 환경 생성 후 첫 추가 step 전에 전신–기타 원본 충돌
형상을 native pose에 놓아 검사한다. 설정·관절각·strap rest length·부위별 signed query 값·
가까운 점·형상 수·source hash와 CPU 진단 이미지를 run별로 저장한다.
기존 native 환경·controller는 변경하지 않았다. 자동 시작 gate/reset은 아직 없다.

```bash
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib \
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.run_initial_overlap \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/새_overlap_run_ID
```

MuJoCo 3.2.3의 CPU 보조 query이며 GL은 필요 없다. Gym을 MuJoCo보다 먼저 import한다.
위 환경변수로 `python -m unittest discover -s stability_adapter_2/tests -v` 실행 시
초기_overlap_v2 검증 당시에는 새 합성 검사 1개와 기존 계약 검사 6개, 총 7개가 실행됐다. 현재 같은 검사 명령은 batch/input 계약 검사를 포함해 총 13개 검사를 실행한다. 초기화 실행 명령 자체에는 MuJoCo가 필요 없다.
관통 시 음수의 크기는 실제 깊이로 검증되지 않았으며 PhysX cooked 형상과도 대조 전이다.
v2에서 R_Hip–G:body 음수 후보가 검출되어 무관통 시작으로 인증하지 않는다.
run별 초기 관절각/절대 rest length 입력과 batch 부분 재개는 구현되어 있다. 허용 거리·PhysX 기반 자동 시작 판정은 별도로 검증·결정해야 한다.

## 넥–손바닥의 국소 높이 시각화

`plot_neck_palm.py`는 native 초기 H0를 읽어 palm 형상 중심·넥 길이 기준선·직교 투영
지점·대응 단면의 world 높이를 표시한다. 실제 초기 상태 그림과 설명용 가상점 그림을
분리한다. [기준과 검증 계획](/home/ajou/yigyu/3/stability_adapter_2/POSTURE_CONSTRAINTS.md:98)은 자세 변경·controller/gate를 적용하지 않는다.

위 겹침 검사와 같은 환경변수로 실행한다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_neck_palm \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/새_neck_palm_run_ID
```

수치와 두 이미지의 설명은 [누적 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:310)에 있다.

## 실험 분석과 산출물 역할

GPT-6.1 Sol (`gpt-6.1-sol`)이 raw 결과를 분석하고 후보 방향·수치를 정한다.
GPT-6 Luna (`gpt-6-luna`)는 승인된 brief에 따라 증거 기반 산출물과 누적 결과 기록을 만든다.
새 작업은 [실험 workflow 합의](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:1)를 먼저 읽는다.
Luna 모델 override는 하위 작업에만 적용하며 현재 parent 채팅 모델은 유지한다. 자동 라우팅 runner는 아직 없다.

## 현재 run 입력·batch 상태

run별 관절 절대각·절대 rest length 입력, 순차 local batch 실행과 hash 검증 resume이 구현되어 있으며 CPU 기능 진단 13개 검사가 통과했다. 세 run의 결과·측정 비교와 한계는 [batch_contract_v1 결과](../docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/README.md)에 정리했다. PhysX clearance gate, runtime feedback, 자동 후보 탐색과 모델 자동 라우팅은 미구현이다.

[같은 3조건의 0.5초 후속 진단](PALM_POSITION_HALF_SECOND.md)을 진행한다.
0.1초의 작은 손 위치 차이가 지속되는지 동일 gain/box/초기각/LA로 확인하며,
기존0.1초 자료와 producer를 보존한다. 새 설정이나 안정 후보 채택은 아니다.

0.5초 비교 완료: PALM_RATE는 RATE_PI 대비 왼손 최대이탈을115.675→90.541mm로
줄였지만 기타 이동35.691→36.091mm 증가/회전5.006→4.762° 감소의 tradeoff였다.
LH접촉0·큰손이탈이남아채택하지않는다. 기존prefix·계약·분석재생성을확인했고
이번단계에1초/새gain/box/PD는추가하지않았다. 결과는
[palm_position_half_second_v1](../docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/README.md)에 둔다.

[저장된 팔 목표–실제 응답 대조](PALM_TARGET_RESPONSE_AUDIT.md)를 진행했다.
왼어깨 scalar 목표–실제 차이가약21°남고,정의가능한29구간의손이동은초기복귀방향의
반대성분을가졌다. 정적목표계산은16.7ms응답예측이나PD원인증명이아니다.
새 native/제어설정변경은없으며 force계측가능성을먼저검토한다.

[총 DOF force 관측](DOF_FORCE_OBSERVATION.md)은 동일 PALM_RATE의 120step에서
기존 7배열을 그대로 재현했다. 첫 0step 실패와 참조 보존 수정 후 성공을 구별해 보존한다.
총힘값은 actuator 전용 토크나 PD 부족의 증거가 아니며, 기타 36.091mm/4.762°·LH 90.541mm
이탈이 남는다. 다음 [어깨 stiffness 비교 제안](SHOULDER_PD_COMPARISON_PROPOSAL.md)은
중요한 PD 변경이므로 사용자 확인 전이며 아직 구현·실행하지 않았다.

[SDK 저장 목표 대조](NATIVE_TARGET_READBACK.md)는 기존 PALM_RATE 첫0.1초에서
48회×105축 getter 읽기와 제출 목표가 정확히 같음을 확인했다. 기존7raw prefix와
상태·목표·PD 불변성이 통과했다. 이 구간의 전달값 불일치는 관측되지 않았으며
후기·PD 원인·기타 유지 성공은 미검증이다. 어깨 stiffness 비교는 계속 확인 전이다.

[PALM_RATE의1/2N 초기 길이 비교](PALM_PRELOAD_COMPARISON.md)는 승인된 길이
범위에서4새rollout을 완료했다. 0.5초1N의 기타36.077mm/4.757°는0N보다
0.014mm/0.00445°만 작고 LH이탈은 늘었다. 2N은회전이 악화됐으며 LH접촉0이다.
새길이를 채택하지 않고0N/기존PD를 유지한다. 후기1초와 새어깨PD는 이번에 적용하지 않았다.

사용자가 [어깨 stiffness 단독 비교](SHOULDER_PD_COMPARISON_PROPOSAL.md)를 승인했다.
양쪽 Shoulder6의 stiffness200→300만 변경하고 같은 PALM_RATE/초기각/LA로
기준·시험 각0.1초, 계약 통과 시 각0.5초를 검증한다. 구현은 별도 wrapper에 둔다.
기타 고정·상태 덮어쓰기·강제 부착·새 연주/학습 구조는 추가하지 않는다.

어깨 비교4fresh/288step 완료:300은0.5초구간 기타 최대35.780mm/4.551°로 조금 줄었지만,
LH이탈91.485mm·어깨scalar gap22.804°로200보다 악화됐다. LH접촉0과 실제scalar
한계위반이 남아300을 채택하지 않으며200/기존초기각/LA를 유지한다. 1초는 미측정이다.
후처리회전수치검사 실패와 수정은 보존했고 실제native 재실행은 없었다.
마지막0.5초 위치오차는34.773→35.780mm로 악화돼 후기 유지 개선으로 해석하지 않는다.

[원본 PD 경로 감사](PD_ACTUATION_PATH_AUDIT.md)는 native 실행 없이105축 nominal
gain/cap·정책30축씩·현재main66/torso9를 대조해6계약/101SHA를 통과했다.
원본 POS/stiffness0+force tensor와 현재 solver position PD는 구동 경로가 다르며,
공식 문서의 tensor EFFORT 요구와 원본 코드 차이는 실제 응답을 별도 확인해야 한다.
숫자 일치로 actuator 동등성이나 원본 오류를 주장하지 않는다.
[1축 CPU API 검증 제안](TENSOR_EFFORT_API_PROPOSAL.md)은 사용자 확인 전이며 미실행이다.

사용자가 위1축 API 진단을 승인했다. 별도6fresh/144step fixture 비교를 진행하며,
기존 main scene은 유지한다. 진단만으로 원본 구동 실패나 기타 안정화 성공을 주장하지 않는다.

승인진단6fresh/144step 완료: EFFORT±1Nm은약±0.11324°q 변화, POS±1Nm는
25개q/velocity가0Nm 기준과exact였다. Source±90°와native hasLimits=false를 구분하며
구간Δq/Δt와SDK완료-step velocity 차이는미확정이다. Main구동/gain/controller는유지한다.

2026-10-07 사용자 운영 변경: 필요한 실험 결정은 별도 승인 요청 없이 진행한다.
근거·조건·결과를 기록하며 원본 보존과 기타 고정/강제 부착/지속 상태 덮어쓰기 금지는 유지한다.
이전 단계의 “확인 전” 기록은 당시 이력이며 향후 작업을 승인 대기로 멈추는 규칙이 아니다.

## 현재 진행: 손가락 접촉과 기타 이탈 feedback

[FINGER_GRIP_HOLD_PLAN.md](FINGER_GRIP_HOLD_PLAN.md)에 따라 LH 12 finger의
source-clear 초기 grip과 양팔 24 PD 목표 preload, world-palm·기타 이탈 feedback을
검증했다. 1초 최대 기타 오차는 기준 20.341mm/5.283°에서 16.170mm/2.517°로
줄었으나 중지·약지 접촉은 약 0.55초 이후 소실하고 손바닥 접촉은 없다.
기타 정지 안정·지속 grip 성공으로 채택하지 않으며 다음에는 엄지의 반대쪽 지지를 검사한다.
root/하체는 물리적으로 고정하며 몸통 9 H0 목표·PD와 기존 passive strap 길이는 유지한다.
기타는 free/중력/내부 충돌 ON이며 runtime 상태 덮어쓰기는 없다.

진입점 `python -m stability_adapter_2.run_finger_grip_hold`의 선택 옵션
`--palm-feedback <native FK jacobian.json>`은 실제 기타 goal−actual 오차를 손 목표에
최대 10mm/축·0.05rad/축만 반영한다. 최종 arm 목표는 초기각 ±0.5rad ∩ native이며
palm 보정 ±0.15rad/1rad/s를 기존 PI/preload와 합성한다.
[결과·실제 Isaac Gym 전체 영상](../docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/README.md)을 따른다.

## 사용자 정정: 파란 넥 측면의 손바닥 지지

현재 우선순위는 [PALM_NECK_SIDE_SUPPORT_PLAN.md](PALM_NECK_SIDE_SUPPORT_PLAN.md)이다.
사용자 그림의 파란 영역에 손바닥이 닿는 조건을 먼저 다룬다. 이전 엄지 후속 계획은
이 손바닥 지지 검증 이후로 미룬다. 기존 초기 손바닥 source gap은77.050mm였다.
팔12 C02 box 내의 새 배치는 source gap0.049807mm/교차0이고 실제첫step에서
LH:palm–넥 manifold4점이 생겼지만 lambda0이며 step2~24에는 접촉이 사라졌다.
0.1초 최대 기타 이탈5.108mm/0.969°로 지속 지지 성공이 아니다.
[실제 Gym 비교 이미지·측정 결과](../docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/README.md)를 따른다.
다음에는 이 새 자세의 native Jacobian·목표 보정을 확인한 뒤 손가락 제어를 결합한다.

## 새 손바닥 배치의 목표 보정 비교

[PALM_SIDE_FEEDBACK_PLAN.md](PALM_SIDE_FEEDBACK_PLAN.md)에따라새palm facet추적점의
initial native FK와첫step PD목표응답을따로교정했다. initial±.15∩C02/native에서
OFF/bias/bias+blue-tracking0.1초를비교했다. source-facet 추적점최대이탈은71.910→49.466→48.324mm로
줄었지만palm접촉raw lambda0/후기소실과기타5.108mm/0.969°는그대로다. 유지성공이아니다.
실제Gym camera 재현은같은tracking raw5배열과exact다. [결과·비교 이미지](../docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/README.md)를따른다.
다음에는초기각을유지한runtime보정범위확장을먼저1step검증하며원본·이전phase는보존한다.

## 사용자 제안: 손바닥과 넥 바닥면의 평행성

[PALM_PLANE_ALIGNMENT_PLAN.md](PALM_PLANE_ALIGNMENT_PLAN.md)에 두 source 면의
평행성·법선 간격·접선 이탈을 구분했다. 새 초기 자세는 이미 거의 평행하지만 기존
tracking의0.1초 정렬각은4.750409°, 선택점의 법선 분리는40.495078mm다.
새 제어 후보는 손 전체 상대 회전 유지 대신 마주 보는 법선의 정렬을 부드럽게 유지하고
법선 주위 회전 여유를 남기는 것이다. 이 측정 당시에는 새 controller/physics 비교를 하지 않았다.
[측정·설명](../docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/README.md)을 따른다.

## 현재 진행: 법선 정렬과 runtime 목표 보정

[PALM_NORMAL_CONTROL_PLAN.md](PALM_NORMAL_CONTROL_PLAN.md)에 따라 기존 전체 상대회전
목표와 source 면 법선 정렬을 같은±.15 조건에서 비교했다. task교체만으로는
개선되지 않았다. 이어 초기각/기타/PD/LA를 유지하고 runtime 목표box만±.3/.5∩native로
비교해0.1초 point오차48.284→12.187/11.963mm, 법선각4.801→1.281/1.435°를 얻었다.
기타body states는같고palm접촉은step1~2 rawlambda0 뒤소실한다. 안정화성공은아니다.
±.3을다음진단의기준으로남기며 실제Gym 초기/0.1초camera raw6배열을재현했다.
[결과·이미지](../docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/README.md)를
따르고 다음에는짧은유한시간 PD목표응답과새자세의strap길이를별도비교한다.

## 현재 지지 목표의 우선순위

사용자 정정에 따라 평행성은 필수 조건이 아니라 지지를 돕는 부드러운 선호다.
실제 손바닥 지지와 기타 초기 위치·회전 유지가 우선이며 도움이 되는 기울기를 허용한다.
[다음 비교의 판단 기준](PALM_NORMAL_CONTROL_PLAN.md#사용자-정정-평행성보다-실제-지지를-우선)에 기록했다.
현재 코드에는 정확한 평행을 강제하는 제약이 없지만, 접촉 우선 제어는 아직 구현되지 않았다.

## 지지 우선 방향 가중치의 실제 비교

[PALM_SUPPORT_WEIGHT_PLAN.md](PALM_SUPPORT_WEIGHT_PLAN.md)의 같은 초기 자세·strap
비교에서 방향 scale .08/.02/0의0.1초 추적점 최대오차는12.187/12.448/17.168mm였다.
면각은1.281/1.282/6.955°이고 실제 기타 body states는 세 조건이 정확히 같다.
방향항을0으로 하면 접촉 기록은step3까지 늘지만 모두 rawlambda0이며 뒤에는 사라진다.
방향항 완화만으로 유효 지지·기타 안정화가 개선되지 않았다. 평행성은 여전히 선호이며
.08을 유지하는 이유를 각도만으로 설명하지 않는다. 기존 .08/±.3은 변경 전 진단 기준으로
남기고 유한시간 응답 측정과 절대strap 길이의 분리 비교를 이어간다.
[결과·곡선](../docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/README.md)에 기록한다.

## 새 손바닥 자세의 절대 스트랩 길이 비교

[PALM_SIDE_STRAP_PLAN.md](PALM_SIDE_STRAP_PLAN.md)에따라초기각/기타/손제어/PD를
유지하고current/taut/초기5N/10N의절대LA를비교했다. 0.1초기타최대이동은
5.108→3.720/3.355/2.536mm,회전은.969→.551/.461/.357°로줄었다.
10N의palm양의rawlambda는첫step한행뿐이며접촉은step4뒤사라진다. 종료장력0과
비영속도가남아최종길이로채택하지않으며5N도후기속도tradeoff를함께검증한다.
실제Gym10N camera는headless6raw와exact다. [결과·이미지](../docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/README.md)를따르고다음에는네조건의0.5초연속진단을따로기록한다.

## 스트랩 길이의0.5초 연속 비교

[PALM_SIDE_STRAP_LONG_PLAN.md](PALM_SIDE_STRAP_LONG_PLAN.md)의네조건120step을
처음부터연속실행했다. 각첫24step6raw는이전0.1초와exact다. 최대기타p/q는
current53.539mm/6.994°,taut60.944/9.232,5N60.592/9.328,10N60.020/9.534로
짧은길이의초기개선이후기개선으로이어지지않았다. 새길이를채택하지않는다.
current의손추적점최대오차47.437mm/종료법선gap34.275mm·후기접촉소실과
왼Shoulder_x actual−target24.218°가남는다. 원인을단정하지않고유한시간팔응답을
교정한다. 실제Gym current31시점camera는headless6raw와exact다.
[곡선·전체영상](../docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/README.md)에현재5init600step을기록한다.

## 손바닥 지지를 위한 유한시간 목표 응답

[PALM_FINITE_RESPONSE_PLAN.md](PALM_FINITE_RESPONSE_PLAN.md)에 따라 같은 초기q/기타/
LA/PD에서 왼팔12 constant startupbias 주변의0.1초 응답을 실제측정했다. 작은heldout
예측차이는0.000523mm였으나 큰보정에서접촉이생기면 기타오차도커졌다. 전체보정은
point14.208→6.671mm인반면 기타5.108mm/.969°→8.219mm/1.292°로 최종채택하지않는다.
1/4보정의기존tracking 분리비교는point12.187→9.712mm이나 손바닥rawlambda0/후기소실이
남는다. 평행성은선호이며 면각·손위치만좋다고기타유지성공으로판정하지않는다.
12개작은probe에서기타states는baseline과exact여서 기타응답은그국소범위에서식별되지않았다.
다음에는접촉이생기는경계에서손/기타응답을함께읽는다. 새B를feedback에넣지않았다.
총21init504steps, 실제Gym2조건camera5raw/headless exact를
[결과·비교이미지](../docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/README.md)에 기록한다.

## 접촉 구간의 손·기타 응답

[경계 비교](PALM_CONTACT_BOUNDARY_PLAN.md)의 새4init96steps에서 alpha.45는 step2에만
양의 palm raw lambda가 나타났고 .40보다 기타 이동/회전이 커졌다. 새 bias 채택은 없다.
[곡선·결과](../docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/README.md)에 기록한다.
[결합 응답 식별](PALM_COUPLED_RESPONSE_PLAN.md)은 .45 주변12축과 heldout을 각24step
실행했다(14init336steps). 기준 원자료5배열은 이전.45와exact이며 report는 새 경로 등
metadata가 다르므로 실행계약을 별도로 검증했다. heldout 예측차이는 손.030036mm,
기타.024734mm/.003647°다. 접촉은 여전히 초기 순간뿐이며 장기 안정성 인증이 아니다.
새 행렬은 손6+기타6의 유한시간 응답으로 실시간 feedback에 넣지 않았다.
다음은 [작은 결합 보정 검증](PALM_COUPLED_CORRECTION_PLAN.md)이다.

## 기타 오차를 함께 고려한 작은 상수 목표 보정

[결합 보정 계획](PALM_COUPLED_CORRECTION_PLAN.md)의 각 축 ±.001rad 후보를 1/4·1/2·전체로
각 24step 검증했다(3init/72steps). 전체는 손 추적점 9.289→9.113mm, 기타 최대 이동
5.341→5.099mm/회전 1.006→.973°로 줄었다. 양의 palm raw lambda는 step2 한 행뿐이고
종료 source gap 9.048mm가 남아 지속 지지나 안정 자세로 채택하지 않는다. 초기 q/기타/LA/PD는 동일하다.
원 fit producer와 실행 입력을 보존하고 입력 소비 시점만 고친 refit의 11개 결과 필드가 exact다.
기타 p/q feedback은 아직 없으며 [결과·그림](../docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/README.md)에 기록한다.
다음은 [관절 유지 관측](PALM_HOLD_OBSERVATION_PLAN.md)으로 팔 질량/drive property/total DOF force를
검사한다. 원인을 단정하거나 보정 폭/gain을 바로 키우지 않는다.

## 관절 유지 관측과 왼팔 PD 비교 결과

관측 2init/48step은 baseline/full 각 조건의 이전 원자료 5배열을 정확히 재현했다.
둘 다 계측한 실행이며 full은 작은 목표각 보정 조건이다. native 질량과 PD property,
완료 step의 total DOF force를 읽었으나 drive-only torque나 포화 원인은 확인하지 않았다.
[관측 결과·그림](../docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/README.md)을 따른다.

[PD 비교 계획](PALM_HOLD_PD_PLAN.md)에 따라 왼팔12 kp/kd를 1/1.5/2배로 바꿨다.
초기 자세·기타·LA·상수 목표는 같다. API 성공 반환값 검사를 보완한 v2의 최대 기타
이동은 5.099/5.631/6.145mm, 회전은 0.973/1.039/1.100°로 gain 증가를 채택하지 않는다.
손바닥 양의 raw lambda는 step2 이후 유지되지 않는다. 첫 v1 3init/72step과 보완 v2
3init/72step을 구분해 보존하며 같은 배율의 원자료5배열은 exact다.
[결과·설명](../docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/README.md),
[보완 검증 기록](PALM_HOLD_PD_VERIFICATION.md), [다음 강성 분리 계획](PALM_STIFFNESS_ONLY_PLAN.md)을 따른다.
기타 초기 p/q를 직접 읽는 실시간 feedback과 학습은 아직 구현하지 않았다.

## 새 실험의 기본 기록: 초기 값과 실제 Gym5초 영상

사용자 요청에 따라 앞으로 각 실험의 초기 값과 실제 Isaac Gym0~5초 영상을 남긴다.
상수 목표 비교는 `python -m stability_adapter_2.run_recorded_trial --trial <JSON> --out <새 경로>`를
사용한다. 초기 settings/실제81각/기타 world p·xyzw q/PD/절대LA를 저장하고,
전신·손 근접 두 영상을30fps로 만든다. t0 및 endpoint 포함151frame≈5.033초다.
과거0.1초 결과는 보존한다. 새 feedback runner에서도 동일 녹화 helper를 사용한다.
[녹화 계획](FIVE_SECOND_RECORDING_PLAN.md)과 [검증 결과](../docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/README.md)를 따른다.

## 왼팔 stiffness-only 5초 비교와 다음 초기 strap 변경

같은 초기 자세/LA/목표의 왼팔 kp1/1.5/2, kd1을 각각5초 실행했다. 최대 기타 오차는
82.047/246.612/241.007mm,10.831/76.100/74.383°로 상향gain을 채택하지 않는다.
초기자세와 스트랩 후보 탐색을 이어가며 다음은 [5초 strap 초기길이 비교](STRAP_FIVE_SECOND_PLAN.md)다.
결과·실제 영상은 [stiffness-only 결과](../docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/README.md)를 따른다.

## 엄지 후면·손가락 전면·손바닥 옆면 접근 비교

왼팔12와 왼손21의 초기각을 조정한 두 감싸기 후보와 기준을 실제Gym에서 각각5초
실행했다(3init/3600step). 초기값과 전신·손근접 영상은
[결과·그림](../docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/README.md)에 저장한다.
seed2 최대 기타오차는26.773mm/8.323°로 기준82.047mm/10.831°보다 작다.
엄지·검지·중지는 종료step에도 양의 raw lambda가 있지만 palm의 마지막 양의 raw lambda는step121이다.
값이0인 palm 접촉행은step134까지 있으며 전체 접촉행 소실과 구별한다.
초기 palm측면3.842mm/엄지후면5.831mm 간격이 남아 세면 동시 초기지지를 달성하지 못했다.
접촉은 body쌍 기록이며 면별 지지나 안정화 성공으로 해석하지 않는다.
기타/root/하체/몸통9목표/오른손/LA/PD와 기존 startupoffset 법칙은 유지했다.
왼쪽33축은 이번 초기 자세 탐색 범위이며 최종66관절 제어 범위를 축소하지 않는다.
다음은 [손바닥 지지 보완 계획](MULTI_FACE_GRIP_PALM_REFINEMENT_PLAN.md)이다.

## seed2 손바닥 접근 보완의 실제5초 결과

국소 초기각8후보 중 source안전·거리개선5개를 찾고 half/quarter 두후보를 각각5초
실행했다(2init/2400step). half는 fresh native 초기6면 gap≤3mm를 달성했지만
기타 최대오차29.575mm/8.691°로 이전seed2의26.773mm/8.323°보다 커졌다.
quarter도28.296mm/8.436°로 두보정을 채택하지 않는다. 초기근접은 실제유지성과 다르다.
양조건palm의 양의rawλ는step112/142가 마지막이고 λ0접촉행은122/149까지 남았다.
[결과·초기값·실제영상](../docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/README.md)에 기록한다.
다음은 원seed2초기각을 유지하며 약15.237mm strap초기여유를 줄이는
[새LA3조건 비교 계획](SEED2_STRAP_INITIAL_PLAN.md)이다. 아직실행하지않았으며
기타p/q feedback·학습·안정화성공도 아직 없다.


## 새 감싸기 자세의 초기 스트랩 길이 비교

[SEED2_STRAP_INITIAL_PLAN.md](SEED2_STRAP_INITIAL_PLAN.md)의 actualGym3init/3600step을 완료했다.
seed2초기각을 유지하고 절대LA만current/taut/preload5n으로 바꿨다. 각초기값과
전신·손0~5초151frame 영상은 [결과](../docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/README.md)에 둔다.
current전체5초 원자료5배열은 이전seed2와exact다. 실제초기81q·PD·기타p/q·속도·solver가 같고
LA/직전상태 기반strap법칙/영상/입력봉인8검사를 통과했다.

짧은LA는0.1초p/q를5.108mm/.969°에서3.545mm/.505°와3.197mm/.428°로 줄였지만,
5초최대이동은26.773→35.020/35.293mm로 커졌다. 최대회전은8.323→7.543/7.516°로
줄어 이동과회전tradeoff를 구분한다. 종료이동·회전도current가 작아 다음진단기준으로 유지한다.
짧은LA는palm/middle 접촉기록을 늘렸으나 thumb/index후기소실이 남는다.
이는body쌍 관측이며 사용자요청의rear/front/side접촉과 연속지지를 인증하지 않는다.

다음 [시작 목표각 비교](SEED2_STARTUP_TARGET_PLAN.md)는 새초기q에 남아 있는
기존왼팔12bias의OFF/절반/기존값 비교다. 첫왼Shoulder_x목표 변화−17.0104°가
측정됐으나 원인으로 단정하지 않는다. 아직미실행이다. 상체9초기목표/양쪽66제어권과
자유기타/root하체고정/자기충돌 조건은 유지하며 기타복원feedback과학습은 아직없다.


## 새 감싸기 자세의 시작 목표각 보정 비교

[SEED2_STARTUP_TARGET_PLAN.md](SEED2_STARTUP_TARGET_PLAN.md)의0/.5/1배 비교를
같은초기q/기타p/q/LA/PD/solver에서 실제3init/3600step으로 완료했다.
각초기값·전신/손5초영상과 접촉기록은 [결과](../docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/README.md)에 둔다.
처음0.1초 최대p/q는33.015mm/4.619°,12.365mm/1.919°,5.108mm/.969°,
5초 최대값은158.088mm/26.355°,120.157mm/21.524°,26.773mm/8.323°다.
OFF/절반을 채택하지 않고fullbias/currentLA를 다음 진단 기준으로 유지한다.
full 원자료5배열은직전current와 처음24step 및 전체5초가 exact다.

실제제출목표 변화0/8.5052/17.0104°와 실제팔좌표편차를 분리해 측정했다.
왼팔12 외69목표는유지했고 양쪽66제어인터페이스도유지했다. 세조건 오른손–기타접촉은0행이었다.
half의palm 양λ는끝까지 기록돼도 기타오차가120mm여서 접촉만으로성공을판정하지 않는다.
초기6부위source접근 통합조건은미달이며 넥면별 지속지지·안정화는아직미완성이다.

다음 [기타 응답 식별](SEED2_GUITAR_RESPONSE_PLAN.md)은 연주목표66+지지bias+기타오차 residual의
합성 관계를 명시하고 작은6축목표probe/heldout을 실제5초로 확인하는 계획이다.
아직미실행이며 학습구조를 먼저 확정하지 않는다. 기타는자유/root와하체는물리적고정,
몸통9초기PD목표유지/self-collisionON조건은같다.


## 감싸기 지지의 작은 목표 보정: 실제 응답과 별도 검증

[작은 기타 응답 계획](SEED2_GUITAR_RESPONSE_PLAN.md)의 기준+6probe와
[결합 검증 선택](SEED2_HELDOUT_SELECTION_PLAN.md)을 실제8init/9600step으로 완료했다.
같은초기81q/기타p/q·속도/LA1.1018469719600776m/PD/solver에서 Shoulder/Wrist의
PD목표만변경했다. 각초기값과실제Gym전신/손0~5초151frame영상은
[결과·영상·변경파일](../docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/README.md)에 둔다.

결합heldout 최대p/q는26.774777mm/8.124454°로 기준26.772807mm/8.323296°보다
최대이동0.001970mm늘고 최대회전0.198842°줄었다. 종료p/q는23.108978mm/7.388837°다.
작은회전개선후보로보존하고 초기seed2/full/currentLA를진단기준으로 유지한다.
기준원자료5배열의처음24step과전체5초가직전full과exact이며 probe/heldout8검사씩통과했다.

0.1초샘플의6×6응답은rank0, last1s잠정rotationlever.1m 가중rank6/조건수56647이다.
last1s선형예측잔차 .789333mm/.155463°가 실제기준대비변화 .152794mm/.028116°보다커서
행렬을runtime기타복원feedback에사용하지않는다. 요청±.001rad와float32실제제출차를구분한다.
초기source접근6부위통합조건은미달이고 heldoutpalm양λ117/전체행135 이후소실,
thumb/index/middle마지막양λ1200/RH0행이다. 면별지지·연속지지·cooked관통인증은아직없다.
root/하체물리고정·기타자유/self-collisionON/몸통9초기PD목표·양쪽66제어권을 유지한다.

다음 [음의방향과 결합근사 확인](SEED2_RESPONSE_LOCALITY_PLAN.md)은 새3개5초비교다.
아직실행하지않았다. 초기값을유지한응답진단이며 정책·학습은결정하지않는다.

독립검수는 raw8실행·응답/예측 재계산·법칙9600구간·PNG2 직접QA·31입력SHA와문서를
대조해C/W/S없음으로완료했다. [검수기록](../docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/review.md),
[보존·소스봉인](../docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/final_verification.json)을 남긴다.


## 작은 목표 응답의 음의방향과 결합절반 비교

[SEED2_RESPONSE_LOCALITY_PLAN.md](SEED2_RESPONSE_LOCALITY_PLAN.md)의새3init/3600step을완료했다.
같은초기81q/G/LA/PD/solver에서 negativeShoulder_y/negativeWrist_z -.002rad와oldheldout0.5배를
실제각5초·전신/손151frame로기록했다. [결과·초기값·영상](../docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/README.md)을남긴다.
과거기준/양의probe/heldout은savedreference이고새3회에포함하지않는다.

음의Y최대p/q26.684900mm/8.116260°와종료22.883315mm/7.338493°는기준보다모두작았다.
음의Wz최대회전8.377872°, half최대이동26.938437mm는커져채택하지않는다.
가중6×2끝점차분의last1srank2/조건수4.805는잠정.1mlever의국소근사다.
0각보간잔차와half oldJ예측잔차.481436mm/.084446°가남아정확한runtime mapping으로쓰지않는다.
half actualtargetalpha=.500009933989와요청0.5를구분했고첫0..24Gpose는세조건모두savedbase와exact다.

새3조건R_Hip–기타양λstepcount는1200이고 RH손–기타는0행이다. palm양λlast118/124/123,
전체행last134/133/134이후소실과초기6source접근미달은남는다. body기록으로면별지지/힘/관통을인증하지않는다.
기타자유중력·root/하체물리고정·몸통9초기PD목표유지/selfcollisionON·최종66제어권을유지했다.

다음 [어깨크기와기타오차feedback](SEED2_SHOULDER_GUITAR_FEEDBACK_PLAN.md)은 상수-.008/-.016rad와
G6오차를읽는1축boundedPD목표보정의새3조건비교다. 이후아래단계에서실행했다. 1축은진단용이고최종66을축소하지않는다.
초기p/q복원·유지나연주중안정화의성공과학습구조확정은아직없다.

원자료의G오차/양음차분/half보간과실제영상·설명을독립검수했다.
그림producer의초기exact관측을통과조건으로쓰던guard는boolean형식검사로바꿨다.
수정전성공producer/그림/manifest/로그를SHAexact로보존했고재생성PNG는같은bytes다.
[최종검증과원본보존](../docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/final_verification.json)과
[변경파일·실제줄](../docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/CHANGED_FILES.md)을기록한다.

## 어깨 보정 크기와 실제 기타 오차 feedback 비교

같은81개초기각/Gp·q/LA1.1018469719600776m/PD/solver에서새3조건을각5초실행했다.
상수L_Shoulder_y-.008/-.016rad와G오차를읽는60Hz목표보정을비교했다.
원producer는source_final SHA와대조후새prepare/runner/analyzer로복사하고보존했다.
초기값·전신/손0~5초151frame·원자료와 [결과설명](../docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/README.md)을남긴다.

최대p/q는-.00825.929259mm/7.900654°, -.01625.280921mm/7.753357°,
feedback26.950260mm/8.210682°였다. 상수-.016의종료는21.989056mm/7.096635°,
feedback종료21.953773mm/7.096483°이나최대이동은원기준26.772807mm보다커졌다.
원seed2/full/currentLA를공통진단기준으로유지하고-.016을새지지목표후보로보존한다.
feedback채택·안정화성공·학습구조확정은아직없다.

feedback은2.233333초에-.016한계에도달했다(180/300갱신). 상향proxy위반/보류는0이다.
속도제한후요청rate≤.008rad/s와실제float32제출목표최대rate.008003711700439453rad/s를구별한다.
비활성상수조건의계산rate는적용하지않으며실제δ증분0이다. 300갱신을pre-step상태로재계산했다.
검지의마지막양λ는87/95/255step, palm양λ123/124/124·전체131/138/136step이후소실했다.
엄지/중지양λ는종료1200step에도관측됐으며R_Hip양λ고유step1200/RH0행이다.
body명과rawλ는넥면/연속지지/뉴턴힘/관통인증이아니다. source6초기접근미달은남는다.
몸통9목표유지중실제최대좌표편차약4.22°를별도로측정했다.

기타자유·중력·수동strap/root하체물리고정/selfcollisionON과양쪽Thorax→손가락66최종제어권을유지했다.
1축은진단용이며기타를당기는목표힘/고정/손부착/pose덮어쓰기를사용하지않았다.
[다음초기지지자세비교](SEED2_SUPPORT_POSE_WARMSTART_PLAN.md)는관측된왼쪽33종료각의일부를초기값에
반영하고같은절대PD목표를유지한다. 아직미실행이며몸통/오른팔손/G/LA/PD조건은유지한다.
초기복원·유지와연주중안정화는미완료다.

세run의원자료와제어식·제출목표·접촉, 실제영상/그림과설명을별도검수했다.
[검수결과](../docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/review.md)와
[최종보존검증](../docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/final_verification.json),
[변경파일·실제줄](../docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/CHANGED_FILES.md)을기록한다.
산출물에이전트의이전단계문서수정은원snapshot/SHA로복원했고시도는새run아래보존했다.


## 세 면 접근 초기각과 같은 절대 PD 목표 비교

엄지 후면·네손가락 전면·손바닥 옆면을 목표로 기존 source검증 quarter/half 초기33각을 가져와, 저장 -.016 조건의 절대81 PD목표를 유지한 새3회/3600step을 완료했다. 직접 종료각 보간과 투영 후보는 초기검사에서 거절했고 native0으로 소스/로그를 보존했다.

half는 초기 여섯 source hull–면 패치 거리가 모두3mm 이내였고 첫.1초 이동4.718710mm는 기준5.107730mm보다 작았다. 5초 최대25.229274mm/7.770624°로 기준25.280921mm/7.753357°보다 최대이동은 .051647mm 작고 최대회전은 .017267° 컸다. 손바닥/검지 접촉도 지속되지 않아 성공이나 기준교체로 해석하지 않는다.

각 초기값과 실제Gym 전신/손0~5초151frame 영상·이미지설명은 [새 결과](../docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/README.md)에 둔다. 기준반복physics원자료4배열과 두 영상은 저장 -.016과exact이며 새controls는81목표 schema로 달라졌다. 목표유지와 실제몸통4.23° 좌표편차를 구분한다. root/하체물리고정·기타자유·selfcollisionON·최종66제어권을 유지했다.

다음 [손가락 목표 분리 계획](THREE_FACE_FINGER_TARGET_HOLD_PLAN.md)은 half초기각에서 손가락21 목표만 저장절대값/새초기값으로 비교하는 미실행 계획이다. 기타/스트랩/팔 절대목표와gain은 고정한다. 면별 지속지지·초기복원·연주중 안정화와 학습구조는 아직 미완료다.


## 같은 초기 자세에서 손가락 목표21만 변경

[손가락 목표 비교](THREE_FACE_FINGER_TARGET_HOLD_PLAN.md)를 같은half 초기81q/G/LA/PD/solver로 새2회/2400step 실행했다. frozen기록runner를 수정하지 않고 새proposal을 전달했고 팔12/다른48 목표·최종66권한을 유지했다. 새finger21목표는 첫.1초3.933977mm/.872048°로 줄었으나 최대이동26.111870mm와 종료26.047250mm/7.714785°는 저장목표25.229274mm·21.912505mm/7.091529°보다 커졌다. 손가락 초기목표 유지 조건은 채택하지 않는다.

초기값·실제전신/손5초영상·접촉시점그림·설명은 [새 결과](../docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/README.md)에 남긴다. 반복5개원자료배열과2영상exact는 관측이며 통과gate가 아니다. index양λlast81→106·고유23→33, palm고유30→50이나last123같음이며 면별지지/안정화 성공은 아니다. [다음 실제지지소실 진단](THREE_FACE_SUPPORT_LOSS_DIAGNOSTIC_PLAN.md)은 미실행이며 다음목표/gain/material은 진단후 정한다. 자유기타·root하체물리고정/selfcollisionON/몸통9목표유지/66제어권은 같다.


## 세 면 지지 소실의 실제 자세와 SDK 물성 진단

같은 saved_finger_targets 설정1회/1200step 실제5초와 두 기존 조건의 actualbodypose0/.1/.25/.5/1/5초를 분석했다. Native human55/guitar28 shape friction은 모두1.0이며 조회전후 state/PD/Python 제출목표가 같았다. 손바닥 source옆면 간격은 saved2.129621→9.894188mm, initialfinger2.129621→5.392989mm였고 지정facet 방향 dot은 .994→.979/.978로 유지됐다. 방향이 비슷해도 위치지지는 유지되지 않았으며 source거리로 실제면별접촉을 인증하지 않는다.

첫 목표 제출 전 Shoulder_x actual-minus-plannedtarget은 이미 .288445rad, 종료 .378943/.379285rad였다. 초기 배치와 저장 팔 목표의 불일치와 이후 실제 이동을 구분한다. 지정thumbfacet inwarddot도 초기−.816388이며 해부학적pad 정체성은 미확인이다. [초기값·실제영상·기하진단 설명](../docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/README.md)을 남긴다. 다음 [팔 초기목표 일치 비교](THREE_FACE_ARM_INITIAL_TARGET_PLAN.md)는 미실행2조건이며 gain/material/strap/초기q를 바꾸지 않는다. 기타초기 복원·지속지지·연주중 안정화는 아직 미완료다.


## 초기 팔 목표 일치 비교 결과 — three_face_arm_initial_target_v1

왼팔12 PD목표를 half 실제초기각으로 맞춘 새2회5초/2400step을 완료했다. 손가락21은 기존목표/초기목표로 분리했고 초기81q/G/LA/PD/solver와 나머지48목표는 같았다. 최대159.799114mm/25.272466°와157.516483mm/25.623971°, 종료159.795174mm/25.142339°와157.510653mm/24.868219°로 저장기준 최대25.229274mm/7.770624°보다 악화돼 두 조건을 채택하지 않는다. 각각 Gym 손/전신0~5초151frame 영상과 초기값을 남긴다.

두 실행의 passive strap 제출장력은 전체1200step에서0N이었다. 초기 route1.0868332051527874m·LA1.1018469719600776m로 여유15.013767mm이다. 이는 해당 경로의 관측이며 단독 원인이나 strap 비활성화를 뜻하지 않는다. [새 결과/그림/영상](../docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/README.md)과 [변경파일 실제줄](../docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/CHANGED_FILES.md)을 따른다. 다음 [half 초기자세 스트랩 여유 비교](THREE_FACE_HALF_STRAP_SLACK_PLAN.md)는 기존 절대목표로 돌아가 여유7.506883mm/0mm 길이2조건을 비교하는 미실행 계획이다. 자유 기타 초기복원·세면 지속지지·연주 안정화는 미완료다.


## half 초기 자세의 스트랩 여유 비교 — three_face_half_strap_slack_v1

저장half 실제초기81q와 기존절대81목표를유지하고 LA만1.0943400885564325/1.0868332051527874m로변경한새2회5초/2400step을완료했다. 최대이동30.696048/32.861798mm·회전7.727219/7.103582°, 종료30.695007/32.860232mm·7.622948/7.103303°다. 최대회전이줄어도 위치최대/종료및종료회전이저장기준보다커두길이는채택하지않는다. 몸통9PD목표·고정root하체·최종양쪽66제어권과gain/material/solver를그대로유지했다.

Palm body 양λ기록은두조건last1200이나thumb3는35/96까지만있다. 이는요청된넥면/접촉력N/연속지지인증이아니다. Passive법칙 최대12.894182/5.119047N·종료1.063010/2.677263N과원자료재계산오차0을확인했다. [초기값·비교그림·실제Gym영상](../docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/README.md), [변경파일 실제줄](../docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/CHANGED_FILES.md)에기록한다. 다음 [native contact feature 위치 진단](THREE_FACE_NATIVE_FEATURE_MAP_PLAN.md)은 저장3조건을읽어후면/전면/옆면근접을검토하는offline미실행계획이다. 전체초기복원·세면지속지지·연주안정화는미완료다.


## 세 면 접촉 feature 위치 진단 — 저장 자료 분석

저장3조건의5초 접촉/pose3600records에서15511LH–기타feature행을G-root 좌표로 대조했다. 새native/physics0이며 [결과와실제Gym프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/README.md)에그림3개와기존영상출처를둔다. 요청옆면patch의palm투영내부0·거리21~30mm, thumb후면가장자리, index/middle의fret4/5접촉으로현재세면grip은달성하지못했다. SDKnormal방향과sourceoutward이반대로관측되어두부호를분리하고geometry분류gate로사용하지않았다. v1소스/입출력을exact보존후새v2분석을만들었다.

다음 [접촉footprint 재설계](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_CONTACT_FOOTPRINT_PLAN.md:1)는현재각주변FK민감도/source후보를먼저검사하며기존LA·gain·절대목표를유지한다. 계획은미실행이고root하체물리고정·몸통9목표·최종양쪽66제어권및자유기타조건은같다. root의원자료/그림QA는완료했지만canonicalv2/그림최종독립검수는에이전트도구thread limit오류로보류했다. 부분검수와최종검수는구분한다. 안정화/초기복원/연주학습은미완료다.


## 접촉 footprint 후보의 source 검사

현재각 주변 팔12±.05rad·엄지5±.10rad의네source 후보를 검사했다. V1은대표점목표오차.06mm이내지만wholepalm/thumb3교차로거절됐고, fullhull 분리를더한V2는교차0이나thumb대표점이rear패치밖.201/.395mm라거절됐다. 승인0/새native·physics0이다. 목표81/gain/LA/기타p·q/나머지64초기좌표를유지했다. [후보그림·조건·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/README.md)에 source 이미지와이전실제영상출처를구별해둔다.

Source V1/V2와직전feature-mapv2/PNG3개독립검수를완료했다. 새summary/그림재호출은thread limit으로보류다. 자기stdout로그입력봉인문제를 발견해원본을보존하고 explicit inputs의새분석v2로수정했다. 네후보수치는exact 같다. 다음 [후면지향source면 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md:13)은 미실행이다. 관측thumb 면은+GX를향해후면지지에맞는다른활성source면을찾는다. 실제면/해부학적pad/cooked인증이나초기복원·연주안정화성공은아니다.


## 후면지향 엄지 면의 초기 배치 비교

367개rear-facing active source triangle중최대면적323을anchor로삼아엄지±.10/±.20rad와clearance.3/.7mm의네source후보를완료했다. thumb점오차12.61~14.50mm·patch밖9.21~10.55mm와source교차가남아모두거절했다. 새native/physics0이며root하체물리고정/몸통9PD목표/최종66권한·old81T/other64/G/LA/gain조건을유지했다. 마지막palm오차1.810477mm가줄어도grip이나기타안정성공은아니다.

첫QP수치중단을source/log/12파일exact보존후새v2로복구했다. 실제8source거리witness를독립재계산해hull/patch포함과primal/dual구간을확인했고solverflag false를최적해로표현하지않는다. [결과·새source그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/README.md:1), [변경파일·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/CHANGED_FILES.md:1)을남긴다. 기존footprint 요약/PNG최종독립검수도새phase의previous_postprocessing_review.md에서완료했다. 다음 [접근성catalog](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_CATALOG_PLAN.md:1)은아직미실행이다.

이번네source후보/8실제거리/source교차·summary/PNG·문서/SHA의최종독립검수는C/W/S0으로완료했다. 실제물리실행은후보거절때문에0이며stablegrip/초기복원·연주안정화는아직미완료다.


## 근접 후면 엄지 지점과 손가락 초기 배치

367개 후면지향source면에서 가까운303/1462를 골라 네 초기각 후보를 검사했다. 엄지 목표 오차가7.52~8.57mm로 이전 최대면 후보보다 줄었지만 후면 패치 밖의 지점과source겹침이 남아 모두 거절했다. 새실제5초/native실행은0이다. [두 이미지와 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/README.md:1), [후속 검지·중지 초기각 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_FRONT_FINGER_INITIAL_PLAN.md:1)에 기록한다. Root·하체 물리고정/몸통9목표/최종66제어권/자유기타·수동strap 조건을 유지한다. catalog 및 검색 사전 독립 검수는 완료, 결과·그림 최종 독립 검수는 도구thread limit으로 보류했다. 기타 초기복원·지속 세 면 지지·연주 안정화는 계속 진행한다.


## 검지·중지 초기각과 전면 이동 허용 검색

25초기좌표의 source후보6개를완료했지만모두겹침/지지조건미달로거절했다. 새native/physics0이며그림2개/12거리witness·전체교차/81목표대조를완료했다. [새결과/설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/README.md:1)과 [전체왼손을더한후속계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_WIDER_HAND_INITIAL_PLAN.md:1)에기록한다. 최종양팔·양손66권한은유지하며33은다음초기배치탐색의일시범위다. 독립검수는도구thread limit으로보류했고안정화성공으로표시하지않는다.


## 엄지후면·네손가락전면·손바닥옆면근접 자세의실제5초

추가source15후보는모두지지조건미달이었다. 겹침없는근접후보로같은81초기각/LA의두actual5초를기록했고손가락21전체초기목표는최대이동25.779645→37.615076mm/회전7.800837→8.587915°로악화해채택하지않는다. 엄지후면과손가락전면근접feature는있어도palm요청옆면근접은둘다0이므로세면grip성공이아니다. [초기값·실제영상4개·그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/README.md:1)에남긴다. 다음 [손바닥옆면우선계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_PATCH_PRIORITY_INITIAL_PLAN.md:1)은미실행이며기존81목표/LA를유지해요청patch부터맞춘다. 최종66권한/몸통9PD목표/자유기타·수동strap/root하체물리고정은유지한다. Luna/독립검수도구한도로이번산출물은root가만들었고독립승인완료로표시하지않는다.


## 결과영상의 스트랩 경로 표시 — 기본 사용

앞으로 새결과영상은 실제route를주황실선/가려진옅은점선으로표시한다. 실제5초검증에서원자료5배열과raw nativePNG302개는직전입력실행과exact같았고기타물리상태·힘·gain변경은없다. [초기/종료이미지설명·전신/손영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/README.md:1)에저장했다. 새상수trial의기본entry는run_strap_recorded_trial, 근접진단은run_strap_recorded_diagnostic이다. 새feedback runner도StrapTrialRecording을연결한다. 기존frozen영상/runner는보존한다. 천mesh/처짐이아닌기존passive routed cable의실제경로표시이며독립검수는도구한도로보류했다.


## 손바닥 옆면 우선 초기 자세와 실제 스트랩 영상 — 소단계 완료

두 source후보는 모두 지지조건 미달이다. 겹침0 근접 후보 한 actual5초·1200step과 스트랩 포함151frame 전신/손 영상을 완료했다. 초기 손바닥 source gap0.421670mm이나 요청옆면 SDK근접0이며 기타 최대26.091583mm/7.937143°로 직전25.779645mm/7.800837°보다 조금 커 채택하지 않는다. 엄지후면 근접793step/last1200·중지전면1052/last1200은 부분 관측이다. Bodyλ는 실제면/힘N/연속지지 인증이 아니다.

[초기값·영상·두 그림 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/README.md:1), [변경파일 실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/CHANGED_FILES.md:1)에 기록한다. Source12검사/4거리witness·150벌점동등성·native/원자료·SDK4304행·10시점 Chest/팔 vector재계산과 actualPNG QA를 완료했다. 기존81목표/LA/나머지48·root하체fixed/몸통9목표/최종66권한·자유기타/passive strap은 유지했다. 독립검수/Luna 도구한도로 root가 작성했으며 독립승인으로 표시하지 않는다.

다음 [native 충돌형상·몸통9 PD 계획](/home/ajou/yigyu/3/stability_adapter_2/TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md:1)은 미실행이다. 실제몸통drift4.231250°와 초기 source근접 시 SDK손바닥contact 부재를 분리해 확인한 후 body9 gain만 비교한다. 기타 초기복원·유지·연주중 안정화는 계속 진행하며 학습구조는 아직 확정하지 않는다.


## 몸통9 PD 유지 비교 — 실제한5초와초기조회 완료

같은initial81/G/old81T/LA에서body9 stiffness×2·damping×√2만변경했다. actual1200step/두151frame스트랩영상의최대G오차26.091583→14.052228mm/7.937143→2.884291°로줄고body최대좌표4.231250→3.536898°였다. 하지만palm contact0/요청side0이고thumb후면793→3step·middle전면1052→12step으로줄어세면지지성공으로채택하지않는다. body×2는후속지지제어의임시진단기준으로만보존한다.

별도initialnative조회1회/physics0에서human55/G28shape·정책과기존initialstate/PD/target을exact확인했다. Collisioncamera rawRGB는normalcamera와exact같아별도cookedmesh인증으로보지않는다. 초기black해석을재열기후v2관측에정정했고원v1을보존했다. [초기값/영상/두그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/README.md:1), [변경파일실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/CHANGED_FILES.md:1)에남긴다. 독립검수/Luna도구threadlimit으로root자체검증과구분한다.

[다음계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_SUPPORT_RESIDUAL_AT_BODY9_PLAN.md:1)은현재native/FK대조·palm민감도계산부터진행하는미실행단위다. 기존81목표+boundedpalm residual을검토하고기타초기p/q복원·66연주권한과의관계를측정후학습구조를정한다. root하체fixed·몸통9목표/나머지72properties·자유G/passivestrap·기타고정/부착/poseoverwrite금지조건은유지한다. 전체목표는계속진행한다.


## 현재native/FK대조와palm residual 준비 — offline계측완료

저장body9×2의0/.1/.5/5초와추가20시점actualq/bodypose를t0한번calibrate한FK와대조했다. 추가native/physics0이다. 전체손FK는두좌표회전네가설모두미달했고약지손끝오차가약1.22mm까지누적됐다. 원인은아직확정하지않는다. Palm/팔24시점origin최대0.000312034/0.000278428mm·rotation약6.38e-7rad는잘맞았다. 전체손실패를palm범위통과로바꾸지않는다.

[원자료/두그림설명·실제baseline영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/README.md:1), [변경파일실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/CHANGED_FILES.md:1)에남긴다. 기하dq의PD목표경계만통과했으며runtime접촉/안정화개선은아직검증하지않았다. Root실제PNG QA·자료검증완료,독립검수/Luna는도구threadlimit으로보류다.

[다음계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_MEASURED_POSE_RESIDUAL_PLAN.md:1)은actualfingerbodypose의source mesh와검증된팔12기하제안의전체손겹침·상향을먼저확인한다. 센서pose로현재형상을읽고physicsstate를덮어쓰지않는다. Finger21예측실패는유지하며기존81목표+boundedpalm residual의안전범위/PD반응확인후실제5초를진행한다. 최종66제어권과initialG p/q복원/유지·세면지지·연주안정화전체목표는그대로다.


## Palm 단독 접근 형상 진단과 단일 축 손가락 검증 완료

직전 body9×2의 저장0/0.1/0.5/5초를 이용해16 source 배치를 조회했다. 신규12제안 중 t0 quarter만 선별을 통과하고 이후에는 검지·중지–기타 교차 증가가 있어 이 팔12 방향의 native ON을 실행하지 않았다. 손바닥 대표점 접근만으로 전체손 지지가 안전해지지 않았다. 추가 native/physics는0이다.

엄지2/3·검지2/3·중지2/3의 actual parent 조건부 예측은24시점/144행에서 기존0.1mm/1mrad 경계를 통과했다. 전체손 finger1 모델 실패는 유지한다. [그림·설명·기준 실제 스트랩 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_measured_geometry_v1/README.md:1), [실제 변경 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_measured_geometry_v1/CHANGED_FILES.md:1)에 남긴다.

[다음 팔12+손가락6 연동 source 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_FINGER_COUPLED_SOURCE_PLAN.md:1)은 미실행이다. Source 각도 범위/PD 경계와 전체손 형상을 함께 확인한 뒤 실제5초를 진행한다. 최종66 연주권한·자유G·하체root 고정·몸통목표와 기타 초기p/q 복원·유지 목표는 유지한다. 새 영상은 실제 passive strap 경로를 필수 표시한다. Luna/독립검수는 도구한도로 root 수행과 구분한다.


## 영상 모음 — 사용자 요청 완료

기존 results의120개 영상(약25.08MiB)을 [videos](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos)에 원본과 같은 바이트로 복사했다. [VIDEO_INDEX.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX.md:1)는 최근 실제 스트랩 영상과 전체 출처를 묶는다. 원본 이동·변경/재인코딩/물리 재실행은 없다. 복사/목록은 root가 작성했으며 Luna/독립검수는 도구 thread 한도로 미완료다. 후속 영상이 생기면 원본을 유지하며 별도 갱신 단위로 모음에 추가한다.


## 미세 떨림 허용 — 정지 유지 기준 채택

사용자 판단을 반영해 현재 실제 body9PD×2 기록의2~5초 정지 유지는 실용적으로 상당 부분 만족한 것으로 평가한다. 해당 구간 위치차이 최대0.001899241mm/회전차이0.001245157°다. 완전한 평형/속도0을 필수 조건으로 두지 않는다. 초기이탈14.050564mm/2.856298°와 손·팔 움직임 중 유지는 별도 평가한다. [결정](/home/ajou/yigyu/3/stability_adapter_2/QUIET_HOLD_BASELINE_DECISION.md:1), [수치·기존영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/practical_stability_assessment_v1/README.md:1)을 기록했다. 원본 report 변경/새물리 실행은0이며 다음 단계는 이 설정에서 작은 손·팔 움직임의 실제 유지성 확인이다.


## 작은 왼손목 움직임 — 실제5초 완료

현재정지유지기준과t0/PD/LA를같게두고L_Wrist_x목표만±0.005rad·1Hz로t0부터움직였다. 한actual1200step/두151frame스트랩영상과12분석검사완료. 실제좌표응답진폭0.146929°·palmworld원점차0.495638mm이고2~5초G변화는0.481766mm/0.091929°였다. 전체최대초기오차14.132608mm/2.894328°로기준14.052228mm/2.884291°보다조금커졌다. [초기값/실제영상/그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_wrist_motion_v1/README.md:1), [영상모음122개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v2.md:1)에기록했다. 이작은1축시험을전반연주·초기p/q복원완료로보지않고최종66권한/자유G/몸통목표/고정하체root/passivestrap을유지한다. [다음strap−2mm비교](/home/ajou/yigyu/3/stability_adapter_2/BODY9_STRAP_FINE_COMPARISON_PLAN.md:1)는미실행이다. Luna/독립검수도구한도로root자체검증과구분한다.


## 몸통9 PD×2·같은손목동작의strap−2mm — 한5초완료

LA1.1018469719600776→1.0998469719600776m만줄였고native t0/PD/1200target는exact같았다. 최대초기오차14.132608mm/2.894328°→14.010556mm/2.607665°,2~5초변화0.481766mm/.091929°→.363488mm/.070089°로줄었다. 실제손목좌표진폭.146929→.147836°,cablepeak24.129230→28.152161N과첫양의T step39→37을기록했다. Actual한1200step/두151frame스트랩영상·분석10검사완료. [초기값/영상/그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/README.md:1), [영상모음124개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v3.md:1)에남겼다. −2mm는유망한동작비교기준이며별도무동작정지는미측정이다. [다음total−4mm계획](/home/ajou/yigyu/3/stability_adapter_2/BODY9_STRAP_MINUS4MM_PLAN.md:1)은미실행이다. 전체66권한/몸통목표/고정root하체/자유G/passivestrap과초기p/q복원·유지/연주목표+안정화보정목적은유지한다. Luna/독립검수도구한도는root자체검증과구분한다.


## 자유 기타에서 fret·strike 체크포인트 전이 설계

사용자 추가 목표에 따라 기존 연주 prior를 유지하고 자유 기타의 연주 오차/초기p·q 이탈을 함께 보정하는 설계를 기록했다. [메인 설계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_ADAPTATION_PLAN.md:1), [계약 조사·기존 이미지/영상 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_prior_adaptation_v1/README.md:1)을 따른다. 대표 checkpoint CPU 조사4검사 통과: fret420/30·goal_pair, strike303/30·S3_SONG_INTEGRATION. 두 source60관절+Thorax6으로 현재66권한을 유지하며 하나의 최종PD목표를 제출하는 공동residual을 권장한다. 예시는 최종선정/성능인증이 아니다. 신규물리/학습/actor추론0, 기존LA total−4mm는 미실행으로 보존한다. 다음은 평가기반 source선별과 관측/action/history 매핑의 작은 계약 검사다. Luna/독립검수는 thread도구한도로 미완료이며 root 자체검토와 구분한다.


## Strap total−4mm — actual 한5초와3조건 비교

원본LA1.1018469719600776m대비−4mm만변경했고같은native runner·초기81/PD/1200손목목표를유지했다. original/−2/−4의max초기이동14.132608/14.010556/14.023529mm,회전2.894328/2.607665/2.335921°다. −4는−2보다회전개선/후기변화소폭증가의tradeoff라회전후보로보존하고−2를후기유지비교기준으로둔다. 실제한1200step·두151frame스트랩영상,3조건13분석검사와독립검수Critical/Warning0. [결과/영상/그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/README.md:1), [결정/다음지지형상검증](/home/ajou/yigyu/3/stability_adapter_2/STRAP_MINUS4MM_DECISION.md:1), [영상126개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v4.md:1). 앞선checkpoint조사의Strike schema null은원본보존후audit_v2/새출력5checks로보완했다. 목표초기p/q복원·완전palm그립·실제fret/strike연주·학습은미완료다. 다음은추가단축대신−2actual저장상태의팔12+hinge6source합성검증이다.


## 팔·손가락 source 검증과 연주 보정 학습 평가 순서

LA−2mm의 저장 상태에서 팔12+hinge6 조건부 모델5검사와 v3 형상 검색7검사를 완료했다. 같은 왼손의 비인접 source110쌍도 검사한다.4개 baseline+12개 제안 중 통과는0.5초의1/4보정 한 행이며, 손바닥 patch 간격 감소는 약21.243µm에 그친다. t0와5초 통과 방향이 없어 실제 PD 시험으로 채택하지 않는다. v1 목표 기준 오류와 v2 same-left 누락은 원본 보존 후 새 버전에서 보완했다. [결과·그림 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/README.md:1), [후속 결정](/home/ajou/yigyu/3/stability_adapter_2/COUPLED_SUPPORT_SOURCE_DECISION.md:1)을 따른다.

사용자 방향에 맞춰 현재 G 기준 연주 정확도와 초기 world p/q 유지 성능을 분리해 평가한다. 동결 fret/strike 목표60개+Thorax6에 하나의 공동 residual을 합성하고, 무학습 연결→단일 이벤트→전환→짧은 phrase 순서로 비교한다. [추가 학습 평가 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:1)에 기록했다. 기존 학습 계획/체크포인트는 보존한다. 이번 단위 신규 native/physics/actor 추론/학습은0이며 기존 영상126개는 그대로다. source 형상 접근은 실제 접촉·지지력·연주 성능 인증이 아니다.


## 손바닥 witness 초기18각 — 실제5초 비교와 연주 보정 연결

초기 팔12+hinge6과 대응 PD목표만 최대0.002616494894rad 바꿨다. Source 거리 상한은0.421669522→실제 t0 source0.109523083mm로 줄었고, fresh native14검사/비인접 self1188쌍 source 교차0을 통과했다. Actual 한 초기화/1200step·두151frame 스트랩 영상을 완료했다. 기존 목표 offset/LA−2mm/몸통9PD×2/G초기p·q/root하체/손목파형은 유지하고, 비선택63각·1200목표를 exact 대조한16분석검사를 통과했다.

최대 초기 G오차14.010556mm/2.607665°→14.085148mm/2.616525°,2초 기준 후기변화0.363488mm/0.070089°→0.373544mm/0.072412°로 소폭 늘었고 palm 양의 raw lambda는 둘 다0이다. 새 초기각은 채택하지 않고 기존−2mm를 작은 손목 동작의 비교 기준으로 유지한다. [결정/다음 순서](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:1), [결과·초기값·실제영상·그림 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/README.md:1), [영상 모음128개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v5.md:1)에 남긴다.

완전 palm접촉을 연주 필수 선행 단계로 두지 않고, 동결 fret/strike의 현재 G기준 목표와 초기world G p/q유지를 공동 residual로 보정하는 [학습 평가 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:17)을 따른다. 다음 작은 단위는 실제 checkpoint 평가 기록 선별과 residual0 관측/action/history CPU계약이다. 이후 무학습 연주 baseline을 측정하며 이번 actor추론/학습update는0이다. 초기 p/q복원·전체그립·연주학습 완료는 아니다.


## 연주 source 후보/81D 목표 합성 CPU 계약

새 playing_target_bridge는후처리된 source30+30과Thorax6 residual을하나의81D target/history로합성한다. 원Base.apply_actions AST80step×17batch의residual0최대차2.384185791015625e−7rad,최종history복원차1.1920928955078125e−7rad이며bitwise동등으로표시하지않는다. 이름순서/66gradient/held15/포화/9거절경계를포함한10CPU검사를통과했다. source후처리·420/303전체관측·actor·물리연결미구현이다.

Strike10,000은원본checkpoint SHA와64episode single-pick F1=1.0/timingp95=5.628ms가연결되는후보다. 앞선10,708은중단저장본으로승계하지않는다. Fret47,000/47,500의전체곡F1=.100098/.073486·sustain1/35는낮고47,000도goal_pair/stalled이므로좁은진단후보일뿐이다. 네파일모두기존strictG0자격false이며자유기타연주선정완료로표시하지않는다.

현재−2mm 초기실제각과유지목표는같은LH6관절이Fret source범위밖이며,범위까지최소변경최대각은초기.661268771rad/유지.617647946rad다. CPUBRIDGE는이warmstart를거절하며history를몰래clip하지않는다. [결정/평가한계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_TARGET_BRIDGE_DECISION.md:1), [구현·검증계획](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_TARGET_BRIDGE_PLAN.md:1), [표·그림·이전실제배치설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/README.md:1)에기록한다.

다음은[손6 초기profile호환계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_PROFILE_INITIAL_POSE_PLAN.md:1)의새초기각/유지목표와freshnative직접형상gate를검수한뒤actual5초를비교한다. 이전18변수FK모델을finger1변경에유효하다고확대하지않는다. 현재body9PD/LA−2mm/G초기p·q/고정하체root/나머지75각·목표를유지하고최종66권한/현재G연주+초기worldG복원·유지목표를계속진행한다. 이번native/physics/actor추론/학습0,기존영상128개유지.


## 사용자 요청: 스트랩 길이 고정·관절만 조절 비교

[새 계획](/home/ajou/yigyu/3/stability_adapter_2/JOINT_ONLY_FIXED_STRAP_PLAN.md:1)에 따라 original LA1.1018469719600776m를 고정하고 initial팔12+hinge6/대응목표만 바꾼 한actual5초를 준비한다. 기존−2/−4 결과는 보존하고 sourceprofile6 초기 시험은 뒤로 보류한다. 기존 small_wrist_motion_v1를 같은LA 기준으로 비교한다.


## 스트랩 길이 고정·관절18만 변경 — actual5초 완료

LA1.1018469719600776m를기준/새후보에서고정하고초기팔12+hinge6/대응PD목표만최대.002616495rad변경했다. Actual한초기화/1200step·두151frame스트랩영상·freshnative14/분석17검사완료. 2초기준2~5초변화.481766500→.257785610mm/.091929111→.051002962°로각46.49/44.52%줄었다. 초기최대이동14.132608→14.084223mm지만회전2.894328→2.920042°로소폭증가했다.

[고정LA관절비교결정](/home/ajou/yigyu/3/stability_adapter_2/JOINT_ONLY_FIXED_STRAP_DECISION.md:1),[초기값·그림·실제영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/README.md:1),[영상130개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v6.md:1)에남긴다. 고정LA도passive장력은작용하며새후보peak24.626N이다. Palm양의rawλ0/selfcontact0이며초기worldG복원·전반연주·반복재현은미완료다. 기존결과보존·최종66권한/root하체fixed/body9목표유지. 새후보는fixedLA후기유지비교기준으로보존하고다음관절폐루프/연주연결검증에서도길이조절을탐색변수에서제외한다.


## 고정 LA에서현재어깨→기타signed응답준비

[새계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md:1)에따라직전관절18후보의초기값/고정LA/body9PD2/손목파형을유지하고L_Shoulder_y목표만±.008rad로두actual5초를준비한다. 이전seed2의j는초기33각/bodygain/손목조건차이로승계하지않는다. 초기p/q복원과최종66공동제어를위한현조건응답진단이며sourceprofile6/actor/학습은보류한다.


## 고정 LA·어깨 목표 ±0.008rad — 두 actual5초 완료

동일 초기81/G p·q와 LA1.1018469719600776m를 유지하고 L_Shoulder_y 유지 목표만 바꿨다. 각1초기화/1200step·두151frame 영상·fresh14/1188 source self gate를 통과했고 저장29검사를 완료했다. 기준/−/+ 최대 초기 위치 이탈은14.084223/15.989064/11.926351mm, 회전은2.920042/2.862553/3.169993°다. +방향의 위치 개선에 회전 악화가 동반돼 공동 개선으로 채택하지 않는다. 고정LA 관절18 기준을 유지하고 다음은 다른 손목 축의 응답 비교다. 4~5초 단일 열의 양방향 불일치50.75%와 범위 밖 LS+.02768rad 때문에 즉시 폐루프에 적용하지 않는다. [결정/후속 단계](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md:1), [영상134개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v7.md:1). 기타 자유 물리·최종66권한/root하체fixed/몸통목표·passive strap 유지, actor/학습0이며 초기p/q복원과 연주 안정화 전체 목표는 계속 진행한다.


## 중지 굽힘과 접촉 영역 — 저장 자료 조사

[새 조사/표시 계획](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_REGION_PLAN.md:1)에 따라 최근 고정LA·어깨+0.008rad의 실제 저장 관절/접촉을 읽어 중지 초기각·고정 PD목표의 영향을 확인한다. 새 native/제어 변경은 없으며 길이의 필수성·자연스러움은 단정하지 않는다. 기타 local 허용영역·손끝 후보패치·실제접촉을 구별하는 다음 표시/평가 방향을 정리한다.


## 중지 굽힘 원인 조사 — 기존 목표와 접촉을 구분

최근 고정LA+어깨 목표 조건의 저장5초를 분석했다. 중지2 목표64.343°/중지3 목표60.684°가 전체1200step 고정이고 중지3은 시작부터60.146°,5초에도60.684°다. 검지/약지/소지3 목표는7.991/2.954/33.027°다. 현재 제어가 손가락 길이나 접촉 거리를 보고 중지만 자동으로 더 굽히는 구조는 아니다. 중지3 양의rawλ는초기18step(.108~.183초)뿐이며2초이후0,검지3은1145step이다. 굽힘을 곧 지속지지로 해석하지 않는다. 길이 때문에 필수인 각도/자연성은 미검증이다. [조사와표시계획](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_REGION_PLAN.md:1)에따라G-local 허용면·손끝후보패치·실제접촉점을구분하는표시와soft자세평가를후속으로둔다. 표시만으로제어가바뀌지않으며모든손가락동시접촉을강제하지않는다. 신규native/actor/학습0,LA고정·최종66권한을유지한다.


## 손가락 접촉 지도 준비

[저장 접촉 지도 계획](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_PLAN.md:1)에 따라 현재 고정LA 실행의 실제 body 원점/SDK feature와 기타 local 참조면을 대조한다. 기존 native PNG와 별도 좌표 그림을 구별하며 물리/목표 변경·새native는0이다. 직전 중지 목표/접촉 조사 결과를 다음 자세 변경의 근거로 발전시킨다.


## 손가락 접촉 지도 — 저장 좌표 검증 완료

1198개 양의 왼손 SDK feature와 실제 body 원점을 기타 local로 변환했다. Post-step 양쪽 feature 최대 잔차0.000082033mm이며 선택0/.133/.233/5초의 현재 feature 수는0/2/0/1이다. 중지 원점 경로는약99.64mm로 검지88.47mm보다길지만 약61° 굽힘이 필수라는 증거는아니다. 5초 검지 top 원점과실제 feature는약5.80mm 떨어져있어 원점을패드로취급하지않는다. [그림·원본 Gym 프레임 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/README.md:1)에정리했다.

[후속 결정](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_DECISION.md:1)은고정LA 관절18 baseline에서 middle3 유지목표만−.05rad 줄이는한actual5초 후보이며 아직미실행이다. 접촉영역 표시를soft 자세선호·분포·실제접촉평가에연결하되 모든손가락동시접촉은요구하지않는다. 최초substep기본값판정은별도설정검사로보완했고native readback과구분한다. 이번새native/physics/actor/학습0,기존영상134개유지.


## 사용자 변경: 자연스러운 연주 허용 범위와 스트랩 고정

[새 평가 설계](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_PLAYING_ENVELOPE.md:1)에 따라 초기p/q의정확한복원보다자연스러운연주자세·기능·유지를우선한다. 첫작업범위는초기대비30mm/5°,후기연속1초변화5mm/1°이며영상으로조정할임시값이다. 구역안에서는초기점복원비용을없애되연주오차·drift·자세선호는유지하는설계를둔다. 새controller/reward는미구현이다. 스트랩은현재비교기준1.1018469719600776m고정이며다른환경출처를확인중이다. 원본환경의route기반단축방식과단일절대길이를혼동하지않으며route자동rebase/길이탐색은하지않는다. 최종66권한·몸통목표·고정root하체·자유G/접촉제약을유지한다. 과거판정은보존하고미실행엄격복원계획보다새사용자방향을우선한다. 이번새물리/학습0.


## 자연스러운 허용 구역 — 기존 고정LA4기록 재평가

[저장분석계획](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_ENVELOPE_ASSESSMENT_PLAN.md:1)의계산을완료했다. 네기록0~5초각1201표본모두임시30mm/5°안이며후기121개완전1초창도각5mm/1°안이다. Rawpose/trace·독립SO(3)·입력전후SHA26검사통과. 관절18후기의1초창최대는.455912mm/.084049°,어깨+는.292116mm/.052998°다. 이전2초기준변화와서로다른지표라순위차이를구분한다. [후속결정](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_ENVELOPE_ASSESSMENT_DECISION.md:1)에따라미세한초기오차축소보다손가락자세/연주접근성개선을우선한다. 관절18기준중지3−.05rad시험은다음단위미실행이며어깨와동시변경하지않는다. 이번분석새native/actor/학습0,길이고정/다른환경출처pending·최종66권한유지. 임시구역통과를자연성/연주성공으로표시하지않는다.


## 고정 스트랩·중지3 목표 완화 실제 비교 준비

[한후보계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_PLAN.md:1)에따라관절18baseline의초기81각/G p·q/LA1.1018469719600776m/몸통PD·고정root하체·손목파형을유지하고LH:middle3 유지목표만−.05rad줄인다. Fresh초기형상gate뒤실제5초/두스트랩영상을기록하고다른80목표·시계를exact대조한다. 초기오차미세축소보다손자세/접근성을평가하며임시30mm/5°·후기1초5mm/1°기준과기능미검증을구분한다. 다른환경길이출처pending이며길이조절은하지않는다.


## 중지3 유지목표만 완화 — 실제5초 완료

초기81/G p·q/LA1.1018469719600776m/PD·손목파형을유지하고중지3목표만60.684346→57.819559°로바꿨다. 준비7/fresh14·1188source/actual1초기화1200step/두151frame스트랩영상/분석19검사완료. 다른80개의1200목표·시계exact,5초중지3실제57.820850°다. 후기1초창최대위치.455912→.437298mm/회전.084049→.081147°이며두조건모두임시범위안이다. 이전2초단일기준변화는늘어모든지표개선이라고하지않는다. [결정](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_DECISION.md:1)에따라완화조건을후속손자세후보로보존한다. 다음total−.15rad는미실행이며중지2/어깨는유지한다. 손6sourceprofile/실제연주/학습미완료,초기배치변경과유지목표변경을구분한다. 최종66권한·몸통목표·고정root하체·자유G/고정길이유지.


## 中지3 총−0.15rad 다음 한후보 준비

[새 계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md:1)에따라초기81/G p·q/LA/다른80목표·PD·손목파형을유지하고관절18기준중지3유지목표만총−.15rad로줄인다. 직전−.05조건과기준을저장자료로함께비교한다. 준비검산·fresh gate·실제5초/두스트랩영상·접촉/임시허용구역을단계검증하며아직실행전이다. 자연성/연주성공으로확대하지않고다른환경출처pending·고정길이를유지한다.


## 중지3 총−0.15rad — 세조건 실제 비교 완료

[새결정](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_V2_DECISION.md:1)에따라초기81/G p·q/LA/PD·다른80목표를유지한actual5초를완료했다. 중지3은5초52.090865°로펴졌고후기1초.437387mm/.080289°로직전−.05와비슷한유지를보였다. 준비7/fresh14·1188source/후처리31검사통과,각121개임시1초창통과다. 중지3양의λ50step은초기.125~.333초뿐으로후기지지개선이아니다. 다음은초기중지3각을현재52.089980°목표에정렬하고동일최종절대목표를유지하는한후보이며아직미실행이다. 중지2는관측분포안이므로크기만으로펴지않는다. 자연성/연주기능/학습미완료·고정길이·최종66권한유지. 영상모음은138개다.


## 중지3 세조건 비교 산출물

[결과·실제5초영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/README.md:1),[새파일절대경로·줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/CHANGED_FILES.md:1),[누적이미지설명§108](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1971)을추가했다. 저장자료그림55입력/55사본전후SHA와실제그림을검수했고추가물리/actor/학습은0이다. Phase최종감사는별도JSON에기록하며새초기각정렬시험과실제연주기능검증은남아있다.


## 중지3 초기52.09° 배치와동일최종목표 비교 준비

[새한후보계획](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_MIDDLE3_ALIGNMENT_PLAN.md:1)에따라중지3초기각만직전52.089980°유지목표에맞추고offset0으로동일81최종목표를제출한다. 다른80초기각/기타p·q/LA/PD/손목파형은유지한다. Source교차·예측FK와nativefresh를먼저검사하고탈락이면물리실행없이상세를보존한다. 이번은초기자세변경이며연주기능/학습완료가아니다. 이전입력closure는보존하고과거snapshot의재귀중복복사만줄인다.


## 초기middle3 정렬 — 동일81명령 실제5초 비교

[판단](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_MIDDLE3_ALIGNMENT_DECISION.md:1):초기middle3를60.145874→52.089980°로맞추고offset0으로같은최종81×1200명령을제출했다. 준비14/source1188·fresh14/1188·actual1초기화1200step/두151frame영상·분석23검사완료. 초기목표오차8.055894→0°지만G최대이동14.077232→14.608483mm/후기1초.437387→.648625mm,.080289→.115306°로늘어G안정성개선이라고하지않는다. 두조건임시구역통과라quiet비교기준과새초기자세후보를함께보존한다. 다음은현재고정LA/초기후보들의fret·strike source범위호환재조사이며아직미실행이다. 최종66권한/몸통목표/root하체고정/자유G·LA고정유지,실제연주/학습미완료.


## 初期middle3 정렬 비교 산출물

[결과·실제두영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/README.md:1), [변경파일·실제줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/CHANGED_FILES.md:1), [이미지설명§109](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1988)을추가했다. 저장자료그림46입력/46사본전후SHA와실제4패널그림·native시작/종료프레임을확인했다. 그림단계추가물리/actor/학습0이며영상모음은140개다. 최종독립검수와보존감사는별도기록으로봉인한다. 다음현재두후보의연주source범위CPU재조사는미실행이며초기목표오차0을기타안정성/자연성/연주완료로확대하지않는다.


## 고정LA 두초기자세의 source 범위 CPU 재조사 준비

[새 계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_COMPATIBILITY_PLAN.md:1)에따라현재두자세의실제초기81/PD초기81/유지81목표·1200명령을fret47,000/strike10,000 계약의native/source/normalized 교집합과대조한다. 이전LA−2mm의손6숫자를승계하지않는다. 위반관절과signed최소변경을계산하고실제warm-start거절을확인하며물리각이나history를clip하지않는다. 이번은CPU필요조건조사이고task후처리/전체관측/actor·자유G연주검증은남긴다. LA고정/최종66권한/몸통목표/root하체고정/자유G를유지한다.


## 고정LA 현재두자세의 연주범위 CPU 재조사 완료

[판단과다음초기배치](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_COMPATIBILITY_DECISION.md:1):34CPU검사/48입력·48사본전후SHA를확인했다. 기존초기6개/현재52.09°초기5개,두조건유지·명령범위각5개가source교집합밖이다. 남은LH thumb1_x/y,thumb3,index1_x,ring1_x의최소변경최대는초기.661269rad/유지.617648rad이며양쪽warmstart는거절했다. Scalar범위차이를해부학적잘못/안정한보정량으로해석하지않는다. 두source strictG0자격false를보존했고actor/physics/학습0이다. [다음한후보계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md:1)의5관절초기/유지각변경과freshnative직접gate/5초는미실행이다. LA고정·최종66권한/몸통목표/root하체고정/자유G를유지한다.


## 고정LA 연주범위 재조사 산출물

[결과·그래프·이전Gym초기장면설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/README.md:1), [변경파일절대경로·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/CHANGED_FILES.md:1), [누적이미지설명§110](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2007)에정리했다. 실제PNG/14직접입력·14사본전후SHA를확인했다. 원자료CPU48입력의전후보존은원CPU기록으로검증하고그림입력으로과거closure를재귀복사하지않았다. 추가native/physics/actor/학습0·기존영상140개유지다. 후속손5관절초기배치/freshnativegate/5초는아직미실행이며최종문서독립검수와보존감사는phase별기록에봉인한다.


## 사용자요청: 스트랩없는 현재자세 영상 준비

[별도비교계획](/home/ajou/yigyu/3/stability_adapter_2/NO_STRAP_VIDEO_PLAN.md:1)에따라최근초기52.09°조건의초기각/PD/G p·q/1200손목명령은유지하고strap force와주황표시만제거한실제5초를기록한다. 현재기준/손5관절후속계획은보존한다. 기타중력·접촉·관절PD는그대로이며자세붕괴도숨기지않는다.


## 스트랩 없는 현재 자세 actual5초 비교 완료

사용자 요청에 따라 현재 initial_middle3_alignment_v1 초기 자세의 strap force와 orange overlay를 모두 OFF한 실제 Isaac Gym 실행1회를 완료했다. 중력·native contact·PD는 유지했다. 전체 초기 state를 포함한20공통필드와81×1200 최종목표/명령clock이 strap-on 기준과exact이며 기타고정/손부착/시작후pose덮어쓰기는없다. 분석의legacy check명 all21_initial_fields_exact는20필드검사의잘못된개수label로보존한다.

- [x] 새no-force adapter와raw native recorder 사전검수
- [x] 실제1200step/5.000초·151frame30fps두영상·초기값저장
- [x] explicit force API0·1201applied tension0·root/하체fixed·fresh14/source1188 검사
- [x] 저장자료분석20checks 및 영상모음142개(기존140exact) 갱신

No-strap 최대초기변위20.584004mm/회전12.152977°,종료20.525764mm/12.145216°이다. 후기2~5초 완전1초window최대변화0.335897mm/0.064720°로작아졌지만초기회전이큰다른자세에머문결과다. Strap-on은14.608483mm/2.918412°였다. 이번조건에서는strap이초기회전억제에도움이됐다. 본선고정LA기준은유지하며이번user요청은별도조건이다. 자연스러움/연주성공/물리접촉인증이나학습성공으로승격하지않는다. 기존후속손5관절source호환초기자세계획은별도로보존한다.

[결과·초기/종료이미지·두영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/README.md:1) · [영상모음v11](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v11.md:1). Leaf계획과실행소스는소비후보존하며최종검수·감사는결과폴더에기록한다.


## 고정LA 손5관절 초기 후보 직접검증 준비

[실행계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_INITIAL_EXECUTION.md:1)에따라 기존초기52.09° 자세의다섯손관절만source/native범위가까운경계안쪽으로바꾼한후보를준비한다. Fresh native직접형상gate에서0step거절또는같은초기화5초두스트랩영상으로기타변화를비교한다. LA/다른76각·목표/G초기p·q/PD/root하체고정/몸통9목표/최종66권한을유지한다. 단순범위호환을초기안정화·자연성·연주성공으로대체하지않는다.


## 고정LA 손5관절 초기 후보: 실제0step 형상거절

숫자준비9검사를통과했고LH thumb1_x/y,thumb3,index1_x,ring1_x 초기/유지각이모두source/native/normalized교집합안으로들어왔다. 다른76초기각/목표와G초기fullstate·LA/PD/몸통목표/root하체조건은유지했다. 실제한초기화의fresh native15검사중human–G source형상검사만실패했다. LH:thumb2–guitar의LP공통내접반경은4.288364821mm이며PhysX cooked관통깊이로해석하지않는다. Cross-hands/self1188와palm상향proxy0.956547은통과했다.

- [x] 5관절numeric후보·1ULP/다른76보존/목표무clipping검산
- [x] 새fresh native직접gate·사전독립검수(Finger1 FK미사용)
- [x] 실제1초기화·0step거절·t0이미지/두1frame partial영상보존
- [x] 저장분석15검사·영상모음144개(기존142exact+partial2) 갱신

후보는채택하지않으며5초기타안정성은측정하지않았다. Native exit1/미완료report를보존하고예상된초기geometry거절terminal로구분했다. 숫자범위안의각도만으로겹침없는지지가보장되지않는다는근거다. [결과·실제초기이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/README.md:1), [명시적0step영상모음v12](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v12.md:1)에기록한다.

[다음엄지2계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md:1)은현재native실제finger1변환을기준으로scalarthumb2의0/±.05/±.1/±.2rad 7source조건부터검사한다. 최소변경clear한후보만freshnative직접gate/통과시같은초기화5초로검증할예정이며아직미실행이다. LA고정·자유기타·최종66권한·몸통9목표/root하체고정과원자료보존을유지한다. Source숫자조건을최종연주성공으로승격하지않는다.


## 엄지2 단일 관절의 7조건 형상 여유 비교 준비

[계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md:1)에따라직전실제거절초기state를기준으로엄지2만0/±.05/±.1/±.2rad에서비교한다. 실제finger1다축변환은고정하고검증된scalar힌지만변경하며zeroidentity와전체source HG/cross/self1188을확인한다. Clear조건이있으면최소변경한후보의freshnative직접gate와통과시같은초기화5초를진행한다. Source범위호환이아닌겹침없는지지회복과기타초기오차개선을위한단계다. LA/기타p·q/root하체/몸통9목표/최종66권한을유지한다.


## 엄지2 source identity 검사 v2 정정

v1은충돌에서제외되는LH:thumb_pad body까지고정대상으로검사한구현오류로중단됐고7조건을완료하지못했다. 원본입력/소스/로그/exit를보존한다. [정정실행](/home/ajou/yigyu/3/stability_adapter_2/THUMB2_CLEARANCE_V2_EXECUTION.md:1)은thumb2전체자식body를XML에서유도해같은7조건을새v2경로에서계산한다. 실제collisiongeom은thumb2/3둘이며top/pad는따라가는pose만있다. 이것은후보각도/제약/물리목표변경이아니다.


## 엄지2 7조건 source 비교 완료: 초기 형상 겹침 유지

정정v2 source실행은8검사/7조건을완료했다. Thumb2를0/±.05/±.1/±.2rad float32로바꾼모든조건에서thumb2–guitar source겹침이남았다. 기준LP공통내접반경4.288364821mm에서−.2rad의3.054823670mm까지감소했지만clear후보는없었다. Cross/self1188은모두clear,palm상향·나머지bodypose는보존됐다. 새native/physics/actor/학습은0이고5초안정성은미측정이다. 이결과는시험한±.2범위이며thumb2전체가동범위의불가능성으로확대하지않는다.

- [x] v1오류기록보존·XMLthumb2자식전체로identity정정
- [x] v2 source8검사/68입력·68사본/7조건·zeroidentity·범위/다른pose 검사
- [x] Clear후보없음에따라native미실행·LP반경과후면patch거리저장

[결과·그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/README.md:1)에정리한다. [다음기저부native계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md:1)은thumb1_x−.05/−.1 또는thumb1_y+.05/+.1rad의한축4초기각을범위안에서순서별freshnative직접gate로검사하고첫통과조건만같은초기화5초로기록한다. Finger1다축FK로초기형상통과를예측하지않으며아직미실행이다. LA/G초기p·q/root하체/몸통9목표/최종66권한을유지한다.


## 엄지 기저부 실제 native 4초기각 검증 준비

[기저부 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md:1)에 따라 손5관절 범위호환 후보에서thumb1_x−.05,thumb1_y+.05,thumb1_x−.10,thumb1_y+.10rad를순서별실제native로검사한다. [새 phase runner](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_native_phase.py:1)와 [직접 gate entry](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_candidate.py:1)는기존소비코드를수정하지않고새trial/결과경로를쓴다. 각후보의다른80초기각·목표/LA/기타p·q/PD/root하체/몸통9를보존하고첫gate통과만같은초기화1200step5초를기록한다. 최대4초기화/1개완료5초의소단계이며전체안정화·연주성공선언이아니다. 아직실행전이다. 직전스트랩OFF영상요청은기존실제영상151frame/5초·forceAPI0을확인해사용자에게전달했다. 본선LA고정조건을계속한다.


## 엄지 기저부4조건 실제 초기검사 완료 — 모두겹침유지

숫자준비23검사/실제4초기화/각15fresh검사와source self1188를완료했다. 네조건모두thumb2–guitar source교차만남아0step으로거절됐다. 기준4.288365mm보다공통내접반경이5.015440~6.079509mm로커졌고후보는채택하지않는다. 다른80초기각·목표/기타fullstate·PD·LA/root하체/몸통조건을보존했고저장분석35검사를통과했다. 실제5초안정성은미측정이며8개의1frame partial영상을명시적으로분류해영상모음152개에추가했다. [다음손목계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_WRIST_CLEARANCE_PLAN.md:1)은실패한엄지변화를승계하지않고기준손전체를작게움직이는13source조건후한freshnative/통과시동일초기화5초단계이며아직미실행이다. 길이고정/최종66권한·자유기타조건을유지한다.


## 엄지 기저부4조건 산출물

[실제초기이미지·수치·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/README.md:1), [변경파일·실제줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/CHANGED_FILES.md:1), [누적그림설명§114](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2069)을추가했다. 저장자료도표11직접입력/13사본·전후SHA/실제PNG와이번native초기프레임을확인했다. 후처리새물리/actor/학습0이며5초안정성미측정·partial8분류를유지한다. 최종독립검수와이전원본보존감사는별도phase기록으로봉인한다. 다음손목13source/한freshnative계획은미실행이다.


## 손목13조건 source 비교와한actual 검증 준비

[손목계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_WRIST_CLEARANCE_PLAN.md:1)에따라손5관절baseline의실제손계층을고정하고wristx/y/z한축0·±.05·±.1rad 총13source조건을새경로에서비교한다. 이전기저부4actual0step거절은다음방향을정하는실측진전이며실패변화를승계하지않는다. [sourceproducer](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:1)·[phasewrapper](/home/ajou/yigyu/3/stability_adapter_2/run_wrist_clearance_phase.py:1)·[freshnative entry](/home/ajou/yigyu/3/stability_adapter_2/run_wrist_clearance_candidate.py:1)를추가했다. 모든기존offset과다른80초기/held/기타p·q/LA/PD/몸통9/root하체/최종66권한을보존하며conditional source후보를actualgate와구분한다. 첫selected한후보만같은초기화5초로기록하고sourceclear없으면native0회다. 아직실행전이다.


## 손목13source조건 완료 — 엄지겹침감소와다른손부위겹침의교환

source8검사/69입력·69사본전후SHA/13조건을완료했다. Clear후보없음으로proposal/native를만들지않았다. 모든thumb2–G교차가남고Wrist_y−.1rad의thumb2 LP반경은.815476mm로줄었지만palm–G2.076522mm를포함한HG교차총6쌍이남는다. Sourcecross/self1188은모두clear,palmup및기존offset/다른80初期·held/손상대계층을보존했다. 새actual/physics/actor/학습0·5초안정성미측정·기존영상152개유지다. 반경은PhysX침투깊이가아니고13표본을전체손목범위불가능성으로확대하지않는다. [다음팔위치계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md:1)은원baseline과Wrist_y−.1가설의두seed에서Thorax/Shoulder/Elbow9축작은변화를총74source조건으로비교한뒤한후보만freshactual/통과시동일초기화5초로검증한다. 아직미실행이며길이고정·몸통9목표/root하체/자유기타/최종66권한을유지한다.


## 손목13source 비교 산출물

[13조건표·그림·이전Gym장면설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/README.md:1), [변경파일절대경로·실제줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/CHANGED_FILES.md:1), [누적그림설명§115](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2080)을추가했다. 산출물6직접입력/8사본·전후SHA/실제13조건2seriesPNG를확인했다. 다른HGpair없음의none표시는거리0이아니고LP임계값초과보고pair없음을뜻한다. 새native/physics0·기존영상152개유지이며최종독립검수/보존감사를별도phase기록으로봉인한다. 다음74source팔위치조정과한actual검증은아직미실행이다.


## 팔 초기각74제안·68형상조건 비교 준비

[팔위치계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md:1)과 [실행범위](/home/ajou/yigyu/3/stability_adapter_2/ARM_POSITION_EXECUTION.md:1)에따라두seed의74numeric제안을검사한다. Thorax모델한계를넘는6제안은raw초기/held목표와위반bound를남겨geometry전에제외하고나머지68조건을source검사할예정이다. Clipping/범위완화는없다. 새source/phase/native entry는AST검사를통과했으며upstreampose검사는실제변경XMLsubtree밖을검사한다. 첫clear최소변경후보만freshactualgate·통과시같은초기화5초두영상을기록한다. Originaloffset/기타fullstate/고정LA/PD/root하체/몸통9/최종66권한을유지한다. 이전goalturn은source13조건의진전이며직전영상요청확인은물리탐색진전은아니다. 다음안전행동으로이번74제안을실행한다.

- [x] 새구현과범위제외기록·AST검사
- [ ] 독립사전검수·74숫자/68source검사
- [ ] Clear후보actualgate/동일초기화5초또는clear없음원인·후속계획


## 팔74제안 source 완료 — 조합 탐색이 필요함

- [x] AST/독립숫자검산·74제안 중6범위제외/68source평가
- [x] Source9검사/72입력·72사본 및 저장분석11검사
- [x] Clear0에 따라proposal/native/physics0·기존영상152개 유지

68조건 모두HG교차가남았다. 원seed의Thorax_y+.025rad는최대HG LP반경2.212092533mm이고,Wrist_y−.1seed+Thorax_z+.025rad는1.231575777mm/palm1.079515513mm·HG5쌍이다. 全68cross/self1188clear,palm상향최소.925554473·offset/다른각/상대계층을보존했다. 10조건에서thumb2보고pair가없어도다른HG교차가남아통과후보가아니다. LP반경은cooked침투깊이·접촉거리로해석하지않는다. 새5초안정성은미측정이다.

[다음bounded연속팔계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:1)은두seed·arm12조합각최대±.15rad/총800source평가·한freshactual/통과시동일초기화5초다. 아직미실행이며실패하면같은source세분화를무한히늘리지않고actualquiet기준의물리제어·연주목표전환설계로돌아간다. Initialsource호환만으로본목표를대체하지않는다. 이번산출물/최종독립검수/보존감사는별도phase에기록한다.


## 팔74제안 source 산출물 정리

[9panel그림·두seed결과설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/README.md:1), [변경파일절대경로·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/CHANGED_FILES.md:1), [누적그림설명§116](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2090)을추가했다. 산출물82입력/82사본·전후SHA·실제PNG가독성을확인했고source68값은66비baseline점+2baseline점선으로표현했다. 6범위제외는NaN공백이며공유축formatter로†tick이안보이는표시한계와정확한제외위치를문서에명시했다. Self1188검사와별도양손검사count를구분한다. 새native/physics0·기존152영상유지이며최종독립검수/원본보존감사를phase별기록으로봉인한다. 연속arm12조정계획은아직미실행이다.


## 연속 왼팔12관절 두 시작점의 실행 준비

[연속팔계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:1)과 [목적함수실행leaf](/home/ajou/yigyu/3/stability_adapter_2/ARM_CONTINUOUS_EXECUTION.md:1)에따라새source/phase/native entry를구현하고AST검사를통과했다. Originalbaseline과직전row47seed에서boundedPowell각400호출이하,총800평가다. Float32초기/held/sin양끝에맞게허용입력구간을계산하며clipping없다. HG LP반경항·palm/thumbpatch upper거리항·자세변화·평면선호를명시했고매평가JSONLflush/원입력보존/Fullclear후한actual직접gate·동일init5초조건을유지한다. 별도독립검수뒤실행한다. 이전goalturn은74제안68source평가·원본보존감사21checks의진전이며새범위탐색은아직미실행이다.

- [x] 실행leaf·새3entry·AST검사·기존소스보존
- [ ] 독립검수·두seed최대800source호출
- [ ] 한actualgate/통과시5초또는clear없음에따른quiet기준복귀설계


## 연속팔800평가 완료 — 실제quiet 제어권진단으로복귀

두seed각400회·총800source평가가exit0/163.823445736초로끝났고source10검사를통과했다. 두Powell은최대평가수로종료됐으며수렴성공이아니다. 全800HG잔존/clear0/새proposal/native/physics0이다. 최대HG반경최소는row798 .783417117mm이고palm .427649599/thumb2 .688060578/middle3 .783417117mm가남는다. 범위/other69/손상대계층/upstream·비변경mesh/palmup검사는통과했다. HG가모두남아cross/self1188후속screen은미평가(null)이며전체800clear로오해하지않는다.

최초저장분석은행33충돌목적값의1ULP수준차이(1.490116119e−8)가부적절한절대1e−8허용치를넘어중단됐다. 소비v1분석소스·사본/manifest·invocation/실패기록을보존하고 [분석v2정정](/home/ajou/yigyu/3/stability_adapter_2/ARM_CONTINUOUS_ANALYSIS_V2.md:1)에서float64규모허용치로독립재계산11검사를통과했다. Exact입력/범위/HG임계값은완화하지않고source/native재실행0이다.

[실제quiet검지지지제어권계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md:1)은원quiet초기/LA/PD와기존wrist명령을유지하고native접촉이있던LH:index3의±.005radPD목표보정두5초를검증할예정이다. Source통계범위호환을모든초기PD진단의필수조건으로강제하지않으며native한계·초기전체source/self·palm방향·금지조건은유지한다. 정책qualification우회/actor추론/학습은없다. 아직미실행이다. 같은source탐색을더늘리지않고본래기타p/q보정권한의실제물리응답을측정한다.

- [x] 두seed최대800source·원입력/제약보존·clear없음기록
- [x] 최초분석오차보존·저장분석v2독립검산11checks
- [ ] 그림/문서·독립검수·원본보존감사
- [ ] 다음quiet 실제관절제어권진단


## 연속팔800평가 산출물과 다음 실제제어 진단

[두seed 진행그림·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/README.md:1), [변경파일절대경로·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/CHANGED_FILES.md:1), [누적그림설명§117](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2098)을추가했다. 산출물179입력/179사본·전후SHA와실제PNG의두panel/전체800값/축/가독성을확인했다. 최대HG반경의누적최솟값과가중목적함수최솟값을구분한다. 全800HG잔존으로양손간형상검사와self1188쌍후속검사는미측정이며새native/physics0·기존영상152개유지다. 독립최종검수와원본보존감사는이번phase에별도봉인한다.

다음 [quiet 검지목표 제어권계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md:1)은기존안정기록초기81각/PD/LA/손목명령을보존하고LH:index3에±.005rad의두실제5초응답을측정한다. 계획은아직미실행이다. 초기source통계호환을본래기타위치·회전유지/보정목표의대체성공으로취급하지않는다.


## Quiet 실제 검지 목표 응답 준비

[실행leaf](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_SUPPORT_EXECUTION.md:1), [새 물리runner](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support.py:19), [입력봉인·단일조건 실행](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_phase.py:23)을추가했다. 기존quiet trial을그대로읽고index3목표만2~2.5초에±.005rad로ramp한다. 원1200×81저장명령대조에서other80 exact·2초까지전체목표exact·native목표한계를확인했고AST를통과했다. 기존14,015경로ancestry를새proposal에누적하지않고실제runtime입력/소스/자산을봉인한다. 원quiet기록과이전800phase는보존한다. 독립검수후plus/minus를각한번만fresh native gate·같은init5초로진행한다. 아직물리미실행이며새feedbackgain/actor/training은없다.


## Quiet 음수조건 native 오류와 별도 재시도

Plus는1200step/151frame/5초를완료했고앞2초trace가원quiet와exact였다. 원minus는native SIGSEGV(exit−11)로step152/.6333333333초에서종료됐으며Pythonreport/완료영상은없다. 저장state/trace/task/contact와152개공통명령prefix는baseline과exact·index보정0이고초기15gate/103입력사본·전후SHA도통과했다. 원minus파일SHA를새crash기록에보존하고완성19frame(t0...6초)으로부분영상두개를저장했다. 제어반응실패나완료5초로해석하지않는다.

[재시도leaf](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_NATIVE_RETRY_V2.md:1)에따라물리/초기/목표/그래픽설정과원runner를바꾸지않고새native/minus_retry_v2경로에서ONE추가초기화를계획했다. 기존최대2초기화조건을이새leaf에서총3시도/완료5초최대2로명시변경했다. 소비된원wrapper/소스·실패원자료는보존하고새wrapper사전검수뒤실행한다. 다시native오류면이번leaf의재시도는끝내고원인을진단한다.


## Quiet 검지 실제 응답 완료와 손목 측정 계획

[결과·실제 5초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/README.md:1), [변경 파일의 절대 경로·실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/CHANGED_FILES.md:1), [누적 그림 설명 §118](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2106)을 추가했다. Plus와 별도 minus 재시도는 각각 1200 step/5초/151 frame으로 완료했다. 첫 minus native SIGSEGV는 원인 미확정이며 152 observed step·19 frame partial·86개 원출력을 보존했다. 총 3초기화, 완료 2400 step과 실패 관측 152 step을 구분한다.

47개 저장 분석 검사를 통과했다. 기준/plus/minus의 종료 초기 위치오차는 13.819696/13.750278/13.887982 mm, 회전오차는 2.918277/2.921428/2.916812°다. 작은 검지 보정은 위치와 회전을 동시에 줄이지 않았으며 큰 보정각이나 전체 feedback gain으로 외삽하지 않는다. 공통 20개 초기 필드·other80 전체 명령·앞 2초 native state/trace·첫 484개 전체 명령은 exact다. 기존 152영상을 보존하고 완료 4개와 partial 2개를 더한 [영상 모음 v14](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v14.md:1)는 158개다. 범례 위치만 수정한 v2 그림을 사용하며 원 그림·producer도 보존했다.

실행되지 않은 후처리 소스 변경본을 별도 보존하고 실제 분석에 소비된 원문으로 byte-exact 복구했다. 물리·분석 재실행 없이 같은 원문으로 영상 수집을 완료했으며 입력/사본/닫힌 로그 SHA를 대조했다. 세 완료 기록의 작은 실제 관절한계 초과 0.000099949539 rad는 목표한계 통과와 구분한다. 새 actor 추론·학습은 0이다. 최종 독립 검수와 원본 보존 감사는 해당 phase 기록으로 봉인한다.

다음 [L_Wrist_y ±0.005 rad 실제 제어권 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md:1)은 원 quiet 초기 자세·고정 LA·PD·기존 손목 X 명령을 유지하고 검지 추가 보정은 0으로 둔다. 아직 구현·실행하지 않았다. 손가락의 연주 제어권을 남기며 팔·손목의 기타 보정 응답을 먼저 측정한다.

- [x] 검지 두 완료 5초 응답·첫 native 실패와 별도 재시도 보존
- [x] 저장 분석 47검사·실제 영상/그림 검토·한국어 결과 문서
- [ ] 다음 손목 실제 응답 두 조건 구현·검증


## Quiet 손목 Y 실제 제어권 측정 준비

직전 검지 phase는 독립 PASS·최종 감사32검사·3990파일/이전3172파일 보존 확인으로 마무리했다. [손목 실행 leaf](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_SUPPORT_EXECUTION.md:1)에 따라 새 runner와 봉인기를 추가했다. 원 quiet 초기값·LA·PD·손목 X 파형을 유지하며 Wrist_y만2~2.5초에±.005rad ramp한다. 아직 실제 물리 미실행이다. 두 실제 초기화/같은 초기화5초·151frame 영상으로 제한하며 자동 재시작하지 않는다. 독립 명령 검산·사전 검수 뒤 실행한다.


## Quiet 손목 Y 두 실제 응답 완료

[초기값·5초 영상·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/README.md:1), [변경 파일 절대 경로·실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/CHANGED_FILES.md:1), [누적 그림 설명 §119](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2116)을 추가했다. 각 ONE native 초기화/1200step/151frame으로 두 5초를 완료했으며 재시도 없이 총2초기화·2400step이다. 저장분석42검사·몸통 실제각 진단7검사를 통과했다. 이번 앞2초 공통구간은 응답 측정용이며 연주 선행 WAIT 절차를 도입한 것이 아니다. 66관절 제어권을 유지한다.

기준/plus/minus 종료 초기 오차는13.819696/14.026170/13.634644mm 및2.918277/2.931572/2.907466°다. Minus는 두 종료오차가 약간 작지만 후기1초창 변동.676770mm/.124564°가 기준.648625mm/.115306°보다 컸다. 손목Y의 유한응답은 검지보다 컸으며 큰각도나feedback gain으로 외삽하지 않는다. Palm 양의 raw lambda 접촉은 여전히 없고 실제native관절한계 최대초과.000099949539rad는세기록동일하다. 몸통9목표가 held여도 실제 관절좌표의최대변화는Spine_z약.06176rad(3.54°)였다. 고정root/하체 또는 몸통전체world회전각과 구분한다.

분석1958입력/1957사본·직접1952입력,수집169/168사본,그림1959입력/14선택사본의전후/currentSHA와닫힌log를대조했다. 실제4panel PNG와t0/t5 Gym장면·네영상ffprobe151/30fps/5.033333s를확인했다. 기존158영상을보존해 [영상모음v15—162개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v15.md:1)로추가했다. 독립최종검수와보존감사는해당phase기록에봉인한다. 새actor추론/학습0이며자연연주·정책호환·폐루프안정성은미검증이다.

다음 [손목Z두방향계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_Z_SUPPORT_AUTHORITY_PLAN.md:1)은원quiet초기/LA/PD/손목X파형을유지하고Y추가보정0·Z±.005rad두actual응답을측정한다. 아직구현·실행하지않았다. Y/Z방향의독립성과기여를확인한뒤시험한각도범위에서관절목표feedback을설계한다.

- [x] Wrist_y두actual5초·42저장검사·몸통실제관절각7검사
- [x] 실제PNG/영상·한국어결과/초기값/절대파일줄·162영상정리
- [ ] Wrist_z두응답과제한된관절feedback설계


## Quiet 손목 Z 실제 응답 준비

직전Y두actual5초/42저장분석·몸통7검사·최종25감사검사와3658파일/이전7161파일보존을완료했다. [Z실행leaf](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_Z_SUPPORT_EXECUTION.md:1)에따라새Z runner·분석·수집코드를추가하고AST/두1200목표독립검산을통과했다. Z±.005rad외80/모든손가락·첫484전체목표가exact이며원초기값/LA/PD/자유기타조건을유지한다. 아직native미실행이며독립사전검수뒤각ONE5초를기록한다. Y/Z두응답의독립성·오차축기여를보고제한관절feedback을설계한다.


## Quiet 손목 Z 두 실제 응답·Y/Z 비교 완료

[결과·초기값·실제 5초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/README.md:1), [변경 파일·실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/CHANGED_FILES.md:1), [누적 시각 보고서 §120](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2124)을 추가했다. Z±0.005rad 두 조건은 각각 ONE 초기화/1200step/151frame으로 완료했다. 원 quiet 초기각·LA·PD·손목 X 파형·고정 root/하체·자유 기타를 유지했고, 저장 분석42검사와 몸통 실제 관절각7검사를 통과했다. 재시도 없이 새2초기화/2400step이며 actor 추론·학습은0회다.

기존 baseline/Zplus/Zminus 종료 초기 오차는13.819696/13.817638/13.829543mm 및2.918277/2.895722/2.946758°다. Plus의 위치 개선은 약0.002058mm로 극히 작으며 회전과 후기 변화도 조금 줄었다. Minus는 악화됐다. Palm 양의 raw lambda 접촉은0이고, 몸통9목표 유지와 실제 Spine_z 관절좌표 약3.54° 변화는 구분한다. 미세한 차이를 성공/실패 기준으로 과장하지 않는다. 네 실제 영상의151frame/30fps/5.033333초와 실제 도표·장면을 확인했으며 기존162영상을 보존해 [모음v16—166개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v16.md:1)에 추가했다.

Y/Z 저장 비교v1은 baseline 보존목록을 Y inventory에서 찾은 참조 오류로 계산 전에 종료했다. 원 소스·invocation·실패 기록을 보존하고 v2에서 각자의 inventory를 엄격 대조했다. 물리·분석 재실행 없이 v2의6검사를 통과했다. 정규화된6×2 응답은 rank2·조건수2.719646212이며, Y−.005/Z+.005 동시 입력의13.635787mm/2.882135°는 모델 예측이다. 아직 실제 동시 입력이나 폐루프 안정성·연주를 검증한 결과가 아니다.

다음 [현재 기타 오차를 쓰는 Y/Z feedback 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md:1)은60Hz에서 기타 world p/q 오차로 두 손목 목표 보정을 계산한다. 축당±.005rad·.002rad/s로 제한한 OFF/ON 두5초를 비교하며, q_hold와 안정화 보정을 한 최종 PD 목표로 합친다. 이 계획은 아직 구현·실행하지 않았다. 전체66관절 제어권을 유지하고 이후 fret/strike 목표와의 합성을 검증한다.

- [x] Z 두 실제5초·42저장 검사·몸통7검사·실제 영상/도표/한국어 산출물
- [x] Y/Z 저장 응답 비교v2 6검사·v1 실패 보존·제한된 실제 feedback 계획
- [ ] 현재 기타 오차 기반 Y/Z OFF/ON 구현·검산·두 실제5초 검증


## Quiet 손목 Y/Z 현재 기타 오차 feedback 구현 준비

직전 Z phase는 독립 최종 PASS·27개 보존 감사 검사와3676파일/이전10818파일 보존 확인으로 마무리했다. [Y/Z feedback 실행 leaf](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md:1)에 따라 현재 기타 world p/q 오차를 읽는 작은 helper와 새 OFF/ON 녹화·봉인 runner를 작성했다. 기타 오차→두 관절 목표 보정이며 기타에 복원 힘을 가하거나 state/pose를 덮어쓰지 않는다. 기존66관절 제어권·초기값·LA·PD·손가락 목표를 유지한다. 아직 실제 물리는 실행하지 않았다. 독립 수학/1200목표 검산과 사전 검수 뒤 각 ONE 5초를 진행한다.


## Quiet Y/Z 현재 기타 오차 feedback 두 실제 비교 완료

[초기값·실제5초 영상·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/README.md:1), [변경 파일·실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/CHANGED_FILES.md:1), [누적 그림 설명 §121](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2142)을 추가했다. 순수 수학/목표12검사·독립 사전 검수 뒤 OFF/ON 각 ONE 초기화/1200step/151frame·제약위반0으로 완료했다. 두 실행의106입력/사본·닫힌log를 대조했으며 새actor추론·학습은0회다. 원초기각·LA·PD·Wrist_x파형·고정root/하체·자유기타·66관절권한을 유지한다.

현재 기타 world p/q 오차에서 gradient를 구해 Y/Z 목표 보정각을60Hz로 갱신했다. [56개 저장 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/analysis.json:1)에서 실제 명령직전 상태→오차→rate→delta→최종PD목표를 독립 재계산했고, OFF 전체native경로·81목표가 기준과exact함을 확인했다. ON은첫484전체목표/2초prefix/나머지79와손가락목표가exact이며첫분기는step485다. 종료 오차는OFF13.819696mm/2.918277°에서ON13.665215mm/2.889313°로소폭줄었다. 후기1초변화는.648625mm/.115306°에서.693968mm/.124492°로조금커졌으며미세변동을과도한성공/실패기준으로삼지않는다. ON최종보정각은Y−.005/Z+.003548712rad다. 몸통9목표유지와실제Spine_z좌표변화약3.54°를구분하고palm양의rawlambda접촉0을숨기지않는다.

분석direct1956⊂wrapper1962입력/선택11사본,도표direct1960⊂wrapper1969/선택32사본의전후/currentSHA·닫힌log를확인했다. 실제4panel PNG와t5 Gym손장면·4원영상151frame/30fps/5.033333초를확인했다. 영상수집wrapper는4복사/새색인생성뒤metadata인자slice오류로exit1이었다. 원소스·사전기록·로그·출력을보존하고새readonly회수감사9검사/2178입력으로기존166영상+새4영상·색인SHA를확인했다. 물리·분석·도표·수집재실행은없다. 미기록collector STATUS/wall은null로남기며 [영상모음v17—170개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v17.md:1)와원실패/회수결과를분리해보존한다.

다음 [startup feedback 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_STARTUP_FEEDBACK_PLAN.md:1)은같은초기값·보정각±.005rad에서feedback을시작부터활성화하고slow/fast두변화율을비교한다. 아직구현/실행하지않았다. 현재2초이전최대위치오차14.608483mm는보정OFF라동일했으므로초기흔들림도직접검증한다. 유지구간국소응답의startup유효성·자연연주·정책호환·전역폐루프안정성은미검증이다.

- [x] 현기타오차→Y/Z목표합성·12수학/목표검사·두actual5초·56저장검사
- [x] 실제영상/도표·원수집wrapper실패보존·회수감사9검사·170영상·한국어산출물
- [ ] 시작부터feedback slow/fast 구현·독립검수·최대두actual5초


## 사용자 요청: 실험 중단·정리 및 다음 방향 논의

2026-10-08 사용자가 여기서 작업을 마무리하고 향후 방향을 정하자고 요청했다. 새 실험과 자동 반복을 중단한다. 기존 startup slow/fast 계획도 보류하며, 사용자와 재개 방향을 정하기 전 실행하지 않는다. 마무리 상태 확인에서 실행 중인 stability_adapter_2 module process는 없었다.

[메인 인계·재개 방향 제안](/home/ajou/yigyu/3/stability_adapter_2/SESSION_HANDOFF_2026-10-08.md:1)과 [결과·영상 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/SESSION_WRAP_UP_2026-10-08.md:1)을 새로 정리한다. 현재 후보의 초기 기타 변화는 약14mm/3° 규모이고 이후 움직임은 작지만, 연주 가능한 손 자세·checkpoint 전환과 자연스러움은 아직 검증하지 않았다. 미세 오차 탐색보다 기존 영상의 자세/연주공간 검토→fret/strike 목표·관측·history 연결 설계→새5초 연주 전환 검증을 다음 논의의 권장 방향으로 둔다. 이는 새 실행 결정이 아니며 성공 기준을 임의로 확정하지 않는다.

최신 feedback/Y/Z/no-strap 봉인 파일과170개 영상을 보존한다. [마무리 상태 점검](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/session_wrap_up_2026-10-08_v1/status_check.json:1)에 새 물리·학습 실행0, 기존 파일의 크기/SHA 대조와 실행 프로세스 부재를 기록한다. 기존 phase·소스·산출물을 수정하지 않는다. 이 추가 기록이 위의 과거 다음 실험 계획보다 우선한다.

방향 논의·선정만으로 새 trial을 시작하지 않는다. 새 실험은 사용자의 재개 요청 뒤에 진행한다.

## 사용자 요청: 수동 기타 초기 배치 도구

[실행·키 설명](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_EDITOR_GUIDE.md:1)과 [구현 계획](/home/ajou/yigyu/3/stability_adapter_2/INTERACTIVE_GUITAR_POSE_PLAN.md:1)에 따라 Isaac Gym native viewer 키보드 편집기를 추가했다. F1~F6으로 이동/회전 축을 고르고 J/L로 조절하며, S로 여러 후보의 절대 p/q·관절각·PD 목표·스트랩 조건과 실제 카메라 이미지를 저장한다. 초기 배치 편집은 시간이 멈춘 별도 EDIT 상태다. Space는 자유 기타의5초 물리와 양 시점 녹화이며 이후 state setter를 차단한다. E로 fresh 환경을 만들어 선택한 초기 배치로 돌아간다. root/하체 고정·상체9 PD·66관절 구조·원본 고정 스트랩 길이를 유지한다. 스트랩 OFF는 힘과 표시 모두 끈다. 이번 preview는 일정 목표이며 손목 파형/feedback/actor학습은 없다.

수학4검사와 독립 사전검수 뒤 actual Xvfb 키 입력 및 ONE5초/1200step/151frame/두영상이 완료됐다. 원 검증 harness는 마지막 NumPy bool JSON 직렬화에서 exit1이어서 소스·truncated JSON·로그를 보존했다. 별도 정적v2의27검사가 통과했고 신규 물리0으로 전체 기타link 변환·human/PD/목표 불변·실제 키·undo/save/load와 기존5초 기록을 확인했다. 원 물리 시작 후 상태 쓰기는0이며 차단1은 의도된 guard 검사다. OFF는 이번 정적 표시/raw 녹화 분기만 확인했다. 직접 사용자 마우스 조작·자연 자세·관통 허용·연주 가능성은 아직 인증하지 않는다.

[결과·실제 이미지 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/README.md:1), [변경 파일 실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/CHANGED_FILES.md:1), [영상 모음v18—172개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v18.md:1)에 정리한다. 기존 자동 탐색·startup feedback 실행은 계속 중단 상태다. 이번 사용자 요청은 수동 도구 구축·검증에 한정된다.

## 사용자 정정: 자연스러움 판단 도구는 물리 없는 정적 전용

기타 위치·회전의 시각적 자연스러움을 고르는 도구에는 물리적 상호작용이 없어야 한다는 사용자 정정을 반영했다. 새 기본은 `bash /home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor_static.sh`이며 [정적 사용 가이드](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_GUIDE.md:1)를 따른다. 초기화부터 중력0·물리적분/외력 API 차단, UI는 렌더·수동편집만 수행한다. 물리시간은항상0이고접촉반응·PD움직임·스트랩힘이없다. T는참고route표시만바꾸며Space/E도물리를시작하지않는다. 후보physics_enabled=false/steps0/strap_visible를기록한다. 위v1의물리preview/launcher는과거재현용보존이며새정적도구에서는제거했다.

actual native Xvfb의F3/L/SPACE/E와6축·undo/save/load·사람상태불변·API차단18검사를통과했다. 새물리step/trial/영상생성은0이다. [실제이미지·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/README.md:1)과 [변경파일줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/CHANGED_FILES.md:1)에남긴다. 자연배치선택용정적도구이며지지가능성검증이나자동탐색/학습재개가아니다.

정적도구의최종권장진입점은 `bash /home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_static.sh`다. [최종entry설명](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_ENTRY.md:1)을따른다. 원정적harness가T/S를draw없이연속호출했을때OFF사진에이전viewer선이잔류했다. 실제UI도같은eventbatch에서가능하므로새entry는사진저장직전에viewer선을지우고촬영후현재표시를복원한다. 원정적소스/사진은보존했다. 추가정적4검사에서T/S연속저장두PNG의주황선pixel0·전체상태불변·시간0을확인했다. 물리trial/영상생성은계속0이다.

## 2026-10-08 기타 위치·회전의 정적 시각 비교

사용자 요청으로 실제 Isaac Gym 카메라에서 기타만 바꾼30개 배치를 비교했다. 모든 배치에서 물리 스텝0·humanoid body/DOF 상태 동일을 확인했다. 자동 안정화 실험/학습은 재개하지 않았다.
권장 중심은 바디 중심 world [169.6,65.0,676.0]mm, 넥 상승22°/관객 방위5°/기준 대비 앞판 눕힘+3°다. 시각적 탐색 시작 범위는 좌우±20mm, 앞뒤·높이-10~+20mm, 넥17~27°/방위0~10°/눕힘0~+5°다. 현재 양손과의 정렬을 유지하는 인증 범위가 아니며 팔·손 재배치가 필요하다. 기본 시작값을 교체하거나 물리 성공 gate로 채택하지 않았다.
[권장안·좌표 정의](/home/ajou/yigyu/3/stability_adapter_2/STATIC_GUITAR_NATURAL_RANGE_PROPOSAL.md:16)와 [native 이미지·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/README.md:1)를 따른다. 추천 후보는 해당 결과의 combined/scene/candidate_000/pose.json이다. 회전 비교의 pivot은 바디 중심이며 기존 편집기의 actor-root pivot과 다르다.


## 2026-10-09 재개 — 기타 배치 source screen 및 학습 자원 검사

사용자의 구현·실험·학습 요청에 따라 자동 중단 상태에서 다시 진행한다. 과거 손 각도 탐색을 반복하지 않고 저장된 기타 단독/조합 30개를 고정된 사람 자세에서 source geometry로 검사했다. [결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_pose_geometry_screen_v1/README.md:1)에서 전체 human–guitar source overlap이 없는 후보는 0개다. `audience_yaw+10deg`는 왼손 overlap은 없지만 오른손/팔이 포함된 20쌍의 전체 overlap이 남는다. 새 native 초기화·physics step·actor 추론은 0이다.

학습 환경에는 NVIDIA driver/device가 없고, CPU Strike smoke는 runner의 CUDA resource gate에서 중단됐다. PPO update는 0이며 strict G0 qualification이 없는 source checkpoint를 우회하지 않았다. 상태 근거는 [연주 연구 재개 요약](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/05_IMPLEMENTATION_AND_EXPERIMENT_RESULTS.md:1), [계획·체크리스트](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/04_IMPLEMENTATION_EXPERIMENT_TRAINING_PLAN.md:1), [학습 preflight](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/training_preflight.json)에 있다. 저장된 정적 자연스러움 제안은 시작 기타 pose나 안정화 goal로 채택하지 않았다.

## 2026-10-08 연주 흔들림을 고려한 느슨한 외곽과 끝지점

[새 범위 결정](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_PLAYING_SWAY_ENVELOPE_DECISION.md:5)은 기준 바디 중심에서 world XYZ±50mm, 넥 상승10~40°/관객 방위-10~20° 절대각, 기존 기준 대비 앞판 눕힘-5~+15°를 시각적 외곽으로 제안한다. 선호 중심은22°/5°/눕힘+3°다. 연주 동작에서 팔·손이 함께 따라가는 여유이며 현재 고정손 정렬만으로 좁히지 않는다. 모든 축값의 동시 조합·동적 유지·관통 없는 자세를 인증하지 않으며 controller/gate/기본pose/학습은 변경하지 않았다.
중심1개와12개단독끝점의 실제 Isaac Gym 정적 촬영에서 물리0·human body/DOF 동일을 확인했다. [끝지점 이미지·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/README.md:1)에 정면/측면/손 비교표6개와 저장pose를 제공한다. 비교표 최초 버전의 보존 누락은 결과 기록에 명시하며 원본native와최종v2비교표는보존했다. 자동 물리 실험은 계속 중단 상태다.

## 2026-10-09 사용자 지정 위치·Euler 경계 이미지

사용자가 제시한 기타 월드 위치 X `[-0.50,-0.15] m`, Y `[-0.15,0.15] m`, Z `>=0.65 m`와 extrinsic Euler XYZ X `[45,90]°`, Y `[50,100]°`, Z `[135,180]°`를 단일 좌표씩 바꾸어 정적 Isaac Gym 장면에서 렌더링했다. 기준값은 위치 `[-0.325,0,0.65] m`, 회전 `[67.5,75,157.5]°`다. 12개 포즈에서 물리 step 0, 사람의 body/DOF 상태 불변, 렌더 후 native 상태 불변을 확인했다. Z 상한은 주어지지 않아 표시하지 않았고, 이미지 자료는 접촉·관통·안정성을 판정하지 않는다.

[경계 이미지·케이스별 입력값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2/README.md:1)에 위치/회전 각 3시점 비교표와 12개 실제 경계값을 보존한다. 원본 Isaac Gym 포즈 캡처는 [v1 native 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/comparison.json:1)에 있고, 한글 글꼴을 사용한 최종 비교표는 그 native 이미지를 해시 확인해 새 v2로 생성했다.

## 2026-10-09 경계 이미지 기준 높이 Z=0.80m

사용자 요청에 따라 전체 단독 경계 장면을 기타 actor root `Z=0.80m`에서 다시 렌더링했다. X/Y와 Euler XYZ 범위는 유지하고, 위치 그림의 Z 행에는 기존 `0.65m`와 새 `0.80m`를 비교해 상한 미지정을 표시했다. 12 native 장면에서 물리 step 0, 사람 body/DOF 불변, 렌더 상태 불변을 확인했다. [재생성 이미지·값 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_z080_v1/README.md:1)에 front/side/hands 비교표를 둔다. 정적 시각 비교이며 실제 접촉·겹침·안정성 판정은 아니다.

## 2026-10-09 front/side/top 허용영역 뷰

사용자 요청으로 동일한 고정 기타 pose와 root 위치 허용영역 박스를 정면·측면·위에서 촬영해 [docs/2026-10-12/기타허용범위](/home/ajou/yigyu/3/docs/2026-10-12/기타허용범위/README.md:1)에 저장했다. 박스는 X `[-0.50,-0.15]m`, Y `[-0.15,0.15]m`, Z `[0.65,0.883738]m`이며, Chest rigid-body origin을 높이 상한 근사로 썼다. 기타 actor-root 기준점과 Chest 원점을 표기하고 native 카메라 투영/깊이 검사를 적용했다. 물리 step 0, body/DOF 및 기타 상태 불변을 확인했다. 첫 카메라 저장 시도의 부분기록은 보존하고, 수정된 검사로 최종 3장을 생성했다.

## 2026-10-09 기타 위치영역 박스와 기준점

여러 기타 위치를 나열하는 대신 기타를 root `(-0.325,0,0.800)m`에 고정하고 월드 위치 허용영역 X `[-0.50,-0.15]m`, Y `[-0.15,0.15]m`, Z `[0.65,0.883738]m`을 깊이 검사된 박스로 표시했다. Z 상한은 저장된 초기 자세의 `Chest` rigid-body 원점 높이를 가슴 높이 근사로 사용했다. 노란 점은 기타 actor-root 위치 기준점, 분홍 점은 Chest 원점이다. 박스는 root point 범위이며 전체 기타 mesh의 부피 제한이 아니다. native scene에서 물리 step 0, 휴머노이드 상태 불변 및 렌더 전후 state 동일을 확인했다. [박스·기준점 이미지와 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/position_region_box_v1/README.md:1)에 기록한다.

## 2026-10-09 위치영역 박스 시각 강조 보완

기존 위치영역과 actor-root 기준점을 유지한 채, 범위가 이미지에서 더 잘 보이도록 front/side/top native 장면 위에 깊이 검사된 반투명 면과 굵은 외곽선을 덧그렸다. 결과는 [범위강조_v2 이미지와 설명](/home/ajou/yigyu/3/docs/2026-10-12/기타허용범위/범위강조_v2/README.md:1)에 저장했다. X `[-0.50,-0.15]m`, Y `[-0.15,0.15]m`, Z `[0.65,0.883738]m`, actor-root 기준점 `(-0.325,0,0.800)m`, Euler XYZ `[67.5,75,157.5]°`는 동일하다. 이미지 해시와 시점별 면/모서리 표시를 재검사했고, physics step 0·humanoid 및 기타 상태 불변을 확인했다. 이는 범위 표기 보완이며 접촉·겹침·안정성 검증이 아니다. 구현 계획은 [POSITION_REGION_VISIBILITY_PLAN.md](POSITION_REGION_VISIBILITY_PLAN.md:1), 생성기는 [render_position_region_visibility.py](render_position_region_visibility.py:1)다.

## 2026-10-09 넥 수평·앞판 정면 초기 회전 후보

사용자 확인에 따라넥0°수평과앞판법선world+Y정면을우선초기회전후보로계산했다. 이채팅의기존바디중심을유지하며기타root p도함께보정했다. 넥-10/0/+10°의실제IsaacGym3정적장면에서물리0·사람body/DOF동일·렌더상태불변·앞판방향/바디중심/목표넥각검사를통과했다. NVIDIA접속불가상태에서도CPUPhysX+Mesa소프트웨어Vulkan으로native정적카메라는작동했다. CUDA학습자원가용성을뜻하지않는다.
[결정·후속설계](/home/ajou/yigyu/3/stability_adapter_2/HORIZONTAL_NECK_INITIAL_DECISION.md:3)와[실제이미지·후보pose](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/README.md:1)를따른다. 현재왼손이넥보다높아팔손초기각을함께내려맞춰야한다. 기본시작pose/PD/스트랩/controller/학습은변경하지않았고접촉·관통·자유기타안정성은미검증이다.

## 2026-10-09 사용자 허용 범위 안에서 연주

사용자가 넓게 설정한 기타 위치·회전 범위 안에서는 초기점의 정확한 복귀보다 연주를 우선한다. 내부의 초기점 복원 비용은 0으로 설계하고, 경계 접근/이탈에는 부드러운 보정을 합성한다. 작은 떨림과 필수 정지 대기로 연주를 막지 않는다. [제어·범위 계약](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:3)을 후속 설계의 기준으로 삼는다. 수평 넥 후보는 저장 위치 상자 안에 있고 회전 xyz [67.5,90,157.5]°로 허용 회전 집합에 포함된다. Euler 특이점 때문에 단일 as_euler 결과를 축별 비교하는 판정은 사용하지 않는다. 이번은 문서·오프라인 계산이며 새 controller/판정기/연주/물리/학습은 미실행이다.

## 2026-10-09 현재 작업 파일 정리

사용자 요청에 따라 종료된 단독 실험 파일508개와 캐시2폴더를 제거했다. 현재 진입점·테스트·필수 소스 해시 의존성을 보존하고, 추가 안내를 포함해 루트177개 파일을 남겼다. [현재 파일 안내](/home/ajou/yigyu/3/stability_adapter_2/CURRENT_FILES.md:1)에서 작업을 시작한다. 삭제 전 원본은 [정리 결과·압축 백업](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/README.md:1)에 보존한다. 위의 과거 기록 중 삭제된 파일 링크와 옛 실험 명령은 백업에서 별도 작업 사본으로 복원해 확인한다. 기존 docs 결과·영상·로그와 stability_adapter/는 보존했다. 새 물리·연주·학습 변경은 없다.

## 2026-10-09 최신 초기 배치: 무스트랩·왼손 세 면

최신 사용자 조건에서는 스트랩 힘·표시를 OFF, 넥 수평·줄 면 정면, 오른손 비접촉으로 한다. 왼손은 손바닥 넥 아래면·엄지 뒷면·나머지 네 손가락 전면의 초기 접촉 목표를 찾는다. 현재 기타 p/q로 영역·법선을 갱신하는 CPU helper와 검사 5개를 완료했지만 새 초기 관절각·실접촉·추종 제어·5초 자유 물리는 미검증이다. 최신 [계획](/home/ajou/yigyu/3/stability_adapter_2/LEFT_UNDERNECK_CONTACT_PLAN.md:1)을 따르며 과거 스트랩 고정 조건은 이번 초기 후보에 적용하지 않는다.


## 2026-10-09 실제 무스트랩 초기 배치와5초 비교

수평 넥·앞판+Y·오른손 분리·왼손 아래/뒤/앞 근접 배치를 실제 Isaac Gym에서 만들었다. 기타 root를25mm 올린 별도 입력이며 root/하체는 고정,기타는 자유물리다. 실제 native 초기각/FK/모델 한계/손바닥 위쪽/기타 초기 상자를 통과했고 source 형상 기준 교차0·오른손 보수적 간격52mm다. source 근접은 실제 접촉 인증으로 해석하지 않는다.

상수 PD는 최대133.4mm/28.5°,현재 넥 회전을 따르는 손목 추종은261.4mm/70.4°로 악화됐다. 같은 초기값·PD의 팔24 목표 유지 PI는62.4mm/15.5°,종료34.4mm/4.6°·높이0.667m로 개선됐다. 2~5초 변화는1.85mm/0.30°이며151표본 중3개가Z하한0.65m를 최대0.66mm 벗어났다. thumb/pinky의 접촉 row는 관측됐으나150개 접촉표본에서는 손바닥·검지·중지 접촉이 없었다. 세 면 지속 지지·전체 회전 범위 판정·실제 연주·학습 성공을 뜻하지 않는다.

[결과·실제 초기 이미지·시작부터5초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/README.md:1),[팔 유지 진단 계획](/home/ajou/yigyu/3/stability_adapter_2/UNDERNECK_ARM_HOLD_PLAN.md:1),[실행 코드](/home/ajou/yigyu/3/stability_adapter_2/underneck_pose_trial_v5.py:1)를 따른다. 힘 setter 누락을 추가 검사에서 발견해 소비된v4를 보존하고v5에서 보완했다. 확대 보호/PI 검사4개 통과 후 같은5초 물리 trace/controls를 재현했다. 다음 소단계는 현재 넥 기준 손바닥·검지·중지 접촉 보정이며 초기각을 붙잡는 진단 PI를 그대로 연주 제어로 사용하지 않는다.


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


최근 연속 작업: EFFORTgeometry 타현1이지만 기타44.868°로 미채택. 다음은 POSITIONgeometry 비교이며 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_POSITION_GEOMETRY_PI_PLAN.md)에 기록했다.


현재 다음 설계: [기타 기준 손 방향 선호](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_SOFT_ORIENTATION_PLAN.md). POSITIONgeometry도45°로 미채택이고, 기존 안정적인 policy+PI를 비교 기준으로 쓴다.


다음 실험: [human R9 body-relative SO3 spring](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_BODY_ROTATION_SPRING_PLAN.md). 오류계산만바꾸고원본목표/시간/손가락/기타범위를보존한다.


다음소단계: [중지·약지fourhinge소폭굽힘](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_FREE_FINGER_CURL_PLAN.md). sourcepinch9는유지하고모델finger21중4requestedtarget만boundedresidual.


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


## 현재 기타 기준 왼팔9 추종 비교

2초준비 뒤 손가락21은동결된Fret checkpoint로계속제어하고왼팔9만목표보정하는경로를구현했다. raw COLOR native녹화로OFF전체12.9167초를재현했으며기존native상태/목표/정책출력exact다. 직접source손목목표추종은기타이동을악화시켜5.6333초finger_back으로끝났다. 준비지지관계의작은추종(v2)은공통11.1333초최대회전47.863→19.408°를줄였지만이동73.190→126.888mm·box초과68.363mm로악화했고wrong_press·압현성공0%다. 상대손목오차는소폭감소했으나연주완주는미달이다.

다음은허용범위복원과연주준비자세정렬이다. 현재기타를따라가는것과기타를범위안에유지하는것을구분한다. [현재지지추종결과·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/README.md:1) · [세부계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_CURRENT_GUITAR_SUPPORT_V2_PLAN.md:1).


## 손바닥·엄지 지지 실험 결과 — 2026-10-11

초기각을 최대약1.145° 조정하고 실제 Isaac Gym에서 기존/초기자세 변경/접촉추종/자세유지 결합의 네 조건을 각각5초 녹화했다. 손바닥·엄지 동시 양의 solver 응답은0/22/73.67/44.33%로 늘었지만, 기타최대이동/회전은62.96mm/13.63°,62.80mm/13.70°,96.22mm/16.24°,63.30mm/13.76°였다. 접촉 증가만 확인했으며 안정화 성능 개선은 확인하지 못했다. 마지막 조건은 기존과 거의 같은 수준이다.

root/하체고정·몸통PD유지·무스트랩·self-collision·자유기타 조건이며, 기타고정/손부착/추가힘/pose덮어쓰기는 없다. Fret 연결 gate는false, checkpoint/학습0이다. 최대값은30Hz자세, 접촉은60Hz제어직전300표본이고 rawlambda는뉴턴힘·정확접촉면·마찰/미끄럼인증이 아니다. 다음은 현재기타추종과허용범위복원/연주준비정렬을분리하고 엄지의Fret/안정화 제어권을 단일PD목표로 합성하는 설계다.

[네 조건 그림·초기값·전체영상·검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/README.md:1) · [소단계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_THUMB_POSTURE_SUPPORT_V1_PLAN.md:1).


## 현재 학습 구조 후보 — 왼손 공동 정책 (2026-10-11)

자유 기타에서 지지와 압현을 하나의 왼손 33관절 정책이 맡는 설계 초안을 추가했다. 기존 Fret 동결+잔차는 비교 대상으로 유지한다. 최종 양측66 제어 범위는 유지하며, 이번 후보에서는 오른쪽33과 나머지15의 PD 목표를 유지하고 실제 native81 관절 상태를 관측한다.

Actor D→256ELU→256ELU→33, 별도 Critic D→256ELU→256ELU→1과 PPO는 구현 전 제안이다. 관측 차원D, 학습 설정과 보상 가중치는 미확정이다. 허용범위 안 초기점 복원 비용은0이며 지속 손바닥 접촉을 성공 조건으로 삼지 않는다. 새로운 시뮬레이션·checkpoint 연결·학습은 이번 문서 단계에서 실행하지 않았다.

[주 설계와 구현 순서](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:1) · [설계 그림·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/README.md:1) · [변경 파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/CHANGED_FILES.md:1).


## 최신 정책 설계 정정 — 전체 상체81, 512→256 (2026-10-11)

사용자 정정에 따라 하체 제외 전체 상체81관절을 공동 정책이 제어한다. 몸통9+목/머리6+양팔/양손66이며 root/하체 fixed-lower는 유지한다. 이전 왼손33/held48/최종66 제안은 과거 초안이다. 몸통과 머리는 작은 움직임을 선호하되 정책의 제어권을 남긴다.

Actor D→512ELU→256ELU→81, 별도 Critic D→512ELU→256ELU→1을 기본 설계로 삼는다. 관측D와 학습 설정은 미정이며 실제 구현·학습은 이번 문서 작업에서 하지 않았다. [최신 설계](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:1) · [설계 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/README.md:1) · [변경 파일과 행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/CHANGED_FILES.md:1).


## 최신 움직임·보상 후보 v3.1 — 2026-10-11

상체81/512→256 제어권을 유지하며, 몸통9 목표의native∩초기±5° 후보와 실제±2°/Chest3° 비용없는구간을추가했다. 목/머리는시선최대0.01/초의약한선호를두고, 양측Thorax~손가락은모델범위·연주목표로움직인다. 머리의강한초기각유지나팔/손초기각복원비용은없다. body목표한도는actual각고정이아니다.

압현·타현·기타범위·몸통·충돌위험·관절한계/목표변화항의초당계수와단발이벤트규칙을정했다. 수식/합성사례26개를검사했으며원본detector/실제물리/학습검증은아직후속단계다. [최신보상설계](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:29) · [함수그래프·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/README.md:1) · [변경색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/CHANGED_FILES.md:1).


## 최신 보상 제안 v4 — 2026-10-11

[프로젝트 계획 대조와 보상 설계](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:14)를 추가했다. 음악 결과→유지/전환/timing→작은 접근/자세 선호의3계층으로 예산을 제한한다. 실제 crossing 시 sounding fret가 우선이며 원본 finger-based/source 지표는 보존한다. 긴 음의 유지 보상·REST/idle·무해한 추가압현·유효 영역 접근·부분 strum·고유 wrong crossing·fatal 미정산 ledger를 명시했다.

상체81/512→256·몸통 작은 움직임·아주 작은 시선 선호·기타 허용범위 내부 비용0은 유지한다. 42합성 산술 검사 pass이며 native detector/geometry/tracker 구현·물리/학습 인증이 아니다. SO(3)/sounding-state 및 fatal crossing 상한·γ/ledger 계약 검증 전 pilot을 시작하지 않는다. 현재 환경/보상 런타임은 변경하지 않았다.


보상v4 문서/산술/독립 검수 마감: [설명과 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/README.md:1) · [변경 파일/실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/CHANGED_FILES.md:1). 환경/물리/학습에는 아직 적용하지 않았다.


### 보상 v4 학습 유인 감사

[감사 보고서](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:1)를 추가했다. 구조는 좋지만 평균 U 대연속 dropout,2차 유지 대3차 보조항,긴 구절의 신호 희석,할인/지급ledger와 원본 판정/종료 매핑을 닫기 전 학습 준비 완료가 아니다. CPU source tracker에서54/60 동일 유지율도 최장dropout1/6에 따라 성공/실패가 갈렸다. [계산·비교 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/README.md:1)은 native 렌더가 아니다. 기존 v4/환경/가중치 변경0,물리/학습0. 다음은 판정·시간·종료 계약과 유지 반례를 정리하는 소단계다.


### 새 환경 기본층 — 초기 상태·548D 관측·상체81 제어

현재 실행층은 [learning_scene_v2.py](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:11), 공통 계약은 [environment_contract_v1.py](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:33), 설정은 [environment_foundation_v1.json](/home/ajou/yigyu/3/stability_adapter_2/environment_foundation_v1.json:1)이다. reset은 진단용 새 CPU PhysX 장면 생성이며 root/하체 fixed·스트랩 OFF·자유 기타다. 상체81을 native POSITION 목표로 한 번 제출하고4물리 step 동안 유지한다. body9는 초기±5°∩native, head6/arm24/finger42는 native 목표 범위와부위별rate를 적용한다.

[설계](/home/ajou/yigyu/3/stability_adapter_2/ENVIRONMENT_FOUNDATION_V1.md:28)에서 raw state/548 기반 observation/action을 구분했다. 움직이는 기타 G 상대속도에 병진·각속도를 반영하고 초기 기준/직전 최종 목표를 노출한다. 준비2초에도 제어·물리는 계속되며 음악 clock만2초 뒤 시작한다. 가짜 음악 상태·0보상·완료 판정은 추가하지 않았다.

CPU9 검사와두 native5초 실행에서 초기값exact·관측유한성·target readback·rate/bounds·root/하체고정이 통과했다. **초기 지지는 실패**했다: neutral 최대111.790mm/19.486°, 작은 움직임113.778mm/19.888° 기타 이탈. 다음은 초기 실제 관절각과지지 PD 목표의 별도 교정, 이어 실제 음악/안전/종료 신호 연결이다.548은최종음악입력D가아니고 reward/PPO/GPUvectorreset은 미완료다. [native 이미지와4개영상·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/README.md:1).


### Fret와 Strike를 모두 연결하는 최종 환경

사용자 추가 요구에 따라 최종 환경은 **압현+타현+기타 안정화**를 함께 수행한다. 하나의 자유 기타와 humanoid 장면에서 두 과제가 같은 score clock을 사용하고, 상체81 최종 PD 목표의 단일 소유권을 유지한다. 인정 crossing 시각의 실제 압현/sounding fret까지 함께 평가한다. 기존 두 checkpoint를 동시에 실행하는 동결 비교도 포함하되 한 제출자로 통합한다.

[필수 범위·관측·제어·구현 순서](/home/ajou/yigyu/3/stability_adapter_2/DUAL_MUSIC_CONNECTION_SCOPE_V1.md:13). 같은 곡02_Jazz1-200-B_solo의 canonical42event/60Hz 데이터 검증은 통과했지만 현재548D 물리 기본층에 음악 runtime나두checkpoint가 연결된 것은 아니다. 초기 지지 PD 목표 보정, 공동 음악 clock/목표/detector/ledger, 음악 horizon을 구현한 뒤 실제 양손 시험을 한다. [이번 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_connection_scope_v1/README.md:1).


### 양손 연결 runtime 구현 — 2026-10-12

[run_dual_music_v4.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v4.py:26)에서 같은 자유 기타/고정root·하체/스트랩OFF 장면에 Fret035000과 Strike010000을 동시에 연결했다. 원본 두정책은각30채널목표만요청하고 owner가81 최종목표를한번제출한다. PREP2초 뒤 같은score frame을사용하며 독립240Hz 압현/sounding fret/pick 진단과1299 후보관측을기록한다.

초기 실제상태를유지한 정적 지지목표 보정1.0에서5초 기타최대이동111.790→46.306mm/최대회전19.486→9.179°로줄고 core 위치상자 초과0/301표본이었다. 그러나 두checkpoint를활성화하자 기타는최대403.605mm/63.992°움직였고3.85초에Fret 손목의기타-local X 위치안전조건으로종료했다. 공동4event 성공0이며 곡완주/안정화성공이아니다.

12CPU 반례·새native3회/3324step·초기상태exact·목표/rate/시계/금지호출 검사를확인했다. sourcehistoryFret 역변환clip 오차와COM속도ABI상속한계를공개하며 공동판정은subframe 압현인증이아닌보수적bracket 진단이다. 최종공동81/512→256 정책·reward v4/ledger/PPO는후속이며 학습0이다. [초기값·비교그림·실패전체영상·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:1).


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


### GPU 재확인과 정오 마감 시험 학습 — 2026-10-12

GPU 드라이버580.178.04/RTX4070Ti12GB는 정상이며,격리실행의장치접근불가를드라이버고장으로해석한설명을정정한다. CUDA실제연산과독립GPUPhysX검사를통과했고사용자재설치/재부팅은필요없다. 이번native는기존CPUPhysX를유지하고정책/PPO만CUDA로실행한다.

등록된Fret035000·Strike010000은동결해실제로목표를요청하며820D관측/81D상체정책/512→256 Actor·Critic/단일PD owner를사용한다. 실제1PPO갱신256transition과두전체평가(각16.3667초/3928physics/42event/성공0) 검증을완료했다. 한회갱신은품질개선증거가아니다.이번은명시적deadline_pilot이며정식rewardv4/v5 인증이아니다.

[실행과한계](/home/ajou/yigyu/3/stability_adapter_2/DEADLINE_EXECUTION_V3.md:1) · [이미지·4영상·비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/artifacts_smoke_v2/README.md:1).30분간격저장/전체평가및11:40이후새제어진입차단을구현했으며,장기실제실행상태는[진행로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/live_progress.jsonl:1)에서확인한다. native 입력closure가읽는동안main4를변경하지않는다.


### 기타 이탈 대응과 스트랩 비교 계획 — 2026-10-12

무스트랩 평가의 위치 허용범위 이탈은 약84.6–84.7%, 최장 약12.8초였다. long_run_v3는9PPO갱신/2304transition 뒤 관절상태 안전검사로 중단됐으며 입력SHA와 기존 체크포인트·영상은 보존했다. 기존 보고서에 실패관절의 수치가 없어 정확 원인은 새 진단에서 구분한다.

원본 스트랩 길이1.1018469719600776m를 고정한ON/OFF825관측 비교, 유한 관절속도 초과 시 실제 earlytermination/reset과 할인된 안전실패 비용,820정책의 검증된825warm start를 새버전으로 구현한다. 새Adam/ABI이며 exactresume나 정식rewardv4/v5 인증으로 설명하지 않는다. [소단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STRAP_FALLBACK_TRAINING_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/`에 저장한다. 이후 실제 실행상태는 별도progress로 추가하고 native 입력이 읽히는 동안 이 main문서를 수정하지 않는다.


### 기타 안정성 비중 강화 학습 — 2026-10-12

사용자 요청으로 위치 이탈 초당 계수−2→−8, 회전 upper proxy 계수−1→−4로 각각4배 강화한다. 범위 내 비용0/음악 항/상체81/원본 스트랩 ON·OFF/실제 초기값은 유지한다. floor는−8, 안전 tail은 같은 하한으로 정산한다. 이전825 Actor·RMS만 상속하고 새 Critic·Adam으로 시작하며 보상 ABI를 분리한다. [새 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_PRIORITY_TRAINING_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/`에 저장한다. 이전 ON 프로세스 종료 원인은 미확인으로 기록하고, 저장된ON92/OFF127에서 전환한다. 아직 실행/안정화 성공을 의미하지 않는다.


### 학습 갱신 폭과 안정화 보정 수정 — 2026-10-12

직전 ON54갱신/완료35에피소드가 모두 유한 관절속도 안전 종료됐고, OFF40갱신/완료11에피소드는 완주했으나 공동 음악 성공0이다. 첫 optimizer step와 후속 RMS 변화가 최종 정책 KL 검사를 벗어나는 문제를 분석했다. 새버전은 전체 rollout analytic KL 후보 승인/모델·Adam rollback, RMS 고정, 학습률3e−5, 부위별 작은 radian residual와 평균0 Actor로 시험한다. 원본 스트랩·두 baseline·초기 물리·안전 검사는 유지한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_UPDATE_CORRECTION_V1.md:1) · [원자료 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/previous_analysis_v1.json:1). CPU v1의 Adam 복원 alias 실패는 보존하고 v2의6검사 통과 후 별도 검수와 실제 영상으로 검증한다. 실행 중 A/main4를 변경하지 않는다. 아직 품질 개선을 선언하지 않는다.


갱신 전 원자료 재대조: 직전 OFF의 완료11회는 **완주8회·관절속도 안전 종료3회**다. 앞 기록의11회 완주 표현을 정정한다. ON 완료35회 안전 종료는 동일하다. 최종 구현은 guarded PPO v3/CPU7검사 통과 버전이며 비유한 후보·KL 계산 예외도 모델/Adam 복원 후 거절한다. [정정 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_UPDATE_CORRECTION_V2.md:1). 기존 문서·실행 증거는 보존한다.


### 팔·왼엄지 baseline 기준 목표 제한 시험 — 2026-10-12

직전 actual CUDA3갱신에서KL/RMS계약을확인하고세16.3667초평가를안전중단없이완료했지만위치범위밖84.6–86.0%·음악0이남았다. 팔 baseline nominal의preload대비최대2.716rad 이탈은±.3residual로상쇄할수없는요청공간문제를보였다. 새버전은팔nominal±.15/왼엄지nominal±.10rad를resetpreload기준으로제한하고상체81residual/다른fingerprior/원본물리/기타안정성보상/두baseline추론을유지한다. 이는원본행동재현이나실제손위치고정이아니다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_SUPPORT_NOMINAL_V1.md:1) · [직전영상·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/README.md:1). 사전검수와실제1갱신·초기/갱신전체영상을검증한뒤장기학습을이어간다.


## 2026-10-12 지지 nominal readiness 재시도 v2

초기 평가는 full horizon 완료했지만 새 profile 검사 불일치로 학습이 갱신 전에 중단됐다. 종료 상태 문제는 아니며 실패 기록은 보존한다. 물리·제어·보상은 유지하고 readiness만 수정한 [재시도 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_SUPPORT_NOMINAL_V2.md:1)에 따라 새 runner v8 / smoke_on_v2에서 검증한다.


## 2026-10-12 학습 그래픽 분리

long_on_v1의 EGL SIGSEGV(-11) 뒤 long_on_v2의 CP241 전체 평가를 완료하고 원본을 보존했다. 학습 graphics−1/별도 영상 평가 graphics0과 5분 복구 저장을 새 버전으로 검증한다. 물리·제어·보상과 기존 checkpoint 수치는 유지하며, 코드 ABI의 추가6소스만 허용하는 명시적 이행이다. [계획](/home/ajou/yigyu/3/stability_adapter_2/GRAPHICS_ISOLATION_PLAN_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/`에 저장한다. 아직 재발 방지·학습 재개를 검증한 상태는 아니다. native 실행 동안 A/main 문서를 다시 동결한다.


## 2026-10-12 그래픽 분리 실제 검증 완료

CPU9검사, graphics−1 60회 초기화와CP241의16.3667초 결정론적전체궤적/controls exact비교, CUDA1갱신(CP241→242/256transition),초기·갱신전체평가4영상을완료했다. checkpoint model/Adam/RMS/RNG/counters 이행은 exact이며 정책KL .01990470476448536≤.02/RMS고정을확인했다. physics/PD/81제어/두baseline/원본strap 계약은유지한다. 첫probe의진단JSON을학습ABI에넣은오류는이행단계에서거절됐고원본을보존했으며,새D 진단v2에서입력을분리해통과했다. [실제검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/verification_v1.json:1) · [결과설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/README.md:1).

CP242는음악0/42·위치box밖46.64%/최대47.11cm여서학습품질개선·기타안정화성공이아니다. 기존CP86/241대비일관된개선은없다. 오류예방검증과성능평가를구분한다. 검증된CP242에서같은학습조건으로재개하고,5분복구checkpoint 실제생성과30분공식영상/11:40cutoff를확인한다. 새 supervisor는완료/부분종료가구분되는 실제영상을 `/home/ajou/yigyu/3/docs/2026-10-12/video/graphics_long_v1/`에 자동복사·SHA검사한다. native 실행동안A/main을다시동결한다.


## 2026-10-12 병렬 환경 수집 전환

사용자 요청으로 독립 spawn CPU 물리환경4개와 CUDA batched정책 추론을 구현한다. 초기 관절/기타/스트랩 무작위화는0이며 행동Gaussian탐색만유지한다. 기존single환경의마지막복구CP315/80640transition과종료전로그319회까지보존했으며미저장316–319는이행하지않는다. 기존source/asset/물리·제어·보상/Adam/RMS/RNG/counters를유지하고새6소스만허용하는ABI이행이다. CPU7검사를통과했으며 N2의독립5초물리→N4/T64(256transition)CUDA1갱신·전체영상→N4/T256(1024transition)학습으로검증한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/PARALLEL_COLLECTION_PLAN_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/`에저장한다. 아직실제병렬학습과속도개선을인증하지않는다. native실행동안A/main을다시동결한다.


## 2026-10-12 병렬 수집 실제 검증 완료

CPU7검사,N2각5초/1200physics의초기nativeexact·서로다른행동에실제q차·금지0·원본strap호출검증,N4/T64(256transition)CUDA1갱신과초기/갱신full영상을완료했다. model/Adam/RMS/RNG/counter이행exact,기존물리·제어ABI/기존소스SHA유지,정책KL .019905004650354385≤.02/RMS고정이다. 실제GPU정책배치4,수집4.4516초/57.5069transition/s는이번PREP배치측정이며기존PLAY평균에대한속도향상인증이아니다. [실제검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/verification_v1.json:1).

검증CP316에서N4/T256=1024transition/갱신으로이어간다. 미니배치128·에폭4는최대32미니배치갱신기회이며각기회에서guard가최대8번재시도하므로optimizer.step시도횟수상한32로해석하지않는다. 초기물리노이즈0/행동Gaussian탐색만유지하며실제latent std는몸통·머리약.006738/팔·손가락약.018315(각도아님)이다. 5분복구·30분공식영상·11:40cutoff를유지하고완료/부분영상은 `/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/`에자동보관한다. 아직N4/T256생산학습속도나음악성공을인증하지않는다. native동안A/main동결.


## 2026-10-12 병렬 학습 정오 실행 완료

N4/T256의실제4갱신/4096transition을완료해CP320/84992를저장했다. 수집·최적화합산평균36.5024transition/s이며서로다른checkpoint/배치의기존single참고값14.8839/s와조건통제된benchmark로해석하지않는다. 상체81/825관측/512→256/기존PPO설정·RMS·물리·PD·원본strap·baseline·초기노이즈0를유지했다.11:40협조적cutoff후최종16.3667초평가/16.4초영상까지완료하고프로세스종료코드0/보관오류0/원본SHA불변을확인했다. [완료검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/completion_verification_v1.json:1).

검증/생산대표평가4회·8전체영상은 `/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/` 및 `/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/`에보존했다. 최종음악0/42며초기CP316대비최종CP320밖비율59.78→55.19%/maxinitialSO393.93→91.21°는줄었지만최대rootbox이탈30.45→33.99cm/평균5.82→8.49cm는커져일관된기타안정화성공은아니다. 처리량구현검증과성능검증을구분한다. [초기노이즈분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/initial_noise_analysis_v1.json:1). 이후새run에서이검증entry를재사용하되정오deadline·sourceABI·대표영상타임아웃을새운영기간에맞추는새버전계획이필요하다.


## 2026-10-12 기타·양손 연동 초기 노이즈

사용자 요청으로 기타 actor-root x/y±5mm,z0–5mm,world rotvec성분±1°의 작은 초기배치를 시험한다. 양팔24관절만±.15rad IK로기타기준palm위치·방향을유지하고손가락/body/head/root·하체/원본strap을유지한다. source겹침→fresh native검증통과bank를seeded discrete sampling하며연속균일노이즈로설명하지않는다. 기존preload보정은원기준correction+새q_ref로더해IK delta가두번들어가지않게한다. 새초기분포ABI와CP320 model/RMS warm start를사용하고Adam/counters는새로시작한다. reset생성중1회초기state제출만허용하며제어중덮어쓰기는금지한다. [소단계계획](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_NOISE_PLAN_V1.md:1). 결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1 에저장한다. 아직실제native noisy reset/연주성공을검증하지않았다. native중main4동결.


## 2026-10-12 기타·양손 연동 초기 노이즈 검증 완료

- [x] CPU4검사와사전독립검수,신규구현·원본보존.
- [x] 32제안중절대회전허용집합밖27개거절,기준1+노이즈4 source/native검사통과. 실제손바닥최대초기오차0.000171737mm/팔변화최대1.24364°/body·head·finger 초기q불변.
- [x] 2worker×3 freshreset선택[[2,3],[1,4],[0,1]]·constantABI·실제선택reference전체nativeexact.
- [x] CP320 model/RMSexact warm start+freshAdam/counter0으로4환경CUDA1갱신/256transition/승인optimizer4/KL.01961852≤.02/RMS고정. exactphysical/RNGresume나장기학습성공으로설명하지않는다.
- [x] 고정index1/4의두전체평가:각16.366667physics초/3928physics/982controls/스트랩51064/금지0/안전중단없음/음악0/42,전신·손총4영상492frame16.4MP4초보관.

IK는reset생성때1회뿐이며2초PREP중에도기존PD+안정화정책이제어하고그뒤fret/strike baseline연주목표에진입한다. sampling은검증된5개bank의uniform discrete replacement이며전체노이즈범위의연속uniform분포가아니다. 기존source/assets/실패·결과보존,root·하체고정/상체81/자유기타/원본strap길이유지. bodycenter가아닌고정world actor-rootbox진단의최대후기이탈45.74/40.49cm·자기초기대비SO3최대94.01/89.72°가남아안정화·연주성공은미완료다. 두평가selection.sampling문자열은일반bank모드를기록하는v1한계이며실제고정선택은attempt.evaluation_index를우선한다. 미래버전에서개별selection_method를분리한다.

[전체검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/verification_v1.json:1) · [실제초기값·노이즈후보](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/bank_build_v1/bank.json:1) · [이미지·영상설명정정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/artifacts_v1/README_V2.md:1) · [영상색인V10](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V10.md:1) · [변경실제줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/CHANGED_FILES_V1.md:1).


## 2026-10-12 연주 없는 상체·오른상완 초기 지지 비교

사용자 요청으로 Fret/Strike/학습/안정화정책/초기노이즈를실행하지않고현기준과Chest전체전경변화0/3/5°의상완지지후보를5초비교한다. 기타초기p/q·root/하체·손가락·원본strapON길이/gain/solver를유지한다. 왼손palmworldpose를초기IK로유지하며오른상완capsule을바디상단의양의source간격0.5–1.5mm에배치한다. 초기q_ref자체를fixedPDtarget으로유지하고preload/PI/feedbackIK도추가하지않는다. 실제관절상태는물리에맡기며기타/손부착·지속state쓰기금지. [신규계획](/home/ajou/yigyu/3/stability_adapter_2/UPPER_ARM_STATIC_SUPPORT_PLAN_V1.md:1). 결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1 에저장한다. CPU3검사통과,정적source→fresh native배치→5초영상순서로검증하며아직안정화성공을확인하지않았다. source범위는실제cookedcontact/힘인증이아니다. native중main4동결.


## 2026-10-12 연주 없는 초기 자세 비교 완료

- [x] 초기 자세만 바꾼 기준/상완 접근0°/Chest 전경3°/5°의 Isaac Gym 5초 시험 네 개 완료. 각1200 physics·300 control·151영상frame, CPU3검사 및 실행32+동일조건8검사 통과. Fret/Strike·체크포인트·안정화정책·학습·초기노이즈·preload/PI/실시간IK 호출0. 초기q_ref를5초내내fixed PD목표로 제출했고 기타/root·고정하체/원본strap길이·법칙/gain/solver를 유지했다. 기타·손 고정 및 제어 중 state 덮어쓰기0.
- [x] 초기→5초 actor-root 이동/회전은 기준11.28cm/19.63°,0°10.05cm/15.96°,3°10.59cm/17.41°,5°10.78cm/18.34°. 3°의2→5초 변화는0.062mm/0.0168°로가장작지만 초기자세유지성공은아니다. 기준도후기에작게움직였으며전경량이커질수록좋아지는결과는아니다. 바디중심자연허용범위평가와구분한다.
- [x] 실제주된오른팔접촉은전완R_Elbow였다. 상완R_Shoulder접촉은5°의0.4333–1.3333초55/300시점에만관측,Chest/Torso/Spine접촉은모두0. 겨드랑이로지속지지한결과가아니다. 접촉rawλ와스트랩호출수를N단위지지력으로해석하지않는다.
- [x] prep=horizon인v1준비오류를native전에검수해원본보존후v2설정으로실행. 요청gap0.5mm와source-FK 예측간격을구분하며PhysX cooked최단간격으로부르지않는다.

[결과·이미지·대표영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/README.md:1) · [이미지상세설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/README.md:1) · [8영상모음](/home/ajou/yigyu/3/docs/2026-10-12/video/upper_arm_static_support_v1/README.md:1) · [변경실제줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/CHANGED_FILES_V2.md:1).

다음에는연주없이초기접촉위치를개선하는소단계를계획한다. 상완capsule끝점만맞추는목표를기타바디표면범위와실제접촉위치에맞추고상완·전완을함께검사하여초기낙하전부터지지가형성되는지확인한다. 이는미실행후속제안이다. 기존결과·소스·원본모델은보존한다.


## 2026-10-12 척추 분산 굽힘·왼손 없는 초기 유지

사용자 요청으로 척추를 더 둥글게 만든 초기 자세를 시험한다. Torso/Spine/Chest 구간에 전체전경9°/12°를25%/62.5%/100% 누적으로 분산하며 각몸통scalar는원기준±5°/모델한계 내다. 처음부터왼손을위8cm·뒤3cm 빼는조건과9°왼손지지조건을비교한다. 실제시간release가아니며왼손없음과strap없음을구분한다. 원본strapON·길이법칙/기타초기p/q/root고정하체/gain/solver/머리손가락초기각을유지,상수초기q_ref PD목표를5초제출한다. no음악/CP/학습/정책/추가힘/실시간IK/state덮어쓰기. 오른팔±.3rad,왼팔withdraw진단±.6rad. source/native접촉·실제5초영상으로판정하며아직유지성공을확인하지않았다. [소단계계획](/home/ajou/yigyu/3/stability_adapter_2/ROUNDED_SPINE_NO_LEFT_PLAN_V1.md:1). 결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1 에저장하고기존소비소스/산출물은보존한다. native중main4동결.


### 척추 분산 굽힘: 왼손 철수 방향 v2

v1의위8cm·뒤3cm철수는palm/넥source관통으로거절했고native0이다. 원본검색과계획을보존한새v2에서앞8cm·아래3cm로바꿨고3°비지지/9°지지/9°비지지/12°비지지네후보가source FK·한계·겹침검사를통과했다. [정정계획](/home/ajou/yigyu/3/stability_adapter_2/ROUNDED_SPINE_NO_LEFT_PLAN_V2.md:1). 아직실제왼팔비접촉/기타유지를인증하지않으며native5초4조건을검증한다. 나머지물리·제어조건동일,기존소비소스보존. native중main4동결.


## 2026-10-12 척추 분산 굽힘·왼손 없는 초기 유지 비교 완료

- [x] v1위/뒤철수의source관통3개를거절해보존하고v2앞8cm·아래3cm철수네후보source통과. 사전독립검수후실제Isaac Gym5초4조건완료,각1200physics/300controls/151frames,33개실행·입력·영상·동일조건검사통과. 음악/CP/정책/학습/초기노이즈/금지state쓰기0,초기q_ref fixedPD·root고정하체·원본strapON길이법칙/기타초기p/q/PD·solver유지.
- [x] 초기→5초actor-root이동/SO3:3°왼손철수36.24cm/88.16°,9°왼손지지10.84cm/18.97°,9°철수33.54cm/83.31°,12°철수33.29cm/83.41°. 세철수조건의모든왼팔/LH기타접촉0/300query.9°지지/철수는왼팔이외초기목표exact같다. 굽힘만으로왼손없는기타유지에실패했고후기정착을초기유지성공으로해석하지않는다. 위치는bodycenter아닌actor-root진단이다.
- [x]9°왼손지지의R_Shoulder284/300접촉이철수세조건에서는모두0이다. R_Elbow철수0/4/6,Chest/Spine모두0·9°철수Torso일시1query. 더굽히는양만늘리기보다실제바디의상완/전완/몸통지지배치를다시설계해야한다.0query는60Hz측정범위이며연속240Hz비접촉인증이아니다. sourcegap/rawλ는cooked최단거리/N힘으로부르지않는다.

[결과설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README.md:1) · [실제검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/verification_v1.json:1) · [변경실제줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/CHANGED_FILES_V1.md:1).

다음소단계는관통없이기타바디가오른팔과몸통/허벅지접촉에둘러싸이는초기배치를찾는것이다. 필요시기타초기위치의소폭변경도새계획에서구분하며현재4조건의실행결과와혼동하지않는다. 이번시험은시작부터왼손을뺀조건이고실제시간release/strapOFF시험은아니다. 모든기존소비소스/결과보존.


### 척추/왼손철수 결과의 오른손목·손 접촉 보완

전체오른쪽접촉을추가대조했다.3°철수의RH:palm244/300·RH:thumb1 245/300,9°철수의R_Wrist242/300·RH:palm240/300,12°철수의R_Wrist241/300·RH:palm1/300 접촉이남아있다. 따라서root첫README의‘지속오른팔·몸통지지없음’이라는넓은표현을‘지속상완·전완·몸통지지가형성되지않음’으로좁혀정정한다. 접촉존재만으로부위별지지력기여를결정하지않는다. 초기33–36cm/83–88°이탈과왼팔/손query0·기타초기유지실패결론은변하지않는다. 기타가크게돌아간뒤손목/손에닿은상태를원하는연주자세유지로해석하지않는다. 기존문서/소스/원자료를보존한 [권위결과정정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README_V2.md:1) · [오른손목/손 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/right_hand_contact_audit_v1.json:1) · [이미지·영상설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/README.md:1) · [영상8개](/home/ajou/yigyu/3/docs/2026-10-12/video/rounded_spine_no_left_v1/README.md:1). 새로운물리실행은추가하지않았다.


## 2026-10-12 휴머노이드 기준 현실적인 기타 비율

사용자 요청으로 휴머노이드 중립 source 높이·기존 현 marker 길이를 측정하고 Yamaha FS800 공식 치수를 참고한 콘서트형 바디/두께·headstock 연장의 별도 자산을 만든다. 넥·프렛·현 좌표와 body 이름/순서를 유지한다. 상·하 bout convex mesh 두 개로 허리를 유지하며 시각/충돌을 맞춘다. 원본 자산·기존 소비 소스/실험은 보존한다. 초기각/배치만으로 기타 유지에 실패한 기존 결과와 구분한다. 원본 길이·법칙의strapON을 유지하되 버튼은 새 바디 측면/끝면에 맞춰 route 변화를 기록한다. native 각body 질량은 원본과 맞추고 새 imported COM·관성을 초기화 전 적용/측정한다. 먼저 source·ABI 검증과 기존5초native 기준을 기록한 뒤 새형상 관통없는배치·5초native/전신손영상을검증한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/REALISTIC_GUITAR_PROPORTIONS_PLAN_V1.md:1). 결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1 에 저장한다. 음악·학습을 연결하지 않으며 안정화/실물 물리 정확성을 아직 인증하지 않는다. native중main4동결.


### 기타 비율 모델의 native 물성 검증 보완 v2

source기하8검사와첫관통없는배치front35/up80을검증했다. 휴먼중립source높이172.05cm,새바디길이48.79/폭37.30/두께8.84–10.80cm·전체100.23cm다. 실제FS800사양을현marker평균길이에맞춘연구용비율/윤곽근사이며제품정밀복제나실물물성인증이아니다. native전사전검수에서COM/I전체readback과런타임propertysetter금지검사를보완한새v2 runner/guard를준비했고CPUguard4검사를통과했다. v1runner는native未실행·원본보존. [보완계획](/home/ajou/yigyu/3/stability_adapter_2/REALISTIC_GUITAR_PROPORTIONS_PLAN_V2.md:1). 원본/새모델5초영상과실제mass/COM/I/cache·source/충돌렌더를검증하며아직native완료/안정화성공을인증하지않는다. native중main4동결.


## 2026-10-12 휴머노이드 기준 기타 비율 새 모델 검증 완료

- [x] 휴먼중립source높이172.05cm·기존현길이에맞춘FS800공식치수참고:새바디L48.7896/W37.3039/depth8.8351–10.7985cm·전체100.2298cm. 상·하convexbouts로허리유지,headstock연장,각부분render/collision같은mesh. 기존body이름/순서/원점·넥/프렛/현좌표CPU및nativeABI검사통과. 제품정밀복제/실측사람키인증아님.
- [x] CPU기하8검사+propertyguard4검사/독립사전검수,두actualnative각5초1200physics300controls151frames완료. 원본/새모델totalM4.6487157kg·각bodymass같음,newimportCOM/I×massratio/전체readback/cache/초기setter0/1·실행중setter금지검증. 음악/CP/정책/학습/초기노이즈/state덮어쓰기0·기타자유/root고정하체·PDsolver/body9초기각/머리손가락유지.
- [x] 새기타는초기앞3.5cm/위8cm·팔24IK±.6으로source/native초기관통없음. strap길이/법칙은원본이고버튼은새바디측면/끝면에맞춰route가다르다. 초기→5초actorroot13.192cm/SO310.013°·후기0.017267mm/.003439°,새bodyenvelopecenter이동10.2077cm. 새R_Hip290query·LH손가락접촉이나상완/전완/Chest0이다. 비율/형상초기구현검증이며겨드랑이/왼손없는유지·음악성공인증아님;초기배치/route도바뀌어서형상만의효과로해석하지않는다.
- [x] manifest평균depth center필드의이름을실제bboxcenter와구분하는companion정정(v2audit/v3분석)을보존형태로추가했다. 실제bboxcenterG[0,-.4,-.05569252]m,legacyorigin/중간깊이참조/nativebodyCOM과다르다. 물리재실행0.25개실행검사와추가nativeABI/I스케일검사통과. 실물중공목재중량/COM/마찰·checkpoint성능은별도미검증.

[새모델](/home/ajou/yigyu/3/stability_adapter_2/assets/realistic_guitar_v1/guitar_asset.xml:1) · [결과와정정범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/README.md:1) · [비교이미지설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/README.md:1) · [전신·손4영상](/home/ajou/yigyu/3/docs/2026-10-12/video/realistic_guitar_proportions_v1/README.md:1) · [변경실제줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/CHANGED_FILES_V1.md:1).

공용원본/학습기본환경은변경하지않았다. 새자산은별도runner에서만실행검증했다. 다음에는새바디기준허벅지/상완/전완접촉배치를다시찾고실제무게/질량분포가필요하면독립물성단계로측정한다. checkpoint연결전원래고정기타기준성능과기하이전영향을다시확인한다. 기존기록·소스·자산보존.


## 현실 비율 기타 그림 정정본 — 2026-10-12

원본과 새 기타의 t0 시각/충돌 비교 및 실제 cm 축척 윤곽 비교는 [정정 그림 문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/README.md:1)를 사용한다. v1의 일부 그림은 상대 축척·패널 배치가 부정확해 보존한 채 v2로 정정했다. 이번 정정은 후처리이며 물리 재실행·영상 재복사는 없다. 크기 변경의 실제 물리 비교와 한계는 [결과 문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/README.md:1)에 기록했다.
