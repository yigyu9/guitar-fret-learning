# 자연 연주 허용 구역 저장자료 재평가 독립 검수

요약 판정: **문제없음**. 요청된새analyzer/leaf/동결기준및실제저장출력만검수했다. 검수자는AST compile·소스/원자료읽기·별도rawstate/SciPy SO(3)수치대조만했고analyzer main/기존분석/native/render/actor/train을재실행하지않았다. 이review외파일수정은없다. 그림/최종문서는아직후속범위다.

## 코드·계약

- [analyze_natural_envelope.py:34](/home/ajou/yigyu/3/stability_adapter_2/analyze_natural_envelope.py:34)의정규화quaternion상대각은2atan2(vectornorm,abs(w))로부호불변최단각을계산한다. 상대회전의곱순서가달라도angle은같으며원SO(3) magnitude와맞는다. Euler축별각으로해석하지않는다. 현재저장goal은네기록exact동일이다.
- 53–69행은각1201orderedstate/trace·1200step완료·동일LA·finitepose/240Hzclock·정규화rawpose대조·trace오차·독립SO(3)·quaternion부호불변을검사한다. 실제원report의failure없음/1init/1200step도독립확인했다. 초기위치는명목goalworld norm이고회전은goal대비최단각이며각30mm/5°초과표본을집계한다. 이산sample비율을연속시간안전보증으로표시하지않는다.
- 72–78행의range480..960inclusive/stride4는start2~4초60Hz의121창이다. 각각stop=start+240이고끝점포함241표본으로시작pose대비창내최대변화를구한다. 마지막창4~5초까지완전하며창끝점차이만구하거나2초pose를모든창reference로쓰지않는다. 위치/회전peakstep을각각기록한다. 5mm/1°경계는inclusive다.
- 79–90행은각창최대값분포의p50/p95/max,전체초기구역비율을구분하고모든검사후출력한다. 비교구간2초는자료분석범위이며WAIT상태를추가하지않는다. 기존판정·report는수정하지않고동결[NATURAL_PLAYING_ENVELOPE.md](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_PLAYING_ENVELOPE.md:23)의새rolling정의를적용한다. 그threshold는임시영상검토기준이며새reward/controller가아니다.
- [NATURAL_ENVELOPE_ASSESSMENT_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_ENVELOPE_ASSESSMENT_PLAN.md:12)는complete1초창/이산표본/연속시간미보증·기존2초ref와구분·작은왼손목1축동작·양손연주일반화금지·다른환경스트랩출처미확인을명시한다. LA/root하체/몸통목표/최종66/자유G보존범위도맞다.

## 실제 완료 출력·보존·별도 수치 대조

- Analyzer SHA `1f64ed7fa138c8775d412bb905bbe54bd677fbd9159f3b3ca0d214f0e28918b3`, leaf SHA `10a4071022b10a83890c5bf844f2fb20cd0f85f19b3d131a9155630765a58f9f`, 동결기준 SHA `02d6f4e087bdf8b9d962c6e69d6ad58846cb1b5889427c0bf54f019738058edc`의소비본을검수했다. 26checks/19input전후/currentSHA,4소스·invocation사전사본 SHA,execution exit0/logSHA/3outputs SHA가맞다. 원자료를수정하거나producer를다시실행하지않았다.
- 저장body root p/q에서별도SciPy relative SO(3)방법으로초기오차및484window/4804timeline의모든값·이탈boolean·window241samples·time/step·각peakstep·p50/p95/max를독립대조했다. 위치는1e−12mm,회전은1e−10°허용오차내로일치한다. 원states와trace/4runLA도맞다.

| 기록 | 최대 초기위치 mm | 최대 초기회전 ° | 121개1초창 위치최대 mm | 121개1초창 회전최대 ° |
|---|---:|---:|---:|---:|
| original | 14.132607728 | 2.894327802 | .612804474 | .113294893 |
| joint18 | 14.084222893 | 2.920042117 | .455912001 | .084048610 |
| shoulder_minus | 15.989064226 | 2.862552945 | .700811936 | .126455159 |
| shoulder_plus | 11.926351230 | 3.169993195 | .292116157 | .052997925 |

