# 저장 손가락·접촉 지도 코드 및 출력 독립 검수

요약 판정: **수정 권장**. 좌표관측·실제저장출력에중대오류는없으나single_substep검사의근거표현을보완해야한다. 검수자는소스읽기/AST compile/저장원자료의별도NumPy·SciPy계산만했고main/native/actor/훈련/기존phase분석을실행하지않았다. 소유권은이review뿐이다. 첫사전검수중root가source-only실행을완료했으므로소비본은보존하고보완은별도기록/새출력으로진행해야한다.

## Critical

없음.

## Warning

- [analyze_finger_contact_map.py:29](/home/ajou/yigyu/3/stability_adapter_2/analyze_finger_contact_map.py:29): `initial['physics_parameters'].get('substeps',1)==1`은실제initial_values에없는키를1로처리해single_substep=true를남긴다. 실제키는position_iterations/velocity_iterations/leg_kp_scale/leg_kd_scale뿐이다. Native SimParams readback인증이아니므로configured source의기본값근거와미조회한계를명시해야한다. [environment.py:52](/home/ajou/yigyu/3/stability_adapter_2/environment.py:52)의동일default1설정을읽었고현재SHA는 `9718c894a36607274d70b7c10d8d915b3f118a7eaf3c2c4bfe13d71bccd4944f`다. 이파일은현재분석17입력SHA맵에는없으므로configured/native구분및근거source보존을별도보완하는것을권고했다. Poststep수치관측자체를폐기하거나기존소비소스를고치라는지적이아니다.

## Suggestion

- [analyze_finger_contact_map.py:59](/home/ajou/yigyu/3/stability_adapter_2/analyze_finger_contact_map.py:59): allchecks assert가features/analysis쓰기뒤에있다. 미래새버전에서는쓰기전에검사하면실패검사값을포함한출력을먼저남기는순서를피할수있다. 현재실제12checks는모두true이며현재출력실패를주장하지않는다. 소비본을수정하지않는다.

## 확인한 정확성·범위

- Producer SHA `9b1d8751898598f5399529313ba1e8b20cf1b27368d610bcc0955add053c512b`, plan SHA `1a83c4584a2011eda5c6a2e20e8e1e44cdcf3c68e22a69fda29e4076f540d5bf`를읽고AST compile을확인했다. 실제analysis12checks/17입력전후/current SHA,execution exit0·6소스/외부invocation사전사본SHA·로그SHA가맞다. 새native/physics/actor/train0이며기존이미지·PD·LA를변경하지않는다.
- 전체1198positiveLH raw접촉행(thumb3 9/index3 1145/middle3 44)의actor/body이름·native ID를독립대조했다. Human/guitar bodyorigin poststep pose로feature를world로복원한뒤Grootlocal로변환한양쪽좌표를모든1198행에서재계산해1e−15m허용오차안에맞음을확인했다. Bodyorigin재구성일치는nativeCOM질의/해부학pad인증이아니다.
- Post pair최대잔차 .0000820329349455mm(<1µm),pre pair최대 .639182476361mm,pre/post기타feature이동최대 .540073450540mm,world↔G roundtrip≤6.20634e−17m이다. 두offset은관측전체0이다. SDKfeature간잔차를cooked표면간격/관통깊이로읽지않으며zerooffset이표면인증을주지않는다. SDK normal 부호와반대부호의문제는이전helper와같이geometry-only지표로읽어야하며힘방향 gate가아니다.
- Finger3별고유positive step은thumb9/index1145/middle18/ring0/pinky0으로직전진단과맞다. Middle의44contact행은18step에걸친여러행이며44step으로혼동하지않는다. 각지정reference guide near2mm rows는thumb5(thumb후면)/index1135(front_outer)/middle44(front_outer)이고이는finite referencepolygon의projection·planedistance관측이지실제해부학pad/cookedface의인증이아니다.
- 네snapshot step0/32/56/1200의현재positivefeature수는각0/2/0/1이다. 특히56은index첫positive54이후여도현재기록0이며그림에서과거접촉을현재접촉으로표시하지않아야한다. Snapshot currentfeature목록과features.jsonl의같은step집합은exact다. Frame step/time/read-only·기존hands이미지SHA검사도맞다.
- 1→2→3→top은저장nativebody원점체인이다. 네시점선분길이합은thumb116.764805~116.764880/index88.473373~88.473452/middle99.640394~99.640469/ring92.472066~92.472125/pinky71.841875~71.841928mm로독립world원점차이와맞다. 이는bone표면/손끝pad/새FK예측이나각도필수성의근거가아니다.
- [FINGER_CONTACT_MAP_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_PLAN.md:8)의G-local유한guide/원neck9.3mm와sourceouter11.230006mm분리·현재SDKfeature/손끝원점후보분리·원nativePNG보존·별도과학지도/저장depth부재·표시≠제어범위는정합하다. 최종66권한/자유G/root하체/몸통목표·LA고정도유지한다. 길이필수/자연자세/초기G복원/연주성공으로확대하지않는다.

