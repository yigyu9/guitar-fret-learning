# 고정LA·중지3 목표 총−.15rad 실행 전 검수

## 요약 판정

**문제없음**. 검수자는새4소스/leaf와분석wrapper만읽고ASTcompile 및저장baseline의독립float32조립을확인했다. Preparation/native/analyzer main/renderer는실행하지않았으며review.md외파일을수정하지않았다. 실제새물리응답은미검증이다.

| 검수 소스 | SHA256 |
|---|---|
| FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md | `c3ec0441bd8ea4c725841a5a030653a35b7f6600170d3eeb81fcaa38b9aff560` |
| prepare_fixed_strap_middle_relax_v2.py | `248bb8a4f15a91053444b221a1851ebb8541bb8f92af7d3746aac4b9a10f112f` |
| run_fixed_strap_middle_relax_v2_phase.py | `0e3e9ff78f0beb9c908d1409ce086fea5872fac842327a4a06c7e8453bde81a7` |
| analyze_fixed_strap_middle_relax_v2.py | `440511be41d70ef7e253541029a3981cb731ea8a044a81dfcd4328f8c9075e54` |

## 준비·보존·실행 계약

- [prepare_fixed_strap_middle_relax_v2.py:31](/home/ajou/yigyu/3/stability_adapter_2/prepare_fixed_strap_middle_relax_v2.py:31)는joint18baseline원trial을복제하고LH:middle3 offset만기존baseline대비총−.15rad한다. 직전−.05조건에다시−.15를더하는방식이아니다. 복원한trial전체/other80목표·초기설정·G·LA가같음을검사한다. 원초기q81/몸통9목표·PD/root하체/자유G·66권한/손목±.005rad1Hz는그대로다.
- 독립 qfloat32+offsetfloat64→float32조립값은middle3목표 `0.9091416597366333rad = 52.08998008242786°`, baseline대비실제차 `−0.1499999761581421rad`, q기준offset `−0.14060189723968505rad`다. Other80 target은exact이고손목−.005/0/+.005의세상태모두nativebounds/offset±.3rad안이다. Compose와desired의exact검사는clipping을허용하지않는다. 실제초기middle3각60.145874°는바꾸지않는다.
- 최초검수시wrapperpreparation입력에새로소비하는v1 inventory/finalverification/decision 및inventory982개가누락돼있음을지적했다. **미소비단계에서해결됨**: preparer:38–44는3metadata와982개원SHA를hashes에넣어끝검사에도포함하며, [run_fixed_strap_middle_relax_v2_phase.py:37](/home/ajou/yigyu/3/stability_adapter_2/run_fixed_strap_middle_relax_v2_phase.py:37)는동일3metadata+982파일을실행전후SHA목록에포함한다. 이전decision도source snapshot대상이다. 현재982파일의size/SHA가봉인inventory와일치함을직접확인했다. 소비된이전v1파일은수정하지않았다.
- Wrapper:24–35는stage실행기록/log/native출력재사용을거부하며frozen entry `2f6565…` 및runner `34d50c…` SHA를강제한다. Proposalchecks/trialSHA와전체입력의실행전후SHA·명령/env/exit/logSHA·R-relative sourcecopy를보존한다. Snapshot대상.py경로는모두R하위임을확인했다. Freshnative14/1188source gate는frozen entry에위임하며그인증을동적cooked관통0/해부학pad/접촉력N으로확대하지않는다.

## 세 조건 분석·후속판정 범위

- [analyze_fixed_strap_middle_relax_v2.py:16](/home/ajou/yigyu/3/stability_adapter_2/analyze_fixed_strap_middle_relax_v2.py:16)의baseline/옛−.05/새−.15폴더가분리돼있다. 34–46행은39개직접입력과옛preparation의실제float32delta를포함하며각조건delta를혼용하지않는다. 57–73행은각label에별도checks를써서한조건결과가다른조건으로덮이지않는다. 각1200other80/clock/wrist/constantdelta·원trial복원·13공통초기필드·rawG/trace·native14/1188·root하체·151frame/readonly/MP4/PNG검사가유지된다.
- 67–71행의독립float64합→float32 expected와command exact 및nativebounds/offset±.3검사는compose재호출만으로무clipping을추정하던계약보다명시적이다. 81–99행의121complete1초창/241표본/고정2초ref구분,actualnativebound초과관측,rawpositiveλ 고유step/self기록과중지3추종을유지한다. 추가middle2goal/5초actual은변경되지않은목표와물리응답을구분한다. 전체3603jointrows/363windows를생성하는구조이며새native집계는이번한조건1init1200step이다.
- [FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md:5)는총−.15/추가−.10을명확히구분한다. 이전실제−.05진척을후속후보선정근거로쓰되새후보의성공을미리주장하지않는다. 임시initial30mm/5°와rolling1초5mm/1°는자연성/연주성공인증이아니며sourceprofile/실제fret·strike/학습은이번구현에없다. Aug19분포는soft선호이고모델hardlimit·strap길이·PDgain변경은없다. 접촉/유지악화도그대로기록하고초기q·다른중지관절은다음단위로분리한다.

