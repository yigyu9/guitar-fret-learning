# 고정 LA middle3 목표 완화 준비·native 실행 전 독립 검수

요약 판정: **문제없음**. 준비코드/leaf/phasewrapper및실제완료preparation·trial/proposal을읽고별도float32조립·SHA대조만했다. 검수자는preparer/runner/main/분석/render/native/actor/train을실행하지않았고이review외파일을수정하지않았다. 실제dynamic효과·native14gate결과·1200target기록·영상은아직후속검수범위다. Root에최초native1회실행blocker없음으로회신했다.

## 소스 및 실행 계약

- Leaf SHA `96f9b6e513f0ac83ac3096ed77d0cc79343a3d2ccb1c74823884a6c068ed0e9e`
- Preparer SHA `f2fdcc51489192133d03211bebc0557c22ad9d7446833940c3bcb44dad9f411f`
- Phasewrapper SHA `72460494b5114ad03b14a708d82b326118772558f5b1650d86252ee32ae66a43`

[prepare_fixed_strap_middle_relax.py:30](/home/ajou/yigyu/3/stability_adapter_2/prepare_fixed_strap_middle_relax.py:30)는joint_only_fixed_strap의소비proposal·trial·native초기값을읽고oldchecks/전체oldinputSHA/trialSHA를확인한다. 37–39행은기존SHA경로를다른값으로덮어쓰지않는closure를확인하고새소스/leaf를추가한다. 46–55행은trialdeepcopy의LH:middle3offset만−.05rad로바꾸고이를복원하면전체원trial과exact임을검사한다. 따라서초기81q/Gp·q/LA/gain/물리/geometryfilter/source_state/다른offset의불변이전체trial대조에포함된다.

49–64행은qfloat32+원래mainoffset의float64합성후targetfloat32를unclippedexpected와대조하고other80native목표/경계·offset±.3rad를검사한다. 손목파형±.005두극값에서도clipping과offset경계를확인한다. Sourceprofile/Aug19경계를새native한계로교체하거나원initialq를바꾸지않는다. 69–74행의새row는기존geometry admission/초기state정보를유지하고expected81target 및trialSHA만신규입력에맞춘다. Support인증false/미검증이유를성공으로승급하지않는다.

[run_fixed_strap_middle_relax_phase.py:24](/home/ajou/yigyu/3/stability_adapter_2/run_fixed_strap_middle_relax_phase.py:24)는stage실행metadata/log/snapshot및nativeoutnooverwrite를유지한다. Nativeentry SHA2f6565f3…/frozenrunner SHA34d50c9f…를34–35행에서exact강제한다. 42–60행은전체inputSHA전후·Python소스/leaf의R-relative사전복사와copySHA·command/env/log/exit를보존해기존basename충돌방식을도입하지않는다. Frozenactualentry의fresh14/1188selfsourcegate뒤1200step/151frame2영상·실패partial보존계약을재사용한다. Sourcegate는cooked동적관통/해부학pad/힘N인증이아니다.

## 실제 준비 출력·독립 float32 계산

준비7checks/exit0·proposal/준비input11465SHA·wrapper11466SHA전후/current 및127개original→사전copySHA·로그SHA를전수대조해맞음을확인했다. 새trialSHA는준비/row와exact이며middle3offset을복원하면baseline전체trial과exact다. 처음입력의sourceclosure/초기LA1.1018469719600776m를보존했다.

| 항목 | 값 |
|---|---:|
| middle3 초기각(변경없음) | 60.145874019756° |
| 기존유지목표 | 1.0591416358947754rad / 60.684345643352° |
| 새float32유지목표 | 1.0091416835784912rad / 57.819559399774° |
| 실제float32delta | −0.04999995231628418rad |
| 새기준q대비middle3offset | −0.04060189723968506rad |

