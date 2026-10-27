# Joint-only fixed strap 독립 검수

요약 판정: **문제없음**. 준비 출력과 수정된 v2 wrapper 기준으로 native 최초 시험을 막는 코드·입력 오류는 발견하지 않았다. 아직 이번 native 응답·완료·안정성·접촉을 인증하지 않는다. 검수자는 prepare/analyzer/wrapper main 및 native/actor/학습을 실행하지 않았고 이 검수 기록 외 파일을 수정하지 않았다.

## 검수 대상과 해결 이력

- 계획 `JOINT_ONLY_FIXED_STRAP_PLAN.md` SHA `72c890cddbe3d2193d5788e00eb42ef274123392baf739e0dd15730da228e02e`.
- 소비된 prepare 최종 SHA `cab66167f194eeca203d313d9d178e7bd04568b7e11564302363750c0839bd13`. 최초 사전 검수에서12–15행의 SHA overlay가 기존 봉인 drift를 숨길 수 있음을 지적했다. 실행 전 old input SHA 전체 사전 assert를 추가한12행을 확인했다. 기존11455 input SHA는 실제 현재 파일과 모두 일치했다.
- Wrapper v1 SHA `b6441e755fafa98d66abbe97cbfe203170faa2c9b23596f66cb7cacc2e896e7d`의26–28행은 native 입력py를 basename으로 평탄 복사하여 다른 원문을 덮어쓰는 문제가 있었다. 실제 입력의 `palm_side_feedback.py`, `fit_palm_coupled_correction.py`, `previous_search_source.py`에서 다른 SHA의 동명이인 충돌을 확인했다. V1은 preparation의3파일만 소비했으므로 그 실행의 snapshot 충돌은 없으며 원형·첫 실행묶음을 보존한다.
- 새 wrapper `run_joint_only_fixed_strap_phase_v2.py` SHA `678484f82b1ff3dcd4bc8eea580efe83c7324194175bff92ffb92ece2b8a1ac0`의28–33행은 R 상대 전체 경로를 유지하고 복사 SHA 및 원본→복사 manifest를 실행 전에 확인한다. 실제 native 입력 중py/leaf127개의 목적지가 고유하고 모두 R 하위임을 readonly로 확인했다. 이 문제는 v2에서 해결되었다.
- Analyzer `analyze_joint_only_fixed_strap.py` SHA `ad08bc079a410871ee21c47892eca55b8fe2f3b7bd47ac7fa2e0c0565a59661c`. 원본 analyzer와 diff를 읽었고 새 기준 경로/label/leaf/source closure/originalLA 체크 외 변경이 좁게 유지된다. 새 prepare/analyzer/v2wrapper의 AST compile은 통과했다.

## 준비 출력과 비교 계약

- Root의 최초 preparation 실행 exit0,4checks true, execution before/after SHA 및 로그 SHA와3개 사전복사본이 exact 일치한다. `preparation.json` SHA는 `1349ea2226ed16fd273840d5fc30b4f6f56cfbccac14e763e4390d627a765308`이다. 준비 출력11460 input SHA는 현재 파일과 전부 일치하며 proposal과 동일하다. 준비 native/physics는0이다.
- 새 trial SHA `ffb3fb69b9c26b0b30579665d8765ed2a011c3b8498481409b868f594a963f88`가 preparation/proposal과 exact이다. 이전 witness trial에 대해 LA를 되돌리면 나머지 dict 전체가 exact 일치한다. Expected initial81q/absolute81PD/source_state는 기존 witness proposal 그대로다. LA는 baseline original `1.1018469719600776m`이며 길이 탐색·장력0 강제가 아니다.
- 동일 길이의 `small_wrist_motion_v1` 원자료와 비교하여 q/유지PD가 달라지는 관절은 선택18(왼팔12+thumb/index/middle hinge6)과 exact 일치한다. 나머지63각/목표와 원left33offset·G translation·leftarm gain·기타 초기z는 동일하다. 최대 초기δ는 `0.00261649489402771rad`다. Trial의 선택18각 float32값도 expected q와 일치한다.
- Frozen native entrypoint SHA `2f6565f3e5bf79b682a5704fcbbaf5978ff925c53fd6a130a92f46e145bdd380`와 runner SHA `34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6`가 기존 proposal 봉인값과 exact이다. V2 wrapper17–18행이 이를 강제한다. Frozen runner는 trial/proposal SHA 및 closure/미인증 source지원 이유를 검증하고 fresh native source/FK/81각/PD/LA gate 뒤1200step을 진행한다. Wrist±.005rad/1Hz/5초 공통 파형을 유지한다. Hook은 실제 pose/filter의 전체 graph>2 source self 및 readonly/zero-step 검사를 추가한다. Source LP를 cooked penetration 인증으로 표시하지 않는다.
- Analyzer25–42행은 동일LA·PD/physics/G goal/names/straplaw/motion10필드, trial18만 변경, held63초기/전체1200목표, clock/waveform 및 양쪽1201states/trace·1200commands/contacts 전체 순서를 검사한다. 43–53행은1200목표 재조립과151frame readonly/604PNG SHA를 검사한다. 55–72행은 G오차·수동strap law·wrist·body9·native범위 및 body별positive rawλ step/first/last와 selfcontact를 비교한다. 이 코드는 검수자가 실행하지 않았으며 새 실제 결과의 숫자는 추후 원자료로 별도 검수해야 한다.