Critical: 없음. Warning: 최초SHAclosure누락은실행전해결돼미해결blocker없음. Suggestion: 없음. 실제새준비·freshgate·1200commands·각도/접촉·그림/문서는완료후별도검수범위다.

분석wrapper SHA `252e3facdb494dd1b47c9431bc108a21a2e146ccbea6630889f75bb4f0b8a1f0`도읽고ASTcompile통과했다. 10source/helper/leaf/invocation과metadata4개+3조건각9raw의총41입력을실행전SHA/사본으로보존하고명령/env/exit/logSHA/전후SHA를남긴다. 분석main/native를호출한검수는아니다.


## 실제 세 조건 저장자료·영상 수집 독립 검수

요약 판정: **문제없음**. 검수자는저장원자료와별도NumPy/SciPy SO3계산을대조했으며preparer/native/analyzer main/render를재실행하지않았다. [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/analysis.json)의31checks/39입력closure와[preparation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/preparation.json)의7checks/12449입력SHA가모두맞다.

| 실제 실행 기록 | 전후·현재SHA 일치 입력 | 사전사본SHA 일치 수 | 종료 |
|---|---:|---:|---:|
| preparation |12450|410|0|
| native |12453|411|0|
| analysis |41|10|0|
| collection |143|5|0|

각metadata전후입력맵·현재원본·source_manifest모든사본·실제logSHA를직접대조했다. 이전v1파일과frozen nativeentry/runner를소비후수정하지않았다.

- 세run각1201rawstates/trace·1200controls/contacts의전체step/240Hz시계,report1init1200step/completed/failureNone/모든checks·violations0을확인했다. Rawt0state와13공통초기필드는모두baseline과exact다. Middle3offset만복원하면trial전체도exact이며other80의전체1200목표·명령step/update/time/wrist파형은exact다. 각조건실제middle3delta가자기preparation값과맞아−.05/−.15를혼용하지않는다.
- 초기qfloat32+offsetfloat64→float32를전체3600command에독립적용하여기록target과exact·모든nativebounds·offset±.3rad를확인했다. Clipping은없고LA1.1018469719600776m/원PD/body9·root하체는유지된다. 실제root하체body state는각run전1201시점에서t0와exact다. Fresh14checks/1188sourcepair·초기교차0도각run원자료와맞으며동적cooked관통0인증으로해석하지않는다.
- RawG world위치/xyzw와trace가일치한다. 독립SciPy SO3 상대회전으로모든363개1초창(각121start480..960/stride4/241표본)과고정2초ref변화를재계산했다. 위치는1e−10mm이내,회전은1e−6°이내에서일치한다. 3603jointseries의middle3actual/heldgoal·middle2actual·시계가원actualq와일치하며middle2goal/5초actual도summary와맞다.

| 지표 | baseline | 총−.05 | 총−.15 |
|---|---:|---:|---:|
| middle3목표 ° |60.6843456434|57.8195593998|52.0899800824|
| middle3실제5초 ° |60.6842910018|57.8208503055|52.0908645919|
| 새1초최대위치 mm |.4559120014|.4372975268|.4373866509|
| 새1초최대회전 ° |.0840486097|.0811468957|.0802892710|
| 기존2초ref위치 mm |.2577856101|.2981385071|.2461075142|
| 기존2초ref회전 ° |.0510029624|.0584584640|.0476646025|

각1201표본의initial30mm/5°와각121창의rolling5mm/1°잠정범위는모두통과한다. −.15의1초위치는−.05보다약.0000891241mm크며초기회전도조금커단조개선이아니다. 새actualnativebound초과9.9904835224e−5rad를summary에그대로기록한다. 이산관측·singletrial이며자연성/연주성공·반복강건성인증은아니다.