실제새과학PNG와최종문서는아직검수범위에없다. 위substep근거표현보완후그림/문서가준비되면그범위만추가검수한다.


## single_substep 근거 표현 별도 보완 검수 — Warning 해소

요약 판정: **문제없음**. 위 Warning은원본analysis/source를수정하지않고추가한 [configuration_clarification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/configuration_clarification.json:1)의명시적보완으로해소됐다. 원본single_substep=true를native readback인증으로읽지않는다.

- [verify_finger_map_configuration.py:9](/home/ajou/yigyu/3/stability_adapter_2/verify_finger_map_configuration.py:9)의AST검증을읽고별도AST parse/literal평가로확인했다. 소비native initial SHA와environment/presets/fixed/self/camera5소스의현재SHA가exact이며, environment의substeps getterdefault1 할당이정확히1개다. 저장physics dict는baseline preset과exact이고substeps키가실제로없다. 따라서configured sourcedefault1의근거는확인됐지만native SimParams값을조회한것은아니다.
- 보완출력의5checks/8입력전후/currentSHA,별도execution exit0·11사전소스/외부invocation사본SHA·로그SHA가모두맞다. 보완소스SHA는 `78686a1e39beb1938826be32c8e284682aa40ad53a2fb5f16eab84426de8c42f`이며ASTcompile도통과했다. 기존analyzer9b1d8751…와analysis6b38c85d…의소비본SHA는불변이다. 새main/analysis/native를검수자가실행하지않았고보완단계native/physics0이다.
- `supersedes_analysis_check='single_substep'`, configured_substeps_from_consumed_source=1, saved_physics_parameters_contains_substeps=false, native_SimParams_readback_performed=false의구분이정확하다. Poststepfeature pair잔차는별도수치관측으로남으며COM/실제cooked면/힘방향인증으로승급하지않는다.

Critical: 없음. Warning: 미해결 해당Warning 없음. 위쓰기전assert권고는다음미소비버전의선택적순서보완이며현재저장12checks true결과를무효화하지않는다. 과학PNG·최종문서검수는후속범위다.


## 과학 지도 producer·wrapper·결정문서 미실행 사전 검수

요약 판정: **문제없음**. [make_finger_contact_map_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_finger_contact_map_artifacts.py:114) SHA `47e5c89991feb677b9d2cc8f0bde5ec1dca5c3d67c5953dd48c4debaf263f74b`의미소비최종보완본을읽었다. Python3.8 AST compile과shellwrapper bash-n을통과했고AST로분리한verify_analysis pure함수만저장입력에적용해현재계약통과를확인했다. Render/producer main/native/actor/train을실행하지않았다. Artifact폴더는사전wrapper만있으며실제PNG의가독성/수치QA는아직인증하지않는다.