Critical: 해결되지 않은 항목 없음. Warning: v1 native snapshot 충돌은 원형 보존+v2로 해결됨. 현재 남은 실행 blocker 없음. 작은18변수 후보의 실패를 joint-only 안정화 일반 불가능으로 확대하지 않으며 최종66권한/연주 residual 설계와 source-profile 손6 시험 보류를 구분한다.

## 실제1200step·분석·영상 수집 원자료 검수

요약 판정: **문제없음**. 저장된 실제 실행·분석·수집과 원자료를 대조했다. 검수자는 checker/analyzer main 또는 native/physics/actor/학습을 재실행하지 않았다. Final artifact/최종 결정문서는 이번 추가 검수 범위 밖이다.

- `analysis.json` SHA `905395b94777ca3ea99eb13fc6a9dfe344edba442b448dc3befee7f8a2bb0e66`,17checks true이다. Native/analysis execution exit0, 각각11464/27개 input before=after=현재 SHA, source manifest127/8개 원본→복사 SHA, 로그 SHA가 exact이다. Report는1attempt/1init/1200step 완료·failure null이며 저장 checks가 모두true다.
- Fresh t0 전체 native state는 이전 coupled-palm-witness actual t0와 exact이다. 새 initial-grip audit 전체도 이전 witness와 exact이며14checks true, source self1188pair/intersection0, human–G/cross-hands0, palmup0.956547159다. Human66body filters는 전체 정책 reference105body 중 해당66개와 전부 exact 일치한다. 원자료 모든 human body와 proposal source_state의 FK 오차를 다시 계산하면 maxposition0.000182844156mm/maxrotation3.69268743377e−7rad로 audit와 exact이다. 기존 geometry admission은 source LP이며 cooked penetration/접촉 성공 인증으로 확대하지 않는다.
- 양쪽1201states/trace·1200controls/contacts의 step/time 전체 범위를 확인했다. 동일LA1.1018469719600776m와 공통10개 초기/물리 필드, 최초G native state, expected 초기81q/유지81PD가 맞는다. 새 trial root/lower9body는 전체1201state에서 t0 exact이다. Held63초기q 및 전체1200목표와 두 조건 clock/wrist파형이 exact이다. 새1200목표를 초기q+원left33offset+선택 wrist 파형으로 독립 재조립하여 float32 exact 및 native bounds를 확인했다.
- 실제151frame은 step0..1200/8간격/30fps이며 state readonly 표시가 모두true다. Raw+strap604PNG SHA가 전부 맞는다. 두 실제 MP4를 ffprobe로 읽어1280×720/151frames/30fps/5.033333s를 확인했다. Hands t0/end PNG를 실제 열어 original LA1.101847m 표시와 시간에 따른 실제 pose 변화를 확인했다. 캡처를 source 그림이나 pose replay로 설명하지 않는다.

### 독립 수치 재계산