모든기록의전체1201sample초기구역이탈0/insidefraction1.0,완전1초창121개도각잠정범위안이다. 이것은위작은이산관측의수치결과이며자연손자세·functionalplaying·fret/strike이벤트성공·연속시간보증으로승격하지않는다. 실제result의naturalness_or_playing_success_certified=false및native/physics/actor/train0이정확하다. 과거2초reference .257785610mm/.051002962°등과새창최대 .455912001mm/.084048610°등은정의가달라값차이가오류나판정소급변경을뜻하지않는다.

Critical: 없음. Warning: 미해결 코드·실제저장분석blocker 없음. Suggestion: 없음. 실제그림/manifest·최종문서표시/판정은준비후별도검수범위다.


## Artifact producer·wrapper·결정문서 최초 실행 전 검수

요약 판정: **문제없음(최초1회실행범위)**. 최종producer SHA `572a6f25e196cda0f53e6959042b34f42e8a550e0512984c64a4c1a4c352fedd`, wrapper SHA `d372950a41fee3a959eee3636f6e7b6e4d874a0fadedba35ab156eec0d11a7ab`를읽고ASTcompile/bash-n을통과했다. 현재artifact폴더에는wrapper만있다. 검수자는producer main/render를실행하지않았다. Root의최초plot1회에수치·범위blocker없음으로회신했다.

- [make_natural_envelope_artifacts.py:77](/home/ajou/yigyu/3/stability_adapter_2/make_natural_envelope_artifacts.py:77)의동결analysis19입력전후맵일치및각currentSHA대조가plot전에추가됐다. SOURCE_FILES의기준/leaf/analyzer3개와raw16개가전체19경로를포함한다. Source+raw+producer/wrapper26개를R-relativecopy/SHA로사전보존하고input전후SHA를비교한다. 실제사본/manifest/log/exit/PNG검증은실행뒤범위다.
- 32–36·92–111행의4panel은initialpositionmax/initialrotationmax/새rolling1초창positionmax/rotationmax에각30mm/5°/5mm/1°를나눈fraction이다. Threshold선은1이며절대단위값은bar옆에별도로표시한다. 16개fraction을저장값에서검산해.052998~.633999로x축0~1.1안에들어감이맞다. 작은bar를절대mm/degree축으로오해하지않도록label에fraction이있다. Run순서4개와window484행도검사한다.
- 113–119행의3독립caption줄은초기/새window기준·121starts60Hz/241samples·provisional/noncertification을명시한다. 자동wrap한줄대신명시줄과reservedbottom을사용한다. 실제PNG에서텍스트잘림/겹침이없는지는아직인증하지않는다.
- [NATURAL_ENVELOPE_ASSESSMENT_DECISION.md:14](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_ENVELOPE_ASSESSMENT_DECISION.md:14)의전체1201sample/새121window·서로다른열최대값은동시발생보장없음·이산/임시/연주미인증이맞다. Plus의새1초통계가joint18보다작고기존2초ref후기에서는약간컸다는설명은기준차이로정합하다. 모든구간/연주에서plus우월로확대하지않는다. 다음baseline-middle3−.05rad단독후보는미실행이며중지2/soft분포/sourceprofile호환/playingprior후속도남긴다. LA/root하체/몸통9/자유G/최종66권한보존범위가맞다.

Critical: 없음.

Warning(재호출보존에한정): [run_producer.sh:5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts/run_producer.sh:5)는시작부터archivedwrapper/log/execution을덮어쓸수있다. 같은wrapper를재호출하면producer의nooverwriteguard가막더라도첫실행metadata/log를먼저바꿀수있으므로미소비본에서출력/metadata부재preflight를cp/redirect전에두는것을권고했다. 현재최초1회실행에는기존기록이없고root에재실행보존범위를알렸으므로최초plotblocker는아니다. 소비후에는원형을보존하고수정/재호출하지않는다.

Suggestion: 없음. 실제그림·최종문서는생성후추가검수한다.


### Wrapper 재호출 보존 권고 해소

요약 판정: **문제없음**. 최초소비전에추가한최종wrapper SHA `b44994625c564cac385040911e05fac8e81dc65736d87173acbf1f9796e5ff26`를읽었다. 5–10행에서archived/log/execution/PNG/manifest/snapshotjson/snapshotdir부재를모두검사하고기존항목이있으면exit2하므로cp/redirect전에거부한다. 위재호출보존Warning은해소됐다. Producer572a6f25…는불변이며최종실행blocker없음. 검수자는wrapper를실행하지않았다.


## 최초 실제 artifact 완료 검수

