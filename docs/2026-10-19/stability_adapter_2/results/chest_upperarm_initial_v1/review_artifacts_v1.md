# 초기 가슴·위팔 지지 산출물 독립 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 선호문서rootREADME→artifactREADME_v3/videoREADME_v2,실제이미지/영상/CSV를원자료와대조했다. 기록상사전map덮어쓰기한계를명시한범위에서현재성공산출물은확인된다. 최종봉인실행은root의후속단계다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음.

## 원자료·복사본 검증

- copy_manifest의36copy를직접검사했다:12MP4+12초기PNG+12마지막PNG가원본/복사/기록SHA와모두동일하다. 이전원본영상을다시편집한파일이아니다.
-12MP4를실제ffprobe로확인했다. 전부1280×720/30fps/151frame/5.033333초다. 이는물리5초에t=0초기프레임을포함한151프레임이며장면정지나반복추가로경과를늘린영상이아니다.
- PNG치수는초기12개1280×960,마지막12개1280×720다. 초기카메라기대1280×720/상속side1280×960충돌과0step실패설명을바로잡았다. 실패native_hold_v1을정상4실행에포함하지않는다.
- motion_samples_v1.csv의4804행(4×1201)을analysis의time/BB거리/SO3시계열과숫자단위로전부대조해exact였다. initial_joint_angles_81_v1.csv의324행(4×81)은nativejoint이름/index/qpos/q_ref와exact이며qpos−q_ref=0이다.
-5개nativeattempt의1270/1273/1278/1278/1281개beforepin을현재파일과직접대조해모두변경0을확인했다. 물리소스/실제입력/원자료가문서수정으로변조됐다는증거는없다.
- 현재성공산출manifest의before/after70개입력과producerSHA,derived5개SHA도모두일치했다.

## 시각 및 설명 정합성

- 초기4×3비교/마지막4×3비교/240Hz그래프PNG를직접열었다. 행hold/near/clear/far,초기열정면/측면/줄표시,마지막열전신/손/근접순서가sourceproducer와문서에일치한다. graph의4조건곡선및최대값도CSV/analysis에맞는다.
- Producer는sourcePNG를복사하고동일비율thumbnail로whitecanvas에배치한다. Nativeimage형상은AI생성/왜곡/임의덧그림이아니며줄표시가비물리적선분임을설명한다. 판정은이미지눈대중이아닌nativequery/pose자료로설명한다.
- 선호rootREADME9/artifactREADME_v3 18/videoREADME_v2 13개,총40개전체Markdown목표가모두존재한다. 상대링크와camera치수역전/사용자가near를선택했다는오해가선호V3에서해소됐다. 기존V1/V2는보존한다.
- 표의4조건LH접촉804/1090/326/0과BBmax2.759/4.287/4.601/4.915mm,SO3max.680/1.219/2.486/2.833°는원자료와맞는다. 원래detector를바꾸지않고V7up시작3.75초/끝4.45초에맞게집계한왕복6현임을구분한다. source_path_v1의39/61충돌실패는선호경로증거로표시하지않는다.
- Far의0LH/0RH는왼허벅지접촉이없다는뜻이아니다.3.75–5초실제Chestrawcontact0/300,오른상완/오른허벅지positive각300,왼허벅지raw300/positive259다. 문서표가positive표본임을명시하므로259표기를raw전체접촉수와혼동하지않는다. 가슴지속밀착·오른상완/오른허벅지만의수동평형·힘폐쇄·학습곡성공을주장하지않는다.

## 문서생성 이력의 감사 한계

- Root의viewerREADME_v2 출력경로수정이artifactpreflight와겹쳐SHAguard가거부한뒤,artifactagent가최초artifact_before_v1 입력map을새map으로덮어써이전거부map이독립보존되지않았다. 이사실을선호문서와doc_correction/correction.json에명시한다.
- README원문inverse편집재구성은변경내용설명일뿐원래attestedbeforepin복구증거가아니다. 본검수도이를원래inventory완전보존이나과거봉인인증으로취급하지않는다.
- 현재성공generation의입력SHA/producersha/sourcecopy/derived자료는직접검증했고native전체beforemap도별도로동일하다. 따라서제한은최초거부artifactpreflight이력이며실제물리결과와현재성공산출물검증을구분한다.
- artifact_doc_correction_before/후속기록은새V3문서생성의입력보존범위를명시한다. 이전잘못된설명/producer/native/data를덮어쓰지않으며최종seal도이범위를넘는소급보존주장을하면안된다.

## 검수 SHA256

- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/README.md`: `1061ac413de6e6042971940631696c0dc12faaf0e9d0216ab8a566bd890085e1`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/README_v3.md`: `3b04a462c513cacacb36fabc24e80757b833657e215d032533dfdd99284ad166`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_upperarm_initial_v1/README_v2.md`: `efa93506bd063ced00f58636edf5e00cce081628a23a1f81e93f738d210e25bc`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/copy_manifest_v1.json`: `7a904b13948338bb7d26cfa3dcaa66b6238a217100141e35c574f10d711aa56e`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/artifact_before_v1.json`: `fbb1ae50f28ec3157598913ab5c273aedce4e1bea863d06de78d1f62dc505720`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/initial_joint_angles_81_v1.csv`: `55798be41eb8903b1a79af716f578670b9dac6c40b4a03ca2086cd825b960c5a`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/motion_samples_v1.csv`: `09323f7a233ce6286af3fe852191fb6b1fb6cb357269e653cdaa87a915057273`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/doc_correction_v1/correction.json`: `4fa8a8adedb162051926594552a552eac7e62fcf50f9a5da78066de721a5af4d`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifact_doc_correction_v1.json`: `1ce8b4938959b25819f92ce23bce0d6a1f86d46e87f34a3800ab9f457b0354d0`
