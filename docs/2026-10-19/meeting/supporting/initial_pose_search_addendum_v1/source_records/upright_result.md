# 허리 직립·Chest/오른쪽 위팔 지지 자세 — 결과 및 인계

**정지 자세는 개선·검증했다. 왼손을 놓은 동적 안정화는 실패해 미완료다.** 정지 V17은 원래 모델의 Torso/Chest 축이 바닥 수직선에서5°이내, 옆기울기3°이내이며,1초 후 Chest와 실제 `R_Shoulder`의 기타 접촉이 동시에960/960표본에서 양의 solver 응답을 보였다. 전신 동적 안정화·연주용 최종 자세·15초 해제 성공으로 채택하지 않는다. PPO 학습은 시작하지 않았다.

권장 정지 재현은 `run_upright_v16` + `inputs/static_v17.json`이다. `inputs/release_v17.json`은 **4.10833초 실패 재현용**이다. 이전 하체 안정화 결과와 자세는 [기존 결과](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/README_v2.md)에 그대로 보존한다. 이번 결과·실패·영상은 이 디렉토리에 모았다. [영상 색인](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/media_index.md).

## 1. 실제 결과

|항목|직립 정지 V17|왼손 해제 V17|
|---|---:|---:|
|실제 물리 진행|5.000초/1200step|4.108333초/986step 중단|
|Torso 전체 기울기 최대|3.780322°|5.478688°|
|Chest 전체 기울기 최대|3.997685°|7.898001°|
|Chest 좌우 절대기울기 최대|0.972949°|5.071946°|
|Chest 좌우 종료|−0.570767°|−5.067966°|
|1초 후 Chest+위팔 동시 양의 접촉|960/960,100%|468/746,62.73%|
|마지막1초 Chest/위팔 양의 접촉|각241/241|Chest14/241,위팔241/241|
|기타 root 초기 대비 최대 이동|64.3638mm|200.4026mm,기존20cm gate초과|
|최대 q속도|1.936831rad/s|1.936831rad/s|
|완료/자세·접촉 종합 판정|통과|실패|

기존 자세의5초 Chest 옆기울기는+18.16°였고, 새 자세는5초−0.57°다. 같은 카메라·같은 물리 시각의 실제 native 프레임을 비교했다. 전체 수직선 이탈과 좌우 기울기를 구분한다. 프레임/CSV/원자료는 [그림 검증](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/figures_static_v17/verification.json), [정지 분석](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/analysis_static_v17/summary.json), [해제 분석](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/analysis_release_v17/summary.json)에 있다.

![같은 카메라의 실제 정지5초 전후](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/figures_static_v17/before_after_native_5s.png)

![정지 각도와 실제 접촉 전표본](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/figures_static_v17/native_tilt_motion_contacts.png)

## 2. 유지한 물리 조건과 자세 변경

원본105관절 모델/105입력 채널을 사용한다. 원래 비영 가동범위는97축이며,범위0의8축을없애거나제어입력8개를누락한것이아니다. native POSITION48/외부EFFORT57이고,하체24 중16유효축은유한 rotational stable-PD,명목0축8개effort는항상0이다. Root와의자는고정,기타는자유강체·중력ON·strapOFF. 기타고정/강제손부착/직접기타힘/매step상태덮어쓰기호출은없다. 초기설정API와실행중강제보정을구분해guard했다. 원질량·COM·관성·형상filter/마찰/contactoffset은이전원본105안정화실험과같다.

최종 **source14**는source9의몸통/머리/하체24를그대로두고,기타목을위로세운자유초기배치에양팔을맞췄다. source9대비기타root world이동[−139.646,+26.255,+231.511]mm와추가회전벡터[−.163299,+.435078,−.015927]rad다. 이것은기타root좌표이며기타몸통중심의동일한상승량을뜻하지않는다. 실제몸통표면이Chest와양허벅지사이에놓이게했다. 팔리핏후오른palm의guitar-local오차.134mm/.055°/왼palm약3.5e−8m/.000063°다.

초기source분리간격은Chest.400mm/Spine28.200mm/RShoulder.342mm/RHip.399mm/LHip.429mm, Pelvis BOX의보수적SAT분리.002m다. 전체source검사는 [source_audit_v13](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/source_audit_v13/report.json)에서통과했다. 이수치는source capsule/convex 계산이며PhysX cooked 관통깊이아니다. 손 mesh 전체의source무관통인증은하지않았고실제native접촉/궤적으로검증범위를보완했다. 상완의앞방향normal_GZ≥.5는soft희망값이었고실제.13393으로미달했으므로확보했다고주장하지않는다.

