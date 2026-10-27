# 몸통9 PD 유지 강도와 실제 기타 안정성 비교

같은 초기81각·기타 p/q·절대81목표·LA에서 Torso/Spine/Chest9 PD gain만 바꿨다. 최대 기타 이동·회전은 줄었지만 손바닥 지지는 생기지 않았고 엄지/중지 요청면 근접 기록은 줄었다. 새gain을 세면grip/연주 안정화 성공으로 채택하지 않는다. 후속 지지 제어를 위한 임시 진단 후보로 보존한다.

## 변경 조건과 초기값

몸통9 stiffness600→1200, damping150→float32(150×√2)=212.1320343017578이다. 나머지72 관절의 PD properties, effort cap·driveMode·initialq/target·기타목표·물성·solver는 같다. 몸통9 effortcap300Nm도 유지했다. Damping비율은 scalar heuristic이며 critical damping 인증이 아니다.

[실제81 초기값·body9 변경 전후 properties](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/initial_values.json), [변경없는 입력 trial](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json:1), [실행계약](/home/ajou/yigyu/3/stability_adapter_2/TORSO_HOLD_EXECUTION.md:1)에 기록한다. LA1.1018469719600776m·초기route1.0858332748277348m·여유16.013697mm, 기타 초기p/q와81 초기native state는 직전과exact같다. 처음PD target은actual초기각이고 첫60Hz제출부터기존절대81목표를사용하는 기존 동작을 유지했다.

Root/하체는 전용asset에서 물리고정이고 몸통9 목표는 유지하되 실제 움직인다. 양쪽Thorax 이하66 주요제어/selfcollisionON·자유기타/gravity/contact/passive strap 조건은 같다. 손 강제부착·기타고정·기타목표힘·지속state overwrite는 없다.

## 일반 카메라와 collision 카메라의 초기 조회

![일반 실제Gym 초기 손/스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/initial_collision/frames/hands/00000.png)

![collision geometry 요청 카메라의 초기 손/스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/initial_collision/hands_collision.png)

동일시점·동일camera view/projection의native 이미지다. Raw RGB 두이미지는exact같았다. use_collision_geometry=true를 요청했어도 이결과만으로 별도의 PhysX cooked mesh를 식별했거나 gap/관통을 인증했다고 볼 수 없다. Root가 실제 rawPNG를 다시 열어확인했다. 최초black화면 해석은 틀렸으며 숫자/출력을 보존한 camera_observation_v2.json에서정정했다.

[활성shape/body/filter/물성 조회](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/initial_collision/shape_properties.json)는 human55/guitar28로과거readback와actor단위exact같다. LH:palm은shape18 한개, filter128이고 guitar 본체shape0/1 filter4096과mask충돌을허용한다. 두shape의 contact_offset은약0.1mm·rest_offset0·friction1이다. Proxy 제외와연결/같은손 importer정책은유지했다. 초기source palm유한패치간격0.421670mm는positivegap이지만native최단간격/지지판정과같지않다.

이초기조회는별도native초기화1회/physics0이다. Query/render 후human/guitarstate·PD·Python target은exact같다. 실제5초시험과집계를분리한다. Camera v1은문법검사만했고 API가None을반환함을공식로컬문서로확인해실행전보존후v2로수정했다. 초기camera actual은v2 한회뿐이다.

## 실제0~5초 스트랩 영상

![몸통9 PD×2 실제Gym 전신0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/whole_body.mp4)

![몸통9 PD×2 실제Gym 손0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/hands.mp4)

한actual5초·1200step/240Hz,두영상각151frame/30fps·인코딩5.033333초다. 주황실선은depth기준보이는13route지점/12구간,옅은점선은가려진구간이다. 픽셀선은천너비/처짐/추가충돌mesh가아니다. RawnativePNG와route/camera/SHA도보존했다. CPU PhysX이며CUDA/context/visualgeom 경고는로그에남겼다.

![종료5초 손과스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/frames/hands/00150.png)