- 114–133행은analysis/config원입력에SOURCE_FILES전체original과19개사본·source_snapshot.json·외부invocation·폰트·decision_inputs·실행metadata/log를포함해SHA를봉인한다. 86–111행은이전소비manifest간SHA합의와original→R-relative/external copy exact를확인하고plot전에producer와shellwrapper원문을보존한다. No-overwrite/사전wrapper만존재하는폴더조건·입력전후·producer/wrapper전후SHA및scope native/physics/actor/train0이맞다. 실제manifest/copy개수/실행log/exit는생성후검수범위다.
- 136–168행은원analysis의single_substep을독립근거로사용하지않고별도clarification의5checks/configured1/native readbackfalse/savedkeyfalse로대체한다. 실제17원입력/1198feature/4snapshot/current0·2·0·1 gate도기존자료와맞는다. 전체1198점을각panel에누적현재점으로그리지않고해당step의현재점만선택한다.
- 186–275행은Glocal좌표×1000mm,저장1/2/3/top body원점체인·top빈삼각형·finger별색과top옆이름1개·현재λ>0 feature점·유한guide를2×2별도Matplotlib3D도표로표시한다. NativePNG를수정하지않고원점체인을pad로부르지않는다. Frame32의2row가같은finger라도row수와고유step을혼동하지않는다. Front9.3mm/outer11.230006mm/thumb−8mm/palmside guide를구분하고cooked면/깊이가림·힘/제어constraint로인증하지않는다. Axis는모든chain/guide/현재feature를포함하는범위를공통으로사용하고실제길이비의boxaspect/orthographic를설정한다. 아직실제label·범례·caption겹침통과는아니다.
- Wrapper SHA `fdda92974b798e573534c1f440e8e47650f9f2158434ff5db053e43780fef0da`는고정Python/MPL환경으로savedproducer를호출하고실제status/log를보존한다. Root요청의SOURCE_FILES원입력누락/불필요math/과도한jointtext는미소비본에서해소됐다. 기존소비소스/원자료/그림을편집하지않는다.
- [FINGER_CONTACT_MAP_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_DECISION.md:15)의원점체인길이참고·중지44행/18step·step56현재0 및5초index topGZ15.080769924mm/SDKfeature9.294778109mm 구분을저장값과대조했다. Top을pad로보고목표면까지직접움직이지않는한계가맞다. 8월19일정리.txt middle3관측p01~p99=1.4~46.1°/제안hardlimit−5~60°와별도renderJSON 약−5~90°를직접읽었고현재native한계로교체하지않음을확인했다.
- 결정32–44행의후속middle3목표−.05rad는같은LA의joint_only_fixed_strap baseline으로돌아가는별도미실행후보다. 지도조건plusShoulder와연속실행으로연결하지않고기존초기q는유지·목표만수정후freshgate/실제5초를별도로검증한다. 60.684→57.820°는수치상맞지만자연스러움/지지·초기G복원개선을보장하지않는다. LA/자유G/root하체/몸통9/최종66권한보존도정합하다.

Critical: 없음. Warning: 미해결 producer실행blocker 없음. Suggestion: 없음. 실제그림·최종문서·manifest출력검수는생성후별도범위다.


## 실제 과학 PNG·manifest 완료 검수

요약 판정: **문제없음**. 최초producer실행전마지막미소비변경은finger별label fontsize7.5→8.5이며최종소비SHA는 `4818018a912215bfaacc7ba800e9a2ceb553c1baf72d7169fb96b2ab500f0b30`이다. 앞서읽은47e5c899… 사전본과구분한다. Root가실행했고검수자는어떤render/analysis/native도재실행하지않았다.

- 실제 [finger_contact_map_snapshots.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/finger_contact_map_snapshots.png) SHA `06cff6af9ca45637208cb58ce6373c0b2c0c7b08e9099b6781bbfc903ef43c3c`를열어2×2의step0/32/56/1200·0/.133/.233/5초·현재point수0/2/0/1·5finger별색/이름/top빈삼각형·mmGlocal좌표·동일축범위·guide높이구분을확인했다. 그림은저장body원점지도이며native렌더위overlay가아니다. 별도원native이미지표시는최종문서범위다.
- 실제범례의body origins/current SDKfeature/front9.3mm/frontouter11.230006mm/thumb−8mm/palmside와하단caption이원자료/코드범위에맞다. 범례·caption은panel/축과분리되어읽히며5finger라벨을20jointtext로늘리지않았다. Step32의두middle3feature좌표는약.864mm떨어져저해상도에서겹쳐보일수있지만두실제행을표시하고title의count2가맞다. Step56은현재0이고과거index접촉을현재점으로그리지않는다.
- Manifest62입력전후/currentSHA·19개original→사전snapshot SHA·producer와wrapper SHA전후/current·producer_execution exit0/logSHA·단일PNG outputSHA를전수확인했다. Shellwrapper fdda9297…도사전사본에포함됐고실제command/envmetadata가있다. Native/physics/actor/train0 및configuration보완의supersedes single_substep/configured1/native readbackfalse가manifest에명시돼있다.

Critical: 없음. Warning: 미해결 그림·보존중대문제 없음. Suggestion: 없음. 최종한국어설명문서/main추가분은아직전달전이므로후속검수범위로남긴다.


