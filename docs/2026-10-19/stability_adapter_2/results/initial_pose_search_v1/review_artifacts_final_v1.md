# 초기 자세 탐색 산출물 최종 독립 검수

요약 판정: **문제없음**. 미해결 Critical 0건, Warning 0건, Suggestion 0건. 이번 검수는 확정된9회 물리 결과의 미디어 복사·본문 설명·권장 링크·생성 기록 범위다. 물리/관절/타현 측정 자체는 `review_physics_final_v1.md`에 별도로 보존한다. 검수자는 지정한 이 새 보고서만 작성했으며 산출물·소스·다른 담당자의 파일을 수정하지 않았다. 최종 보존 감사/봉인은 root 담당이다.

## 현재 권장 문서와 해결된 지적

권장 경로는 [root 결과 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/README_v3.md:1), [변경 색인 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/changed_files_v3.md:1), [상세 설명 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/README_final_v3.md:1) ↔ [영상 색인 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_search_v1/README_final_v3.md:1)다.

- V1의 legacy up cutoff 누락 방향과151프레임 설명은 원본을 보존하고 V2에서 정정했다. 현재 V3는 up≥3.95초가 **상향 앞부분1·2번 줄**을 제외해3·4·5·6만 집계한다고 설명한다.5초 영상151표본은 **t=0 포함0..5초**이며30fps 표시5.033333초를 추가물리시간으로 부르지 않는다.
- V2 상세 설명의 역방향 결과/변경 색인 링크가 이전root로 돌아가는 점을 전달했다. V3는root README_v3/changed_files_v3로 정확히 이어지고 상세설명↔영상색인의동일V3양방향링크를 확인했다. 이전V1/V2문서·미디어는 덮어쓰지 않았다.
- 검수 대상4개권장문서의모든로컬링크가절대경로로존재하고,명시된줄번호가실제범위안에있다. 메인README/PLAN의현재추가제목줄은2511/1427이며최신권장V3로연결된다. 기존2496/2501/2506 및1412/1417/1422의제목도보존된다. 모든main_before* 경계사본이현재메인문서의완전한바이트접두사임을확인했다.

## 미디어45개 검증

[artifact_manifest_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_manifest_v1.json:1)의 **36개MP4와9개PNG**에대해 sourceSHA=복사SHA=실제visual reportSHA를확인했다. 모든MP4복사본을직접ffprobe했다.

|조건|영상수|각프레임|fps|각MP4표시길이|
|---|---:|---:|---:|---:|
|정지4조건·타현·정지반복(6조건)|24|151|30|5.033333초|
|margin_only LH|4|299|30|9.966667초|
|torso_p2 LH|4|193|30|6.433333초|
|roll_m2 LH|4|301|30|10.033333초|

개별front/right_side/top은모두1280×940,합본은모두1920×470이다. 초기3시점PNG는각1280×940, 정지4비교/실패마지막/타현마지막의6PNG는각3840×940이다. 재인코딩/다른실행대체가없다. 색인에는36개모두Markdown MP4이미지문법으로연결됐다.

복사된초기전면(t=0), margin_only LH마지막카메라(9.933초), roll_m2정지5초PNG를직접열어native전신시야·기타/인체배치·기존원형접촉범례를확인했다. 초기그림은실제step0이며실패마지막그림에는‘보호중단직전·16초목표미완료’가표시된다. 초록/분홍손재질과접촉표식을구별하고X-ray·양의lambda채움/0빈원·고정크기·힘N/압력/면적아님을본문이정확히설명한다.

## 본문 사실 확인

- root와상세설명의9회표는comparison report의라운딩값과맞다. source7개중5적합/실제정지4개·LH3개·타현1개·반복1개라는범위를구별한다. 정지/RHscripted strike용 **임시margin_only**이며전체LH적격0·globaldefault유지라는결론이맞다.
- 정지LHfree418/1200,타현LHfree337/1200(접촉863)와RH0을구별한다. 모든정지조건에LH접촉이있으므로왼손무지지/양손독립지지성공을주장하지않는다.
- 세LH의actor-root20cm중단, BB와actor-root기준점차이, SO3가모두35°미만임을정확히설명한다. 물리종료/카메라끝/MP4길이도각각구별한다. margin의RH접촉97/240·moveB RHmiddle3접촉360/360, torso의부분openA104표본, roll의B유지/해제미완료를전체성공으로바꾸지않는다.
- legacycutoff와실제V7stroke window의차이는검출기/원RELEASE를수정한결과가아니다. 스크립트EW6·checkpointOFF·곡연주/학습성공아님을밝힌다.
- 초기값JSON과본문의15개Torso/Spine/Chest/Neck/Head target/actual rad행을전행비교해6자리반올림값이맞음을확인했다. BB/root좌표와정규화xyzw표현도초기값과맞다. DOF suffix를world회전축으로부르지않는다.
- 자유기타·strapOFF·root/하체고정·selfcollisionON·유한능동human제어, source proxy와cooked연속인증의차이, 수동평형/force측정/연주준비완료를주장하지않는범위가확정결과와맞다. root문서는60Hz81위치와240Hzactive33위치/81속도범위도구별한다.

## 생성·보존 근거

- [producer V6 before](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_before_v6.json:1)의11,753개입력을현재SHA와대조해차이가없었다. producer_v6자체SHA·before파일SHA·최초manifest의47개출력(문서2+미디어45)도모두현재일치한다. 이기록은원래V1산출의생성근거이며후속V3문서의새입력이라고소급하지않는다.
- V2manifest의이전4문서/manifest입력SHA·새3문서SHA·45미디어SHA가모두현재일치한다. V3의[artifact_manifest_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_manifest_v3.json:1)은before5개SHA·새상세/영상문서2개SHA와45개동일미디어를확인한다. current권장쌍과연결구조가맞는다.
- 기존물리실패/이전문구/이전문서/소스의보존을확인했으며빈보고서를만들어존재링크를맞추거나finalverification/inventory를작성하지않았다. 이번확인은실제완료된산출물에한정한다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/README_v3.md`: `1986f2c6c374f76893d49043b3f25495e7f01b114438a9ddb37d9ba26179aeeb`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/changed_files_v3.md`: `fc77f728756b879afdc3b636597b5583aaca042d0c0bf123d7e5135966036cf9`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/README_final_v3.md`: `0031280cea0a3b1d731f2b5a1c45c0a61e65066c1fa42202180ed19e96905d64`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_search_v1/README_final_v3.md`: `52c98d074750073e0c065eee8d14d2c98332e3408227943b5fb07a6556840e63`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_before_v6.json`: `9e07cf66cc2403f392a42818250795080bef60ec3d519075f5685f887232cd72`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_manifest_v1.json`: `bc3cca68522b64d14ca19193eb9583d45efbea4c1d13144aedcc427ff983bbeb`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_manifest_v2.json`: `31a48bf50336447100b0f5df95831b32a4e70112ea1b45932c1db7c32cf6f27c`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_manifest_v3.json`: `25d753c44e799dddd739de4e7a07dd7cee77ce8ed1c251a5767016b4f3715bee`