- Human–Gpositive rawλ를body별고유step으로직접재집계해summary와일치함을확인했다. 새middle3는50steps/min30/max80(2초이후0),ring3는19steps37..55(2초이후0)이다. 검지1158/엄지124/RHip1200도맞다. Palmpositiveλ없음/self기록0/palm-up proxy pass이며λ행증가를후기지지개선또는힘N으로확대하지않는다.
- 13routepoint/점속도로원6000/120/cap300 tension-only straplaw를별도재계산해다음step last-applied tension과오차0을확인했다. LA/initialroute·slack조건은세run같다. 151capture의step8/time j/30/renderreadonly·raw/strap604PNG SHA와2MP4 SHA/151frames/30fps/151/30duration도대조했다. 새hands5초PNG를실제열어장면·손/기타·기존strap표시를확인했다. 새hands MP4 별도ffprobe도1280×720/151frames/30fps/5.033333s로맞다. 물리마지막시점5.000s와파일duration은다르다.
- [collect_middle_relax_v2_videos.py:17](/home/ajou/yigyu/3/stability_adapter_2/collect_middle_relax_v2_videos.py:17)의수집결과는기존136개영상/VIDEO_INDEX_v8 SHA를보존하고새원본두개와두복사본SHA를일치시킨다. [video_collection_update_v8.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v8.json)의새VIDEO_INDEX_v9 SHA와실제138개count도맞다. 별도invocation의5사전사본/143입력·실제log/exit0기록이일치한다.

[FIXED_STRAP_MIDDLE_RELAX_V2_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_V2_DECISION.md:7)의3조건표와초기구역/1초창·초기짧은접촉/목표무clipping·actualbound관측이원자료와맞다. [8월19일 정리:39](/home/ajou/yigyu/3/docs/2026-08-19/정리.txt:39)의middle2관측p01~p99는22.7~80.2°,middle3는1.4~46.1°다. Middle2목표64.343141°는그soft관측구간안이며큰scalar값만으로전체자세를부자연스럽다고판정하지않는설명이맞다. 분포를PhysX hardlimit으로교체하지않았다. 다음중지3초기q를현재52.089980°목표에정렬+offset재계산/동일절대PD목표유지는미실행이며새sourceFK/교차/freshnative검증이필요하다고구분한다. 현재mainREADME/PLAN추가분도동일범위이며길이조절/기타feedback/새actor·학습이없다.

Critical: 없음. Warning: 미해결actual자료·수집blocker없음. Suggestion: 없음. 실제최종그림과한국어결과문서는후속검수범위다.

## 세 조건 그림 producer 실행 전 검수

요약 판정: **문제없음**. [make_middle_relax_v2_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_middle_relax_v2_artifacts.py)의현재SHA `703ba61ae363c5e3a6bbfea030c507da48530bf0b4c1815642a8edcaf11eb11c`와[run_producer.sh](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/run_producer.sh) SHA `d053e2affd83386bf137baf082b78a1166830b3ecb645ea9275f1ba73903599f`를읽고producerASTcompile을통과했다. 검수자는producer/renderer를실행하지않았다.

31checks/39consumed-input전후및현재SHA closure를사전검사하고3label순서를고정한다. Fullpath R-relative/external sourcecopy·실행전snapshot 뒤3603jointrow/363window·각121count/goal/5초actual/summarymax/passcount를대조한다. 각조건실패결과를숨기는allwindowspass gate는없다. 좌측3actual/3heldgoal은색으로연결되고center-right실제curve범례3개와solid/dashed캡션을쓴다. 우측6막대는각5mm/1°로정규화하고adaptive xlim이threshold1및현재최대비율+label여백을포함한다. Group표시ylim/3줄캡션여백이명시돼있으나실제겹침은생성후확인한다. Wrapper는기존PNG/manifest/log/source snapshot/execution/자기archive를사전거부하고명령/env/exit/logSHA/입력전후/출력SHA를기록한다. Artifact중native/physics/actor/train0 범위가맞다.

Critical: 없음. Warning: 미해결첫그림실행blocker없음. Suggestion: 없음. 실제PNG/manifest/최종문서를미리완료로표시하지않는다.


## 최종 실제 그림·문서 검수와 기록 동결

요약 판정: **문제없음**. [middle_relax_v2_native_summary.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/middle_relax_v2_native_summary.png) SHA `8129bc11b7a5e92e49ddc2949ddcb96be193cce353f50877544ae6ccc0200ba1`를실제열어확인했다. 저장native원자료의별도과학도표이며native프레임편집/새렌더가아니다. 검수자는그림/분석/물리를재실행하지않았다.