Quaternion을 정규화하고 초기goal 및2초 pose에 대한 위치/회전차를 원trace에서 다시 계산했다. Strap route/velocity와 동일 수동 law로1200개 적용장력을 재계산하면 기록과 exact이다. Wrist는2~5초 actual scalar q−원static baseline의 constant/trend/1Hz fit이며 bone rotation으로 해석하지 않는다. Body9실제 coordinate 변화와 native bound 초과, 모든 human–G positive rawλ step/first/last 및 selfcontact도 원자료에서 재계산했다.

| 항목 | original-LA baseline | joint-only original-LA |
|---|---:|---:|
| 최대 초기goal 위치오차 mm |14.1326077284|14.0842228932|
| 최대 초기goal 회전오차 ° |2.8943278016|2.9200421174|
| 종료 초기goal 위치오차 mm |13.8178982321|13.7885178680|
| 종료 초기goal 회전오차 ° |2.8942190600|2.9197081386|
| 2초 대비2~5초 최대 위치변화 mm |0.4817665000|0.2577856101|
| 2초 대비2~5초 최대 회전변화 ° |0.0919291106|0.0510029623|
| 최대 수동장력 N |24.1292304763|24.6259705250|
| 종료 수동장력 N |1.8884522412|1.8967552820|
| Wrist actual1Hz fit amplitude ° |0.1469291755|0.1495259703|
| Body9 최대 실제 coordinate 변화 ° |3.5382283816|3.5386219712|
| 실제 native bound 최대 초과 rad |0.0000999495387|0.0000998452306|

후기 위치/회전 변화 감소는46.4915866714%/44.5192474729%이다. 초기 최대 위치는 작게 줄고 최대 회전은 늘었다. 초기 world G 복원과 후기 유지 결과를 분리해야 한다. 같은 길이에서 작은18각/PD후보 하나가 개선 가능성을 보였지만 G-feedback controller·연주·반복 재현성·최적화 완료는 검증하지 않았다.

| Positive rawλ body | baseline step수(first,last) | joint-only step수(first,last) |
|---|---|---|
| LH:index3 |1149(49,1200)|1154(46,1200)|
| LH:middle3 |14(29,42)|15(29,43)|
| LH:thumb3 |411(37,1059)|116(37,1038)|
| R_Hip |1200(1,1200)|1200(1,1200)|

Palm positive rawλ는 양쪽0, human selfcontact step도 양쪽0이다. 이 λ를 N이나 지속 손바닥 지지로 환산하지 않는다. Report의 `source_support_search_passed=false`와 미검증 이유를 그대로 유지해야 한다.

### 영상 수집

`collect_joint_only_fixed_strap_videos.py`11–27행은 완료1200step와 이전128개를 확인하고 새 두 MP4의 원본·복사 SHA를 대조한다. 실제 collection execution exit0/source 전후/보존본 SHA `7d1de017daa8de353c5e86485d63df1bf56a8ffd146e983943bc1714c06d8efa`, 로그 SHA, update-v5의 두 원본→복사 SHA와 size가 맞는다. VIDEO_INDEX_v5 SHA는 보존되었고 v6는 v5 전체를 suffix로 포함한다. 공유 MP4는 현재130개다. 이번 collector는 새 물리를 실행하지 않는다.

Critical: 없음. Warning: 미해결 원자료·수치·수집 오류 없음. 개선은 동일길이 단일 국소 초기18/PD 후보의 한 번 실제 시험에 한정한다. 새 artifact/결정·최종문서는 준비 후 별도 검수한다.

## 최종 v2 그림·실패 보존·문서 검수

요약 판정: **문제없음**. README의 baseline 명칭 오류와 변경색인 형식 문제는 전달 후 정정된 최종본에서 해소됨을 확인했다. 검수자는 artifact producer/분석/native/actor/학습을 재실행하지 않았고 이 검수 기록 외 파일을 수정하지 않았다.

