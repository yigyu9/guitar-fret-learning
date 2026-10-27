# 초기 자세 탐색 V1 사전 검수

요약 판정: **문제없음 — 코드·제어·입력 계약 기준**. Critical 0건, Warning 0건. 단, V1에서 만들어진 source 후보는 실제 형상 gate를 통과하지 못했고 native 실행 대상이 아니다. V1 source 탐색은 partial 상태로 중단·보존했으며 native 실행0회다. 후보 성공을 의미하지 않는다.

- [source V1](/home/ajou/yigyu/3/stability_adapter_2/search_initial_pose_v1.py:28)은 기존 near native 초기의 q/G에서 모든 후보에 같은 G좌표 A wrist anchor와 상대회전을 사용한다. 초기 목표는 anchor+0.15×[.070,.080,0]m다. [runner V1](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v1.py:113)의 초기 trajectory fraction과125줄의 명시 anchor/rotation이 이 기준과 일치한다. 이전 cold14초에서 A가42mm 바뀐 비교 혼란을 반복하지 않는다.
- Source는 일반팔1°·Thorax_y/z2°·L_Wrist_y5° margin을 주며 고정head/finger48각을 보호한다. Chest±3°·R_Shoulder±7°·G각축10mm·roll±2°·Torso_z±2°의7가지 고정 탐색 범위다. 원래 body 각과 이 범위는 현재 모델 한계 안이다. 손바닥 normal_up>0·source 자체교차·G/human 교차·지정 지지 gap·손목2mm/.02rad·EW 이산 도달 gate를 둔다. source/capsule 검사를 cooked 연속경로 인증과 구별한다.
- 보존된 source before1,306개 입력은 검수 당시 현재 SHA와 모두 같았다. 실제 humanoid/G XML·모든 compiler.meshdir mesh선언 union106개와 geometry manifest, 직접config/candidate/reference/FACETS/helper가 포함된다. 두 신규 Python AST 문법 검사가 통과했다.
- runner는 이전 검증된 qualification V2에서 phase/계획/report 경로와 왼손 anchor/rotation/fraction만 바꿨다.3개1280×720 기록 카메라와 보조 OM_appearance1280×960, 원래 유한 human PD/task·root/하체 guard·상태 보존·effort cap·target rate·actor-root20cm/SO335°·속도50rad/s 중단을 유지한다. 기타 고정/외력/부착/지속 pose 수정 경로를 추가하지 않는다. 새 native 초기 FK·각/속도·sourceclear 검증은 실행 시에도 필요하다.
- 실제 조회한 partial audit4개는 margin_only/roll_m2/roll_p2/torso_m2다. 모두 기타source 교차는 없으나 L_Shoulder–Torso(일부Spine) source 자체교차로 탈락했다. support gap이나 wrist 오차만 맞춘 것을 적합 후보로 승격하지 않았다. [interrupted.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v1/interrupted.json:1)은 source-only/native0과 원본 보존을 명시한다. 형상 회피 보완은 별도V2 소스로 진행한다.

검수자는 이 보고서만 작성했다. 기존 source/결과·공용 자산·다른 담당자의 파일은 수정하지 않았다. V2 자체교차 회피 수학/입력 범위는 별도 새 보고서로 검수한다.

검수 시점 SHA256:

- `/home/ajou/yigyu/3/stability_adapter_2/search_initial_pose_v1.py`: `915ad18bc5a835947b5cc05288d96095e1253859c6af2071cff6517192b2d32e`
- `/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v1.py`: `f01b3c98559c6a22c5252b43b5455f0af87b0fd83fea6e4460e55cd2f6e61b94`
- `/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_PLAN_V1.md`: `5d0c98c3580e02bf1f518dac5aaef9f6b87788d84d1ad1797cd7528b04b12b14`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v1/inputs_before.json`: `35253a17a8de91edfc7a7cda1eab68772b956565e2223c5d1b58738fe57dbaec`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v1/interrupted.json`: `08205407e292a50f898efe52388d4854de94c2f0eadb9f0516b7347224b00b5b`