발은양쪽을지면에붙이지않았다. 초기왼발최저약19.95mm/오른발16.87mm이며,정지중source꼭짓점최저왼발8.37mm/오른발16.82mm다. Root고정좌식조건의자세안정성이며,발접지로버티는자유휴머노이드균형실험이아니다. 해제실패중왼발source꼭짓점최저−.250mm도관측돼기록했다(cooked깊이아님).

## 3. 유한 제어 변경 근거

- Spine이먼저받치는이전배치는sourceChest가가까워도실제Chest접촉이0이었다. V9/V11의numeric body ID와이름을독립재구성해mapping오류0,Chest filter368와Gbody4096의AND0을확인했다. 접촉누락이나필터차단으로설명되지않는다.
- source13은허벅지중심선이기타convex내부로들어가unsigned거리0/gap≈−radius(−59.8mm)에포화됐다. ±.1mm이동에도값이거의같아미분기반최적화가탈출하지못했다. source14는더높은초기seed에서시작해원래분리/손도달조건을모두만족했다. source13실패가허용영역전체의불가능성을뜻하지않는다.
- source14의V13은가슴접촉을얻었지만위팔접촉이끊기고Chest가옆으로5°이상기울었다. 전역방향servo V14는부호/좌표검수가맞아도동적으로진동해.8초중단됐다. 이실패도보존했다.
- 검증된upper scalarPD/lower stablePD로돌아온뒤,관측처짐을유한한고정관절목표로보정했다. target5 몸통9축=2*qref−V13종료q, target6=target5+.75*(qref−V15종료q). 나머지96축/하체24/명목0축8은동일하다. 자세/팔gain·감쇠·토크cap은키우지않았다. target는기존rate제한을통과해요청한다.
- 오른팔12축은10Hz sourceFK IK로움직이는기타의기존palm좌표와상완virtualpress점에도달하도록유한jointtarget만계산했다. 원범위/초기각±.8rad,손위치1cm/방향.05rad/지지점1cm예측gate를유지한다. **IK예측잔차와실제추종은다르다.** 정지실제RPalm/G오차최대13.992mm/3.875°,마지막1초10.709mm/2.012°다. 연주정밀도는입증하지않았다.

[실제/예측 추종 분리](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/support_audit_final_v1/report.json) · [독립 하체/물성/명령 감사](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/native_audit_v17/report.json) · [전표본 q→native FK 감사](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/coordinate_audit_final_v1/report.json). 정지와해제의모든240Hz표본에서제어연결부23개의q→world FK 최대위치오차는각.462/.634µm로10µm기준을통과했다. 관절suffix를world회전축으로가정하지않았다.

정지마지막1초하체24 최대peak-to-peak=.000109553rad,lower mass독립오차8.15e−7kgm²/child각속도오차9.31e−5rad/s다. 원래0범위8축도native수치잔차최대1.074e−5rad가있고,97축중3축의scalar범위미세초과최대8.66e−5rad가관측됐다. 범위설정/명령보존을실제상태가수학적으로항상정확히0이라고설명하지않는다.

## 4. 왼손 해제 실패와 남은 원인

해제V16은2.45417초/Groot200.498mm로중단됐다. 정지와해제의0~2초상태·센서·접촉과2초전effort/목표배열은exact다. 기존해제계산이초기guitar-localWrist anchor를currentG에다시붙이면서2초Cartesian목표오차33.597mm가생겼다. 제출jointtarget는rate제한을유지하므로state순간이동과다르다. [전환 감사V16](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/release_transition_v16/report.json).

controller14는2초실제LWrist world위치/회전과그순간이동방향을1회저장하고,손가락open2~3초/팔withdraw3~5초로분리했다. **새정지V17은V16과상태/센서/접촉/effort/target행전체가exact**다. 새해제V17은2초목표오차0으로연속성은교정했지만4.10833초/Groot200.403mm로실패했다. 실제최대회전21.70°/q속도1.94rad/s이므로직접중단원인은20cm이동gate다. [전환 감사V17](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/release_transition_v17/report.json).

Chest접촉첫누락2.05417초/RHip2.07083초로,계획된팔withdraw3초보다앞섰다. 2~3초에는fingeropen과실제Wrist-latch IK전환이동시에있어단독인과를분리하지못했다. 종료때도왼index1/index2가실제guitar본체와접촉했다. 따라서'왼손이해제됐지만15초가불안정했다'도아니며,**해제과정자체와지지유지가실패**한것이다. 5초후무접촉과15초완주는검증하지못했다.

후속은①손가락목표변경만/팔target전환만/실제목이격방향을분리한작은시험,②왼손하중을줄일때현재오른팔추종이기타의처짐을따라가는지와Chest/상완/양Hip접촉힘방향의가능성진단이다. 앞면을마주누르는상완배치등은미구현제안이며정답으로채택하지않는다. 작은gain외부PD도검증없이채택하지않는다. 새학습은여전히금지상태다.