손바닥이넥요청옆면에지지된것으로보면안된다. 이번SDK에는palm body contact자체가없었다.

## 기타오차와 몸통실제이동

| 조건 | 최대이동 | 최대회전 | 종료이동 | 종료회전 | 몸통최대DOF변화 |
|---|---:|---:|---:|---:|---:|
| 저장 body9×1 |26.091583mm|7.937143°|22.095629mm|7.117855°|4.231250°|
| 새 body9×2 |14.052228mm|2.884291°|14.050564mm|2.856298°|3.536898°|

![실제world 기타오차와몸통9 좌표변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/artifacts_v2/G_and_body9_comparison.png)

파랑은직전저장5초,주황은이번새5초다. 아래값은매시점몸통9 DOF절대변화의최댓값이며bone SO(3)회전각이아니다. 최대값은줄었지만첫0.1초에는몸통0.989530→1.265931°·기타이동5.053658→5.107730mm로조금커졌다. 모든시점개선을주장하지않는다. 감소율/재현성/정식성공기준을임의확정하지않는다.

![source손바닥간격과요청patch근접 SDK step](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/artifacts_v2/palm_gap_and_patch_features.png)

위source거리10시점은actual저장bodypose로계산한hull–유한patch witness상한/하한이다. 점사이선은연결표시이며연속gap측정/cooked clearancedata가아니다. 초기0.421670mm·0.1초5.239726mm·5초9.102264mm이다. 아래점은rawλ>0·projection내부·법선거리절댓값≤2mm·두localpoint재구성잔차≤1µm를모두만족한SDK행의고유step이다. 빈줄과n=0은접촉이없음을그대로보인다.

| 요청면 근접고유step / last | 저장×1 | 새×2 |
|---|---:|---:|
| 엄지3 후면 |793 /1200|3 /39|
| 검지3 전면 |34 /116|1129 /1200|
| 중지3 전면 |1052 /1200|12 /41|
| 손바닥 옆면 |0 /없음|0 /없음|

SDK원행5526개를검사했다. Thumb body양λ자체는106step/last317이지만후면patch근접은3뿐이므로같지않다. R_Hip 양λ는1200step/last1200이다. Body명/λ/source근접은실제면·해부학적pad·힘N·연속지지·cooked관통인증이아니다. Palm body자체contact0, 양손contact고유step0,상향proxy위반0이다.

Passive strap 법칙최대23.840134N/종료1.880517N이며1200step재계산오차0이다. Chest/팔sourceanchor변위는축별정확vector합으로검증했고norm은합산하지않는다.0.1초Chest/팔norm15.558831/11.489972mm,5초47.609522/39.302397mm다.

## 검증과 다음 단위

[원자료6검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/analysis.json)·[SDK3검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native_feature_analysis.json)·[early-motion4검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/early_motion_audit.json)·[native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/report.json)을완료했다. Getter/setter와300회목표제출·고정root하체·영상/route·입력SHA를확인했다. 성공한물리실행은반복하지않았다. 그림v1의9개몸통좌표를scalar로읽은오류는source/wrapper/log/metadata를exact보존후v2의max(abs(vector))로수정했고추가physics0이다.

[다음계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_SUPPORT_RESIDUAL_AT_BODY9_PLAN.md:1)은미실행이다. 현재native/FK대조와팔12의palm위치/법선민감도를먼저계산한후,기존81목표+작은palm task residual의제어범위를정한다. 옆면접촉후기타초기p/q복원항과연주66목표의보정관계를확인한뒤학습구조를정한다. WAIT→REACH→GRIP→TRANSPORT를연주필수선행과정으로두지않는다.

Root가실제PNG/원자료/그림·문서를검증했다. Luna/독립change-reviewer 도구threadlimit으로이번산출물은Sol/root가작성하고독립검수는보류한다. [변경파일절대경로·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/CHANGED_FILES.md:1)을따른다. 전체기타초기복원·손지지·연주안정화는계속진행한다.