## 최종 한국어 문서·재사용 native 이미지·main 추가분 검수 및 동결

요약 판정: **문제없음**. README SHA `5b582f5e036c24e21f0798c638d4e94c388f1e0dc0c3053e51d764f49a8b2cd8`, CHANGED_FILES SHA `6855050f6f6f928bf38c600b58d11bf577b3bb8e57b6e5cfbd191a292751d271`, ROOT_VERIFICATION_NOTES SHA `ad446b7e4db281996b0f30c450563a67a5cdc60ccb7c193d12e5195b91c9186c`의최종현재본을읽었다. 해당추가범위만검수했고이전봉인phase감사를확대반복하지않았다.

- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/README.md:1)의4snapshot/current0·2·0·1·body원점선/top빈삼각형·현재feature검정테두리점·mmGlocal·9.3/11.230006/−8mm guide구분이실제PNG와분석에맞다. SDKpost pair잔차 .0000820329349mm/pre .639182476mm/왕복6.2e−17m/offset0·chain99.6404/88.4734mm도기존독립재계산과일치한다.
- 5초index top_G mm= [−16.301807400,97.518866640,15.080769924],실제guitarfeature=[−16.186669469,97.109988332,9.294778109]의문서반올림을대조했다. 두점의Euclidean거리5.801563540mm도root/main의약5.80mm와맞다. 원점/SDKfeature/cooked표면/해부학pad를혼동하거나그차이를표면gap으로부르지않는다.
- README의4개hands원본00000/00004/00007/00150은step0/32/56/1200 및8step/frame과일치한다. 추가로32/56시점원nativePNG도실제로열어비교했고시작/5초이미지는앞선검수에서열었다. 과학도표와기존native프레임재사용/픽셀불변/overlay미추가·depth가림미인증이정확히설명됐다. 새native영상/physics/actor/train0이며기존134영상모음은유지된다.
- Configuration보완이최초single_substep을대체함을README/rootnotes/producer가명시하고source설정1과native readbackfalse/savedkey부재를구분한다. 현재원자료bodyorigin변환수치관측이nativeCOM/cooked관통깊이/힘N인증으로확대되지않는다.
- CHANGED_FILES의한국어설명·절대클릭링크·producer/wrapper/19원문사전사본/62입력전후SHA/실제zero-call scope가맞고3문서의모든직접파일링크가존재한다. 소스에없는영상overlay/pad인증/새물리·목표변경을산출물로표시하지않는다.
- Main README1033/PLAN1831 및VISUAL_REPORT1915(§104)의1198행/current수/chain길이/약5.8mm구분·수치·새physics0·134영상유지·후속middle3−.05rad미실행범위가같다. Rootnotes의다음단위는지도조건plusShoulder와joint_onlybaseline을구분하고새초기q변경없이단일목표만변경하는미실행시험으로기록됐다. 앞선Aug19자료의p99/제안limit/별도render범위도현재native한계와혼동하지않는다. 표시만으로자연성을달성했다고하지않고soft분포·접근/실제접촉평가와별도freshgate/5초를남겨둔결정이정합하다.

Critical: 없음. Warning: 미해결 중대문제 없음(최초substeps표현은위별도보완으로해소). Suggestion: 미래미소비버전의쓰기전assert순서권고만유지하며현재완료phase의봉인blocker는아니다. 이review를동결하며root의최종보존감사/봉인에검수blocker없음. 검수자가review외파일을수정하거나main/render/native/actor/train을실행한횟수는0이다.


### 최종 문서 소폭 수정 대조 후 재동결

요약 판정: **문제없음**. 최종README SHA `3c0b663d4191f3d3488c76277364a8e6bc9dad34cd9f9edf67b53cf4517860ee`, CHANGED_FILES SHA `179d63a5895a137d4f15a6ec7c67c437f0ad5838834de9fbe2273ea0e22f294f`를확인했다. README11행은기존스트랩경로표시가유지되고이번새접촉점overlay는추가하지않았다고정확히구분한다. 앞선검수문구의overlay미추가도이번접촉점overlay미추가라는범위로읽는다. CHANGED13행에추가된mainREADME1033/PLAN1831/VISUAL_REPORT1915링크는위에서검수한실제추가분을가리킨다. 물리/원자료/producer/그림은불변이고이소폭문서수정은수치·해석판정을바꾸지않는다. 최종검수문제없음/봉인blocker없음으로review를다시동결한다.