- V2 timeseries PNG를 실제 열었다. SHA `82fd434e843fe2fcbd4f0531d807ef68b1a30717efb277ad6b98f6eeb8ab5a65`이다. Producer132–138행은 저장 `position_error_m×1000`/`rotation_error_deg`와0~5초를 그리며 두 조건과2~5초 음영을 분리한다. 축mm/degree·범례·캡션을 읽을 수 있고 선/레이블이 겹치지 않는다. Curve는 초기world기준 오차이고 표의 late 지표는2초 pose에 대한 벡터변위/quaternion상대각이므로 두 정의를 혼동하지 않는다.
- Producer SHA `227bf17db4640607b8db886d365dfb8d2a1dcde58899dbfea0f159834e8345a6`, manifest199 input before=after=현재 SHA, output PNG SHA, execution exit0/producer전후/log/output SHA, snapshot141개의 원본→복사 SHA가 모두 exact이다. 원본 saved metrics helper가 봉인된 복사본 경로에서 직접 로드되고83–89,120–122행에서 양쪽1201trace 요약을 비교한다. 이 helper의 값은 앞선 독립 원자료 검수에서 이미 별도 수학식으로 확인했다. V2 artifact native/physics/actor/training은0이다.
- 첫 artifact v1의 잘못된 요약 검산은 scalar initial-error 차를 쓰고 전체0~5초 rows에서 최대값을 구해 원분석 late metric과 달랐다. 렌더 전 exit1 및 failure traceback, 원A producer/sourcecopy SHA `a70d4fdab599c2255cd2f53d4d61bbee95b27858fd6180e6625b0db210d66ba5`, 실패log SHA와 pre-run snapshot/copy를 대조했다. V1 PNG/manifest가 없는 것을 확인했다. 첫 실패 실행의 input 전후 SHA 맵은 저장되지 않았으며 현재 snapshot 대조를 그 누락 기록의 복구 또는 실행 당시 모든 input 불변 인증으로 확대하지 않는다. V2는 새 source/새출력이고 원v1을 덮어쓰지 않았다.
- 최초 최종 README3행/표헤더가 `small_wrist_motion_v1`를 ‘−2mm 기준’으로 잘못 명명했다. 원자료는 original LA1.1018469719600776m이므로 정정 요청했고 현재 ‘기존 original LA 기준’으로 고친 본문·표를 확인했다. English/백틱경로였던 CHANGED_FILES는 한국어+절대 clickable 링크로 고친 최종본을 확인했다. 다른 소비 source/입출력은 수정하지 않았다.
- 결과 README/CHANGED_FILES/SUPPLEMENT/ROOTnotes·JOINT_ONLY_FIXED_STRAP_DECISION과 main README1001/PLAN1799/VISUAL_REPORT1858 추가분을 대조했다. 문서45개 절대 링크가 존재하고 줄번호가 유효하다. Journal-before의3main문서 prefix SHA가 보존됐다. 표 수치·46.4916/44.5192%후기 개선·초기최대회전+0.025714316° tradeoff·passive peak변화·palmλ0/selfcontact0·native 실제각 미세bound초과·singletrial/반복미검증 한계가 앞선 원자료 검수와 일치한다.
- 이번 hands 초기/종료 actual Gym PNG와 두 native MP4는 이전 CPU phase의 캡처 재사용이 아닌 이 phase의 기록이며, native1init/1200step/각151frame과 영상모음130개 설명이 맞는다. 차트는 saved-data CPU 요약으로 구분했다. 길이고정은 수동장력을0으로 만드는 것이 아니고 초기 route 길이/장력 변화가 남는다. 초기18/대응PD 변경은 Gfeedback·전체grip·연주/학습·초기worldG복원 성공으로 확대되지 않는다.
- 결정문은 후보를 fixed-LA 후기유지 후속 비교 기준으로 보존하고 스트랩 길이 탐색을 다시 열지 않는다. 최종66 공동 제어와 현재G연주+초기worldG 유지 목표를 보존하며, source-profile 손6 문제/별도fresh native admission·새leaf 필요성을 구분한다. 기존 미실행−2mm leaf를 몰래 수정하지 않는다.

최종 검수 SHA: README `afc47e2904e18223085befc70052a11de80f525e409689d4a0890d5cae97bc0f`, CHANGED_FILES `1ad500910469339336f47ff93055acf5efdfc634bcd7d568fdda16f983fee995`, 결정문 `347fa6e9580e5c5f2065c7e0de16818bda1ed9ec256e287fea2e4e635aa3729a`.

Critical: 없음. Warning: 미해결 그림·수치·문서 범위 문제 없음. 첫실패 input전후 SHA맵 미저장이라는 provenance 한계는 명시적으로 남는다. Root의 실제 최종 보존감사/봉인은 별도이다.