별도qfloat32→float64offset합성→float32조립으로새81target이proposalexpected와exact임을확인했다. 변경되지않은80목표는기존baseline과exact이며중지2/어깨·다른손가락을동시에바꾸지않는다. 세손목상태−.005/0/+.005모두nativebounds/relativeoffset±.3rad안이다. 본검사는실제1200command기록또는actualangle/접촉응답을미리인증하지않는다.

## 계획·판정 범위

[FIXED_STRAP_MIDDLE_RELAX_PLAN.md:7](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_PLAN.md:7)의기준은joint18baseline이며앞선지도plusShoulder조건과구분한다. 기존초기81/G/몸통9PD2/root하체·selfcollision/손목waveform/LA를유지하고단일middle3목표만바꾼다. 새각도기준이아니므로기존18FK인증을미인증finger1변경으로확대하지않는다. 다음실제기록에서1200other80targets/시계·middle3실제목표추종/중지2·self/palm/접촉/임시30mm5°/새121rolling1초창을비교하는검증계획이맞다.

−.05rad완화가자연성/연주성공·손가락길이인과·중지전체문제해결을보장하지않으며p01~p99는soft참고/공용hardlimit불변이다. 개선이없으면미채택·새단위후보를검토한다. LA재설정/길이탐색·기타고정/손부착/지속pose덮어쓰기·새controller/reward/actor/train을도입하지않고최종66권한/자유G를유지한다. 다른환경strap출처pending도정확히남아있다.

Critical: 없음. Warning: 미해결pre-native실행blocker없음. Suggestion: 없음. 실제native/저장분석/그림/최종문서는완료후별도검수한다.


## 새 actual analyzer·분석 wrapper 미실행 사전 검수

요약 판정: **문제없음**. [analyze_fixed_strap_middle_relax.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_fixed_strap_middle_relax.py:31) SHA `3bbb97761766c96f29ff6ad772970627874a7f2df5a428191074a99aa6223388`와분석wrapper SHA `ea385d73cf4f1c015f84efc14a2d455fe12e65841985e5640dfaf0176cbc1596`를읽고ASTcompile을통과했다. 검수자는분석main/native/render를실행하지않았다. 실제native_execution이생겼으나이단락은코드사전계약에한정하며실제수치·영상검수는후속범위다.

- 33–37행은29개직접입력(소스/leaf/helper·preparation/proposal/nativeexecution·두run각9개raw/metadata/audit)을전후SHA대조한다. Wrapper는environment와자신을추가해31paths를봉인하고10소스/helper/leaf/invocation을실행전에R-relative/externalcopy·SHA로보존한다. 명령/env/실제exit/logSHA가분리돼있다. Actualentry/runner는분석중호출하지않는다.
- 46–68행의13공통초기필드·원trial복원·other80전체1200target/clock/wrist명령·constant middle3delta·compose재구성·604새PNGhash·native14/1188gate·root하체모든state·151frame/time/readonly/2MP4hash/151frames30fps/duration이계획과맞다. 두runcoverage는1201states/trace·1200controls/contacts전체step을검사한다. Targetclipping부재는앞서준비의동일q/offset/nativebounds·손목두극값검증과같은파형/초기필드의계약을함께읽는다.
- 69–79행은rawG와tracepose를대조하고검수된angles_deg helper로121개의complete1초창을start480..960/stride4/241표본에서계산한다. 기존metrics의고정2초ref후기와별도값으로저장한다. Initial30mm/5°와rolling5mm/1°는임시범위이며naturalness_or_playing_success_certified=false를유지한다.
- 81–94행은모든actualq의nativebound초과값,rawhuman–Gpositiveλ의고유step집계/self접촉기록,각1201시점middle3실제/heldgoal 및middle2실제coordinate를저장한다. Middle3초기/.5/2/5초와2초이후최대goal오차를scalar degree로표시하며pad회전·힘N으로해석하지않는다. Body9목표/PDproperty동일검증과실제좌표완전고정을혼동하지않는다. Straplaw는검수된원helper를직접호출하고old2초ref/새window지표를구분한다.
- 95–101행은전체checks/assert후windows/joint_series/analysis를쓰므로검사실패를정상완료출력으로남기지않는다. 실제newnative1/1200step집계는reportgate와함께맞춰평가하며새actor/train0이다. 다음그림은실제분석수치검수뒤별도범위다.