요약 판정: **문제없음**. 실제 [natural_envelope_limits.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts/natural_envelope_limits.png) SHA `a76a0224b520e5a9a9eb52cb3f1dcc5185043fdbef08d452c9ae598a55741a79`를열어4panel/4run순서·색/16개절대값label·단위·fraction축·threshold1·3caption줄을확인했다. 모든bar/label이표시범위안이며panel/축/하단설명겹침이나잘림이없다. 실제수치반올림은독립검수한저장summary와맞고1초창정의/잠정성/자연성·연주미인증caption이명시돼있다.

Manifest26입력의전후/currentSHA와26개original→사전copySHA,producer572a6f25…전후SHA·wrapperb4499462…사전snapshot/별도archivedSHA·PNGoutputSHA·producer_execution exit0를확인했다. Metadata는command/env/exit를저장하고log는별도producer.log이며이metadata에없는logSHA필드를검증했다고주장하지않는다. Native/physics/actor/train0이맞고render/main을검수자가재실행하지않았다. 최초wrapper의재호출guard도소비된최종본에서보존돼있다.

Critical: 없음. Warning: 미해결 실제그림/보존blocker없음. 최종설명·main추가분은후속검수범위다.


## 최종 결과 문서·재사용 프레임·누적 기록 검수 및 동결

요약 판정: **문제없음**. 최종현재README SHA `bad72322a763dbb313cb839ffb54e5340acf6a845ddfcca03ae14efe97c18181`, CHANGED_FILES SHA `dda76889d772d15ad56b312780d61e620153e4bd9bdb55b9b90dcfa1f48cc8e9`, ROOT_VERIFICATION_NOTES SHA `245e59de434f0708c5afb1f7550dc3b51e4cd6c403617a1be39dcda1a8bf01ab`, 결정문서 SHA `3c470de65a1291c9343807db4adcdc95764c1987edc9e5350fb9a1932c8d4002`를읽었다. 다른phase감사나새계산실행으로검수범위를확대하지않았다.

- README의4조건×4지표16개표값을독립검수완료된실제analysis와소수6자리반올림까지대조해일치함을확인했다. Barfraction분모30/5/5/1·실제단위label·121starts2~4초/창241표본·처음pose기준maximum·기존2초ref와다름을명시한다. 전체1201sample모두임시구역안/121window모두임시유지범위안이라는관측을자연성/양손연주/연속시간인증으로승급하지않는다.
- 최종README는재사용native frame00150의simulation time5.000초와151frame/30fps MP4표기길이5.033초를정확히구분한다. 기존capture의step1200/time5.0/frame151 및video metadata를읽어일치함을확인했다. 기존start/endhands이미지·MP4를절대경로이미지문법으로재사용하고새녹화/렌더가아니라고명시한다. 기존스트랩표시와실제프레임의출처는앞선검수에서확인했으며이번과학bar그림과분리한다.
- 한국어CHANGED의producer/wrapper/26사전입력사본/manifest·실행metadata·log·분석함수34행/진입점43행·leaf·VISUAL1939 링크가맞고결과문서/rootnotes/decision의직접파일링크는모두존재한다. ROOTnotes의실제2765×1843PNG/16bars/26inputs·source572a6f25…/wrapperb4499462… 및첫실행exit0·재생성금지기록은원자료와맞다.
- Main README1045/PLAN1843/VISUAL_REPORT1939(§106)의26검사/484창4804시점·임시범위/고정LA/다른환경출처pending/새physics·actor·train0/최종66권한·자유G/몸통·root하체보존범위가같다. Plus의새1초통계우위와기존2초ref순위차이는정의차이로설명하고기존판정이나연주전체우위를소급변경하지않는다.
- 현재허용구역의수치상여유를근거로미세초기오차탐색보다손가락자세/연주접근성을우선한다는후속결정은새사용자방향과정합하다. 다음middle3−.05rad는joint18baseline에서단독변경·freshgate/실제5초를요하는미실행후보다. Middle2·손6sourceprofile호환·실제playingprior/기능·학습·새controller/reward의미완료를숨기지않고모든손가락동시접촉을새필수조건으로추가하지않는다.

Critical: 없음. Warning: 미해결 중대문제 없음(최초wrapper의재호출증거보존권고는미소비guard보완으로해소). Suggestion: 없음. 이review를최종동결하며root최종보존감사/봉인에검수blocker없음. 검수자의review외수정/main/분석/native/render/actor/train재실행은0이다.