- 좌측3actual곡선과같은색3constantgoal은독립검수된3603jointrows의동일60.145874°시작/세목표/추종방향과맞다. Actual범례3개가곡선을가리지않고solid/dashed역할은캡션에명시돼있다. 우측6막대표기 .456/.437/.437mm와.084/.081/.080°는원summary를3소수점으로반올림한값이다. 막대길이는각5mm/1°로나눈비율이며임시threshold1과목표선을구분한다. 두.437mm표시가숨기는미세차이는README의6소수점표/0.000089mm차이설명으로보완한다. 제목·단위·group label·축·범례·3줄캡션이겹치거나잘리지않는다. 121개/241표본/2~4초60Hz창과미인증범위도맞다.
- [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/artifact_manifest.json)의55입력전후SHA와현재원본SHA가전부같다. [source_snapshot.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/source_snapshot.json)의55사본은전체원본path/SHA맵과같고각사본byte SHA도맞다. Producer703ba61…/wrapperd053e2…는사전검수본과같으며wrapper원본/archived SHA도같다. Producer_execution exit0/1.439345598s·명령/env/logSHA/입력전후/producer/출력SHA는manifest와맞고artifact중native/physics/actor/train은모두0이다.
- 최종 [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/README.md)의3조건목표/actual/초기오차/새1초·고정2초ref표는앞서독립재계산수치와같다. Initial81/G/LA/PD/other80유지·총−.15와직전−.05비교·전지표단조개선아님·새짧은초기λ≠후기지지개선·중지2soft분포참고/분포≠hardlimit·자연성/실제fret·strike미검증을구분한다. Native2MP4와시작/끝PNG를절대경로embed하며sim5.000초와151/30=5.033333초파일길이를구분한다. 마지막보완에서이번artifact단계새overlay없음/실행시저장한route overlay보존/천geometry아님을정확히명시했다.
- [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/CHANGED_FILES.md)는산출물담당변경과root별도실행/수집7개파일을구분한다. 추가된prepare:28/phasewrapper:20/analyzer:31/collector:16/trial·invocation링크는실재하고각line도유효하다. [ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/ROOT_VERIFICATION_NOTES.md)는원입력/사본수·CPUPhysX/경고·actualbound작은초과·target무clipping/source초기≠dynamiccooked·영상138개를정확히구분한다. Root의직전4봉인phase1132개파일감사는root후속범위이며본검수에서광범위과거전수감사를했다고주장하지않는다.
- Main [README.md:1060](/home/ajou/yigyu/3/stability_adapter_2/README.md:1060)/[완료기록:1065](/home/ajou/yigyu/3/stability_adapter_2/README.md:1065), [PLAN.md:1858](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1858)/[체크포인트:1863](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1863), [VISUAL_REPORT.md:1971](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1971) 새추가분은실제raw/결정/그림과정합한다. 다음initialmiddle3qalignment는미실행이고동일최종절대목표를유지하려는별도시험으로구분한다. 고정LA/다른환경출처pending/다른80·중지2불변/최종66권한/root하체고정/몸통목표/자유G와미완료sourceprofile·연주·학습범위를유지한다. 이전준비시점과새완료기록도추가순서대로구분한다.

| 최종 문서 | SHA256 |
|---|---|
| 결과README | `bc74e8640bd33429cbe33561d250a9e9b89e0b870419bd7a405fafb969edbf21` |
| CHANGED_FILES | `97d05a2aa86518f09ba50bda2d350ac88b7e5f6106df66b126b907e691437df3` |
| ROOT_VERIFICATION_NOTES | `d61d69e3b1ec0676c7da8119130f2f0c909c34d5ecf153d363a59b811406cf6e` |

Critical: 없음. Warning: 미해결최종봉인blocker없음. Suggestion: 없음. 본소유권review.md만추가했고다른소스/소비자료/문서를수정하지않았다. 이최종기록은동결하며root의실제최종보존감사/봉인은별도진행한다.


최종 main 추가 delta도 확인했다. [README.md:1070](/home/ajou/yigyu/3/stability_adapter_2/README.md:1070)의산출물55입력/55사본·실제그림검수/추가물리0과 [PLAN.md:1874](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1874)의완료체크2개·138영상·31검사·최종감사JSON별도기록은현재완료증거와맞다. 다음초기각정렬미실행/전체연주목표계속을명시해이번소단계완료를전체연주성공으로확대하지않는다. 추가Critical/Warning없으며이delta를포함한review를최종동결한다.