Critical: 없음. Warning: 미해결첫분석실행blocker없음. Suggestion: 없음. 실제출력의입력closure/수치/모든target·이미지/영상은완료후독립대조한다.


## 완료된 실제 저장자료·영상 수집 독립 검수

요약 판정: **문제없음**. 검수자는 native·분석 main·render를 재실행하지 않고 저장 JSON/JSONL·SHA·PNG·MP4를 읽어 독립 계산했다. [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/analysis.json)의19checks/29입력closure와 native11469입력/128소스사본, analysis31입력/10사본, collection141입력/5사본은 전후 및 현재SHA·사본SHA·실제exit0·logSHA가 모두 일치한다.

- [analyze_fixed_strap_middle_relax.py:46](/home/ajou/yigyu/3/stability_adapter_2/analyze_fixed_strap_middle_relax.py:46)의13공통초기필드와 raw t0 state가 baseline과 exact다. Middle3 offset을 복원하면 trial 전체도 exact다. Other80의전체1200target과 step/command clock/update/wrist파형은 exact이며 middle3 delta는항상−0.04999995231628418rad다. qfloat32+offsetfloat64→float32를 별도로 재조립하여 두run 모든1200명령이 clipping 없이 nativebounds/원q대비±.3rad 안임을 확인했다. LA=1.1018469719600776m·원초기81/G/PD/몸통9/root하체는 유지된다.
- [analyze_fixed_strap_middle_relax.py:69](/home/ajou/yigyu/3/stability_adapter_2/analyze_fixed_strap_middle_relax.py:69)의 trace와 rawG pose가 일치한다. 독립 SciPy SO3 상대회전과 raw world 위치로 각run121개 complete1초창(start480..960/stride4/241표본) 및 고정2초ref 지표를 다시 계산했다. 전체242창/2402jointseries 행·목표/중지2실제좌표가 원자료와 일치한다. Quaternion 계산 방식에 따른 약2.1e−8°의 수치 차이만 있으며 결과해석에 영향없다.

| 지표 | 기존 joint18 baseline | middle3−.05 |
|---|---:|---:|
| 중지3 유지목표 ° | 60.6843456434 | 57.8195593998 |
| 중지3 실제5초 ° | 60.6842910018 | 57.8208503055 |
| 새1초창 최대위치 mm | .4559120014 | .4372975268 |
| 새1초창 최대회전 ° | .0840486097 | .0811468957 |
| 기존2초ref 최대위치 mm | .2577856101 | .2981385071 |
| 기존2초ref 최대회전 ° | .0510029623 | .0584584640 |
| 중지3 positive rawλ 고유step | 15 | 14 |

새1초창은 소폭개선되고 기존2초ref는 악화된다. 두run 모든1201표본은 임시initial30mm/5° 안이고 각121창은 임시rolling5mm/1° 안이다. 이는 자연스러움·연주·반복강건성 인증이 아니다. 새2초이후 최대middle3goal오차 .00131822651°도 원자료와 맞는다. 손가락 scalar 좌표를 해부학적자연성/손길이인과로 확장하지 않는다.