## 5. 모든 새 정지 시도

|시도|변경|실제초|Chest옆최대°|Chest전체최대°|Chest양의표본|종합|
|---|---|---:|---:|---:|---:|---|
|V1|source2/Chest3D10N|5|3.855|4.087|0|실패|
|V2|source4/PelvisBOX 교차로 즉시 실패|0.0083333|0.440|3.502|0|실패|
|V3|source2/Chest단측법선10N|5|3.822|4.057|0|실패|
|V4|source6/Pelvis제약·몸통전경|5|1.024|4.116|0|실패|
|V5|source7/Hip초기−.04|5|1.076|4.162|0|실패|
|V6|source9/Hip초기−.08·발부유|5|0.496|4.633|0|실패|
|V7|같은source9/Hip목표bias−.04|5|0.880|4.319|0|실패|
|V8|같은source9/Hip목표bias−.08|5|1.703|3.960|0|실패|
|V9|Chest법선cap20N|5|1.706|4.147|0|실패|
|V10|upper_target2/Spine먼저접촉|5|1.142|3.990|0|실패|
|V11|source10/기타중앙이동|5|2.663|3.890|0|실패|
|V12|Chest목표앞8°|5|1.753|7.608|0|실패|
|V13|source14/넥상향·양Hip/Chest접촉|5|7.090|7.144|1161|실패|
|V14|absolute몸통servo 진동 중단|0.8|2.241|3.643|151|실패|
|V15|오른팔IK·관측처짐target5|5|1.156|5.505|1142|실패|
|V16|target6 추가처짐보정|5|0.973|3.998|1132|통과|
|V17|16과정지동일/해제경로교정|5|0.973|3.998|1132|통과|

이phase의정지시도17회중5초자체완료15회,전체기준성공2회(V16/V17,동일물리경로재현)다. 해제시도2회/15초완료0회다. 기존하체phase시도/성공횟수와합치지않는다. [기계판독 시도표](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/attempt_summary.json), [앞선 상세 실패와 보존 사고](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/progress_v3.md).

source1~14에는로컬fit실패·BOX감사누락·발기울기실패·상완normal미달도포함하며숫자가곧실제물리실험횟수는아니다. source5는검수자의SAT괄호오진으로중단했고원helper1/2가수치동일함을검증해정정했다. 초기audit2/3은PelvisBOX를빼먹어source4를잘못통과시켰으며,새audit7~13에서보완했다. source4/nativeV2실패와좁은이전인증범위를보존한다.

## 6. 재현·입력 보존

```bash
PYTHONDONTWRITEBYTECODE=1 MUJOCO_GL=osmesa \
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
TORCH_EXTENSIONS_DIR=/tmp/torch_extensions_tab2body \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-} \
/home/ajou/miniconda3/envs/rl38/bin/python -u \
-m stability_adapter_2.lower_body_release_v1.run_upright_v16 \
--config /home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/inputs/static_v17.json \
--out /tmp/upright_static_fresh_output
```

반드시존재하지않는출력경로를쓴다. 실패해제재현은config만`release_v17.json`으로바꾸고새출력경로를쓴다. 해당경로를성공설정으로사용하지않는다. CPU PhysX/Isaac Gym nativecamera의단회연구결과이며다중seed·외란·정밀압현·타현·GPU학습환경동등성은미검증이다. 몸통up축<4°와원capsule중심선이루는전체각도최대10.092°는정의가다르다. 완벽한기하학적허리직선이라고주장하지않는다.

모든소비코드/입력/leaf계획/결과는버전별보존했다. V8종료후이미broadpin에포함된미실행보조helper2개를일시편집한사고가있어최초사후분석이false를기록했다. 개선본을새v2로옮기고원v1을byte-exact복원해989개입력SHA일치를독립확인했다. 최초false분석과새analysis_static_v8_v2를함께보존하며전기간무수정이라고소급표현하지않는다.

최종검수는 [정지 검수](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/review_static_v16.md), [해제 검수](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/review_release_latch_v1.md), [좌표·후속 검수](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/review_followup_v1.md), [팔IK 검수](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/review_support_ik_v1.md)를참고한다. [최종 보존 감사](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/final_verification.json) · [소스 스냅샷](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/source_final/manifest.json) · [전체 산출물 SHA 색인](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/artifact_inventory.json). 마지막세파일은root최종봉인단계에서생성한다.

최종 봉인의 일괄 문법검사에서는 이전 단계에서 의도적으로 보존한 실패 분석 V2의 IndentationError도 다시 확인했다. 현재 제어의 회귀가 아니며, 원본과 봉인 첫 실패를 보존하고 새 봉인 버전에서 구분했다. [범위·근거·기록](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/seal_notes_v1.md).
