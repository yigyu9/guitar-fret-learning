# 초기 자세 탐색: 최종 물리·측정 독립 검수

요약 판정: **문제없음 — 시험·측정·제한된 후보 판단 기준**. Critical 0건, Warning 0건. **margin_only를 정지/오른손 scripted strike 실험용 임시 후보로만 추천하고, 양손 연주 기본값은 유지**한다는 결론이 증거와 맞다. 세 왼손16초 동작은 모두 실패했으며 검수 통과가 해당 동작 성공을 뜻하지 않는다. 미디어 복사·권장 문서/영상 색인 최종 검수는 별도다.

## 9회 원자료 재계산

|후보·시험|완료/실제경과s|최대BB mm|최대SO3°|LHfree/240Hz표본|RH손목·손raw접촉표본|
|---|---|---:|---:|---:|---:|
|margin_only 정지|완료5|3.286739|0.819455|418/1200|0|
|roll_m2 정지|완료5|6.066885|2.352577|46/1200|0|
|roll_p2 정지|완료5|20.857204|4.727968|93/1200|0|
|torso_p2 정지|완료5|3.999468|1.159350|113/1200|0|
|margin_only 왼손|중단9.966667|112.825130|29.121506|1315/2392|798|
|torso_p2 왼손|중단6.433333|62.826053|28.493017|468/1544|18|
|roll_m2 왼손|중단10.016667|116.170436|30.140898|1132/2404|916|
|margin_only 타현|완료5|5.116316|2.203204|337/1200|0|
|margin_only 정지반복|완료5|3.286739|0.819455|418/1200|0|

[comparison_v1/report.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/report.json:1)의 각9조건을 초기0초+모든240Hz 기타pose/접촉에서 독립 대조했다. BB local centre `[0,−.4,−.055937985]m`와 SciPy 정규화quaternion으로 world BB·SO3를 재계산했고 모든최대값/actor-root/접촉free·paired·RH수가 일치했다. BB/SO3 최대가 같은 시점이라는 주장은 없다.

4정지+3왼손+타현+정지반복=9회, 완료6회/보호중단3회다. source V2의7개중5개적합·실제정지4개검사라는 범위를 구별한다. V1의4개 source탈락 partial/native0도 이전기록으로 남긴다. source 최종1,308입력 현재SHA가 모두 같았다.

## 후보 선정과 독립 지지 제한

margin_only는4정지중 BB/SO3 모두최소이고 반복이 일치해 정지한정 임시추천이 타당하다. 하지만 정지에서LH접촉782/1200, 타현에서863/1200이다. 두 결과를 왼손 무지지 안정성이라고 설명하면 안 된다. source 공통A/상대회전·기본 near 기준은 유지했고 후보별 q/G/지원task local점 재계산을 포함한 초기형상 탐색이다. 수동평형·원인분담·일반강건성·압현학습 초기값 확정도 아니다.

세LH중단 원인은 actor-root205.923375/203.210348/210.964217mm로20cm를 넘은 것이다. 회전35° 미만이며 모두16초미완료다. 기존near16초37.288mm/14.516°완료보다 동작 안정성이 좋아졌다는 증거는 없다. [정지한정 결정문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/static_candidate_decision_v1.md:1)·[root결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/README.md:1)·[완료문서](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_COMPLETION_V1.md:1)의 이 구분이 맞다. global default는 변경하지 않았다.

margin_only의A유지360/360은엄지3+검지3 양의접촉이다. A놓기LHfree240과moveB LHfree360이 있지만moveB 오른중지3 접촉360도 있다. margin_only는B접근부분에진입했으며10초B유지는시작하지못했다. torso_p2 openA는6–6.433333초104표본만 관측했다. roll_m2는10–10.016667초의B유지부분4step에서엄지/검지양의접촉이 있으나1.5초유지·해제를완료하지못했다. 단순히모든B접근/접촉이없었다고말하면안된다. 이러한부분관측과완료여부를현재문서가구별한다.

## 제어·기하·입력

- 7개앞선조건 native before는각1,313개, 타현1,314개, 반복1,315개다. 모든파일의현재SHA가일치하며 각map에 실제human/G XML·compiler.meshdir 모든mesh선언 union106개가있다. 각analysis 입력map과비교/240Hz보충입력도현재일치한다. 선택후보candidate/config/native초기props를직접묶는SHA도유지한다.
- 모든240Hzcontacts가1..N 연속이고 실제제출81effort의coverage/finite/cap를확인했다. 목표각model limit/rate 및정지는전체/left는다른48/strike는다른75목표exact를각각독립검사했다. 실제관절상태동결과구별한다.
- 초기/최종Pelvis·하체native상태는같고runner는매60Hz에도고정체상태를검사한다. forbidden0·초기q/속도/FK/source proxy gate·기타자유/strapOFF/자기충돌ON을유지한다. body9+arms24유한human effort와나머지48 POSITION목표를구별한다.81벡터는최종제출EFFORT명령이며POSITION48의실제순토크/접촉력측정값이아니다. 새기타외력/고정/손부착/지속pose덮어쓰기경로는없다.
- source/analytic capsule/이산EW도달검사는cooked연속비관통인증이아니다. 상속된호환metadata를새실제접촉판정으로쓰지않는다. 실제그립/해제관측과source적합을구별한다.