- 각run1init/1200step, ordered1201states/trace·1200controls/contacts, fresh14checks/1188sourcepairs·초기intersection0, root하체 모든state exact를 확인했다. Human–G positiveλ를 body별 고유step으로 직접집계해 summary와 대조했다. Palm positiveλ 없음/self기록0/violations0/palm-up proxy pass는 raw자료와 맞으며 힘N·지속pad접촉·dynamic cooked geometry 인증으로 확대하지 않는다. Actual q의 약1e−4rad nativebound초과 관측도 숨기지 않았다.
- 13점route와 점속도로 원 tension-only law를 직접 재계산해 trace의 다음step last-applied tension과 오차0을 확인했다. LA와 stiffness6000/damping120/cap300은 유지된다. CPUPhysics 및 CUDA/visualgeometry 경고는 원로그에 보존되며 본검수에서 재실행하지 않았다.
- 새capture151개 step8·time j/30·renderreadonly와604개 raw/strap PNG SHA 및 양run MP4 SHA/151frame/30fps/duration151/30을 대조했다. 새hands MP4도 별도ffprobe로1280×720/151frame/30fps/5.033333s를 확인했다. 마지막 native hands PNG를 실제열어 장면·기타·양손·기존strap route 표시가 유지됨을 확인했다. 마지막물리표본은5.000s이며 MP4duration과 구분한다.
- [collect_middle_relax_videos.py:17](/home/ajou/yigyu/3/stability_adapter_2/collect_middle_relax_videos.py:17)의 결과는 기존134개영상SHA/VIDEO_INDEX_v7 SHA를 그대로 보존하고 새두영상의원본/복사SHA를 일치시킨다. [video_collection_update_v7.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v7.json)과새VIDEO_INDEX_v8 SHA 및 실제136개count가 맞다. 소비된 collector와 실행자료는 수정하지 않았다.

[FIXED_STRAP_MIDDLE_RELAX_DECISION.md:22](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_DECISION.md:22)는 새1초창개선/고정2초ref악화·임시기준·singletrial·목표만변경/초기각동일을 정확히 구분한다. 28–32행의 후보유지는 자연성/연주성공 채택으로 확장되지 않으며 다음baseline대비총−.15rad는 미실행 제안이다. 중지2·어깨 동시변경, sourceprofile/실제hardlimit교체, actor/train 또는 strap조정이 이번실행에 포함되지 않는다.

Critical: 없음. Warning: 미해결 실제자료·수집 blocker없음. Suggestion: 없음. 최종그림·README/main추가문서는 후속범위다.

## 그림 producer·wrapper 실행 전 검수

요약 판정: **문제없음**. [make_middle_relax_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_middle_relax_artifacts.py) SHA `ef9d4244c3b00e60561bb5d71ecfab64bb69ddc5acd2c659ee8c1b40ec869ff9`와 [run_producer.sh](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/run_producer.sh) SHA `c5975cee91716b2d7bafa750d2b773c590ac501c5a5cdaafb56859ba911a7266`를 읽었다. 검수자는 producer를 실행하지 않았다.

19checks/29consumed-input SHA closure를 실제현재입력과 대조한후 snapshot을 복사하고 plot한다. 2402jointrow/242window·각121count/summary목표·5초sample·windowmax·passcount가 연결돼있다. 실패결과를 모두pass로 강제하는 gate는없다. 좌측solid actual/dashed heldgoal과 우측fraction-of-provisional-limit dashed1을 캡션에서 구분하며 mm/degree를 각5mm/1°로 정규화한다. 오른쪽 ylim은y3.58 group label을 포함하고 좌측legend는center right에있다. 3줄캡션·하단여백이 명시돼있으나 실제겹침여부는 PNG생성후판정한다. Wrapper가 기존log/manifest/snapshot/PNG/execution/자신의archive를 사전거부하고 producer의logguard는 shellredirect와 충돌하지않는다. 명령/env/exit/logSHA/입력전후SHA/출력SHA 기록과 native/physics/actor/train0 범위가 맞다.

Critical: 없음. Warning: 미해결 첫그림실행 blocker없음. Suggestion: 없음. 실제PNG·manifest·최종문서는 아직 검수완료로 표시하지 않는다.


## 최종 실제 그림·문서 검수 및 검수 기록 동결

