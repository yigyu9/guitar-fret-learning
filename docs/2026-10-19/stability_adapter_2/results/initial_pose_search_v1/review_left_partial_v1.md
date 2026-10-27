# 왼손 부분 중단 시험·후처리 경계 검수

요약 판정: **문제없음 — 기록/후처리/측정 해석 기준**. 미해결 Critical 0건, Warning 0건. 검토한 두 후보의 왼손16초 시험은 모두 **실패한 부분 실행**이며 안정화 성공이 아니다. 실행 중인 roll_m2의 결과는 이번 검수 범위 밖이다.

## 안전 중단 프레임 처리

[render_initial_pose_search_v1.py:15](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_search_v1.py:15)는 qualification renderer V2의 count/gap 검사만 현재 runner 순서에 맞게 보완한다. native loop는 `step→sample(안전검사)→조건부capture` 순서라 안전검사가 카메라 tick에서 실패하면 마지막 카메라는 정확히8physics tick 앞일 수 있다. 이전 `floor(N/8)+1`,gap<8은 이 정상적인 부분기록을 잘못 거부한다.

새 검사는 실제 frame step을0..last 매8로 정확히 대조하고 capture와 count/step/상태보존을 맞춘다. partial은0≤gap≤8,완료조건은gap=0이다. 임의 끝프레임을 복제하거나 물리를 재실행하지 않는다. 입력/rawPNG SHA·실제 matrix/world feature·마지막 ‘중단 직전’ 캡션·native_completed=false를 유지한다. 직접helper pin도 유지하며 새 Python AST는 통과했다.

|부분실행|물리끝step/초|마지막camera step/초|gap|실제frame|30fps 표시길이|
|---|---|---|---:|---:|---:|
|margin_only|2392 /9.966667|2384 /9.933333|8tick|299|9.966667초|
|torso_p2|1544 /6.433333|1536 /6.400000|8tick|193|6.433333초|

두 raw contact_frames/capture의 전체step·count·flags를 독립 대조했다. 영상 표시길이가 물리 경과와 우연히 같아도 마지막 실제관측 시점이 물리 끝이라고 할 수 없다.

`visual_torso_p2_left_v1`은 기존 검사 실패 뒤 빈 디렉터리로 보존됐다. 새 `visual_torso_p2_left_v2`의588개 post 입력 SHA가 현재 전부 일치한다. 실제4개 MP4를 ffprobe해 각193frame/30fps/6.433333초, 개별1280×940/합본1920×470을 확인했다. 마지막6.400초3-up PNG도 직접 열어 ‘보호 중단 직전·16초 목표 미완료’ 표시와 전신3시점·기존glyph 의미를 확인했다. margin 새 영상 생성은 이 검수의 실제 출력 확인 범위에 포함하지 않았다.

## 실제 중단 원인·불변식

|조건|최대BB중심mm|최대SO3°|최대actor-root mm|최초20cm초과step|
|---|---:|---:|---:|---:|
|margin_only|112.825130326|29.121506328|205.923375488|2391|
|torso_p2|62.826053265|28.493017084|203.210347907|1543|

초기0초+전체240Hz 기타 상태를 정규화 quaternion과BB local centre로 독립 재계산해 analysis와 일치함을 확인했다. 둘 다 actor-root20cm 이동 한계가 중단 원인이다. 회전35° 미만이므로 회전중단이라고 부르면 안 된다. 계획의동작참고50mm/20°도 넘었고 완주/놓기/양station성공을 입증하지 않는다.

두 native의1,313개 before 입력과각analysis14개 입력은 현재 SHA가 모두 같았다. 실제240Hzcontact step1..N 연속성, 최종81 effort finite/cap/coverage, 목표각model limit/rate, 다른48목표 exact를 독립 확인했다. completed=false와failure guitar safety displacement가 보존되며 다른불변식 통과를 전체성공으로 바꾸지 않는다. 모델·제어gain·기타자유도·실제원자료는 새 renderer가 수정하지 않는다.

## 접촉·구간 해석

- 두 후보 모두 A유지3–4.5초360/360에 **LH:thumb3+LH:index3** 양의접촉이 있다. 모든손가락 지지 또는force closure 인증은 아니다.
- margin_only의openA6–7초는LHfree240/240,Chest양의0,R_Shoulder233,R_Hip232,L_Hip39/240이다. 오른손(RH:middle3)raw접촉97/240도 있다.
- margin_only의moveB7–8.5초는LHfree360/360이고구간기준BB최대2.666746mm/SO3최대1.008939°지만 **오른 RH:middle3도raw접촉360/360**이다. 따라서 양손접촉없는 독립지지라고 해석하면 안 된다. Chest양의0,R_Shoulder/R_Hip360/360이며 인과기여는 미확정이다.
- margin_only는closeB8.5–9.966667초352step까지 진입했고 그중엄지+다른손가락 양의접촉102step을 확인했다. **B유지10–11.5초·B해제·마지막놓기는 미수행**이다. B접근/접촉 자체가 없었다고 표현하는 것도 틀리다.
- torso_p2는6–7초openA를 완주하지 않았다. 실제관측openA6–6.433333초104step에서LHfree104/104,Chest양의15,R_Shoulder86,R_Hip104,L_Hip0,오른손raw접촉18이다. 이를240step전체openA성공으로 바꾸지 않는다. 기존분석기는종료7초미달인openA구간을누락하므로이partial104집계는별도검수계산이다.
- raw접촉free는lambda0행까지 포함한엄격기준,양의접촉은lambda>0기준이다. 행수·지지전환으로force N/압력/원인을단정하지 않는다. 관절실제각/속도의기존analysis최대는60Hz81표본이며240Hz모든실제각최대로확대해석하지않는다.

검수자는 지정한 이 보고서만 새로 작성했다. 구현·기존실행·분석·이전검수·공용자산·다른담당파일은 수정하지 않았다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_search_v1.py`: `41f2fd25cd33204c39373c18c710fcab966db92ab859a62ef9b0937d896cdf50`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/native_margin_only_left_v1/report.json`: `b2c43e3d6abdc0f2af63716bc3512050fbda095f63b311d6a224c9c014e227c0`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/native_torso_p2_left_v1/report.json`: `5d1fc62af56ac6160848661885bf73f291439f4661cf2971064ea02a0c2068cd`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/analysis_margin_only_left_v1.json`: `cb0f5a83b877f78308582927db1e37c309493056f39329c0b9aa1307bc24a672`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/analysis_torso_p2_left_v1.json`: `0f238f75e6473d1f7921ee8ef95ce5c0f6553e249b16f101f840b1706390c042`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/visual_torso_p2_left_v2/report.json`: `c4dc6725e89226cdccb01c43362e3c30a14208f6aab955f536712a0a86c3da36`