## 240Hz 관절 보충

[audit_initial_pose_search_240hz_v1.py](/home/ajou/yigyu/3/stability_adapter_2/audit_initial_pose_search_240hz_v1.py:11)는pre0..N−1과finalN을합쳐**active33위치·전체81속도**를검사한다.9조건모두행정렬과값을독립재계산했다. 나머지48위치의240Hz 최대는기록범위밖이며원래analysis81관절각/속도통계는60Hz표본으로보존한다.

[joint_240hz_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/joint_240hz_audit_v1.json:1)의 active33실제위치 최대초과는margin_only LH의L_Thorax_z0.026024728°(6.675초), 전체81속도 최대는margin_only strike2.920955420rad/s다. 모든시험은50rad/s미만이다. 정지margin_only/반복/타현의active33초과0은해당범위측정이지모든81위치를240Hz검사했다는뜻이아니다. 목표변화율과실제속도도구별한다.

## 초기값·반복·타현

- [summarize_initial_pose_search_v1.py](/home/ajou/yigyu/3/stability_adapter_2/summarize_initial_pose_search_v1.py:13)의9조건집계와출력초기값을원자료와대조했다. [초기값JSON](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_initial_values.json:1)의81이름/target/actual이정지native초기와같다. [CSV](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_joint_angles.csv:1)의81행순서·target/actual rad·deg를전행검증했다. 후보SHA와정규화Gquaternion·actor-root·BB좌표도일치한다. BB는[.1432297135,−.0011729466,.6830222996]m다. nativeDOF suffix는world회전축이아니다.
- 정지/정지반복의initial_values/trace/actual_contacts/final_efforts/final_state5개가SHA로정확히같다. 반복도독립1회native실행이며영상복제/traceplayback이아니다. source의빈full_left_task_qualified_candidates는실제왼손완료0과맞고정식학습성공기준으로확대하지않는다.
- 원래 [strike_detector_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/strike_detector_v1.json:1)의1,922개입력SHA가현재일치한다.12RELEASE만존재하고[실제시간창보충](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/strike_actual_windows_v1.json:1)의각eventpayload가원RELEASE와동일하다. down3.2–3.55에서6→1(3.245179–3.506343초),up3.75–4.45에서1→6(3.833910–4.363355초)이다. legacyup≥3.95의3,4,5,6 집계는원본대로보존했다. detector변경이나checkpoint/곡수행성공이아니다.

신규두집계소스AST는통과했다. 물리재실행·원래소스/설정/결과/타담당파일수정은하지않고이보고서만작성했다. 작성중인artifact문서/미존재자료링크와미디어최종QA는다음별도검수에서확인한다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/summarize_initial_pose_search_v1.py`: `4f7a5d21c754a7da49081aebcdb5a10b2f7b712ee9fd8e0ebe7192ef493e0971`
- `/home/ajou/yigyu/3/stability_adapter_2/audit_initial_pose_search_240hz_v1.py`: `4227ec437846b4839df1df0f362756edba956529008ba23fa75b66fa9da172fe`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/report.json`: `6291a8345e564261d03c555159ffac9191c054cd28e5846215f026da0852b22e`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_initial_values.json`: `530421177ab7c9358d2c3496a0b4406048e79daa710e663244bb0ef625ba3754`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_joint_angles.csv`: `a15b31bba5ea8e2673233e704a88abee83fcdba066e55e5e45ba2af08ee54a46`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/joint_240hz_audit_v1.json`: `33f5c0069b107c74eb3ea142cb7afbae8c856d3e9ae888f40d2f71c067c16c8a`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/strike_actual_windows_v1.json`: `5e4109beb20c0d9850dedba10f7373862d786f5c75a5f91b6a48ff1b2f719d61`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/README.md`: `9e7667c6b7f5d98f74aab8a11313fe85809fcfad0f66914f5d25ec84a299a47c`
- `/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_COMPLETION_V1.md`: `f287d242f6d3049caad33115f11ca20bcbaf32d5a5dfc2b0a9c54615bb82061d`