요약 판정: **문제없음**. [middle_relax_native_summary.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/middle_relax_native_summary.png)를 실제열어 확인했다. SHA `e90bd8825fc237d9f76783f72c38e12fa0fd979c93d8347cb263bd94362a1fe9`이며 저장원자료 후처리 그림이다. Native 렌더와 구분된다. 검수자는 그림·분석·물리를 재실행하지 않았다.

- 좌측0~5초 두actual곡선/두constantgoal과4개범례가 raw검수된2402jointrow의방향·시작각·57.819559/60.684346° 목표에 맞다. 범례는곡선·목표선을가리지않는다. 우측4막대의표기 .456/.437mm 및 .084/.081°는 원summary를3소수점으로표시한값이고 길이는각5mm/1°로나눈비율이다. 임시한계x=1과좌측목표점선은3줄캡션에서구분된다. 두panel제목·단위·group label·축·캡션은겹치거나잘리지않는다. 창121개/241표본/2~4초60Hz시작과자연성·연주미인증표시도맞다.
- [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/artifact_manifest.json)의43입력전후SHA는같고현재파일과도일치한다. [source_snapshot.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/source_snapshot.json)의43사본은원본path→SHA목록전체와같고사본byte SHA도모두일치한다. Producer ef9d4244…/wrapper c5975cee…는사전검수본과같으며wrapper원본/archived byte SHA도같다. Producer_execution의exit0·명령/env·logSHA·입력전후/producer/출력SHA가manifest와일치하며 artifact중native/physics/actor/train은모두0이다.
- 최종 [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/README.md)의목표·5초actual·initialnominal오차·새1초/기존2초table는독립검수수치와같다. 같은초기81/G/LA와other80유지를명시하고1초창개선/2초ref악화·임시기준·p99softreference·중지2유지·실제연주/sourceprofile미검증을구분한다. 원native2MP4/시작·끝PNG를절대경로embed하고새overlay/새녹화로설명하지않는다. Simulation5.000초와MP4duration5.033333초도정확히구분한다. 다음total−.15rad는미실행제안이다.
- [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/CHANGED_FILES.md)와[ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/ROOT_VERIFICATION_NOTES.md)의현재로컬링크는실재한다. Native1회와후처리0회추가물리,각stage입력/사본수,CPUPhysX경고보존,136영상,rawλ≠힘N/sourcegate≠dynamiccooked인증,작은actualbound초과관측을숨기지않는다. Root의이전봉인파일150개보존감사는root후속범위이며본검수에서그이전phase전수재감사를했다고주장하지않는다.
- Main [README.md:1050](/home/ajou/yigyu/3/stability_adapter_2/README.md:1050)/[완료기록:1055](/home/ajou/yigyu/3/stability_adapter_2/README.md:1055), [PLAN.md:1848](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1848)/[완료기록:1853](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1853), [VISUAL_REPORT.md:1952](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1952)의새추가분은결정/실제raw/그림과정합한다. 준비기록과완료기록이시간순추가이며초기각변경으로잘못설명하지않는다. 최종66권한/root하체고정/몸통목표/자유G/고정LA,다른환경출처pending,actor/train미실행범위가유지된다.

최종 문서 SHA:

| 파일 | SHA256 |
|---|---|
| 결과README | `0344c10ca764c44ab686b253b07163d329fad61b8f6ba778c760225e9487ebb0` |
| CHANGED_FILES | `03d7ba6c7d3e229887a16439240681bfba137dac20b6f90be1a2a6d044ab4ab4` |
| ROOT_VERIFICATION_NOTES | `1668c05a5677e0dbe383fdaab8277e5b619bbe077abf14782c4c7b3bb2359138` |

Critical: 없음. Warning: 미해결 최종봉인 blocker없음. Suggestion: 없음. 검수소유권인 이 review.md만 추가했으며다른소스·소비자료·문서는수정하지않았다. 이최종검수기록을동결하며root의실제보존감사/봉인은별도진행한다.
