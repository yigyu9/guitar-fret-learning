# Quiet 검지 목표 응답 사전 검수

요약 판정: **문제없음(PASS, 사전 코드·입력·수치 계약 범위)**. 사전 입력 closure의 실제 import 누락 한 건을 root에 통지했고, 미소비 wrapper 보완 뒤 해결을 확인했다. 이 review.md만 생성하며 원800평가 phase의 동결 review·원본 소스·타인 파일을 수정하지 않는다. Native/actor/훈련/solver/분석/그림/감사 main 및 새 runner/wrapper main을 실행하지 않았다. 실제 초기gate·상태prefix·PD응답·5초 성능은 아직 검수 대상이 아니다.

- [계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md:13)과 [실행leaf:3](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_SUPPORT_EXECUTION.md:3)는 initial_middle3_alignment_v1 quiet 실제초기81·원offset/held·Gfullstate/LA/PD/body9/root하체·손목파형을 유지한다. 원trial을 새변형 없이 읽으며 [runner:26](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support.py:26)는 baseline input_trial과 exact 대조한다. index3 initial.12326771765947342rad/held.1394716501235962rad가 원자료와 일치한다. 통계 source profile은 이번 PD진단의 필수초기조건에서 분리하되 실제native한계/초기source형상과 actorqualification은 별개다. Policy 추론·학습을 우회 시작하는 코드가 아니다.
- [원runner 복제본](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support.py:19)을 frozen wrist runner와 diff로 대조했다. 새 입력manifest/원quiet 대조·index명령·직접gate/명확한scope 외에 원240Hz/60Hz관측·스트랩·촬영·body9PD×2/√2·rootlower·조회readonly 루프가 유지된다. [fresh direct gate:93](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support.py:93)는 기존 run_source_hand_initial.audit_initial을 직접 호출하며 빈 search/row를 전달해 예전 FK source_state를 사용하지 않는다. Native human/G filterreadback·전체HG/별도cross/self1188/palmup/rootlower/Gfullstate/PD/66권한·0step/read-only와 baseline실제q81/nativebound·initialPD target/LA를 검사한 뒤에만 적분한다. 초기상태 쓰기는 기존 초기화 경로뿐이고 이후 pose/state 재생·기타복원힘/손부착을 추가하지 않는다.
- [목표 합성:106](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support.py:106)은 원66offset에 Wrist_x ±.005rad·1Hz를 그대로 더한 unperturbed를 먼저 조립하고, index3 ±.005rad를 command_time2..2.5초 ramp/이후plateau로 더한다. Nativefloat32 bounds 및 offset±.3 검사를 수행하는 compose를 사용하고 clipping하지 않는다. [other80:114](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support.py:114)는 index3을 제외한80목표가 원wrist 포함 baseline과 exact인지 검사한다. 매physicsstep 최종81target/clock/updateflag/delta를 기록해 60Hz명령과240Hz held를 분리한다. Submit/query state보존·PD/rootlower 검사는 원루프대로다.
- 검수자가 원quiet의 **1200×81 저장명령**과 rawinitial/원offset/PDnativebounds를 사용해 두 조건을 독립 NumPy 재조립했다. 양쪽 모두 다른80 exact·t≤2초 전체81목표 exact·native범위/offset±.3 통과다. 첫 실제차이 physics_step485(command_time2.016666…초)부터1200까지 **각716개** 명령이다. t=2초 갱신은 보정0이며 t=2.5초부터 plateau다. Index3 목표범위는 **plus .1394716501235962.. .1444716453552246**, **minus .13447165489196777.. .1394716501235962rad**다. 요청±.005와 실제float32목표차이를 구분해야 한다. 이는 명령조립 검산이며 실제state/trace prefixexact나 접촉반응을 미리 인증하지 않는다.
- **발견·해결한 사전보존 blocker:** 최초 wrapper의 relative ImportFrom 전용 추적은 실제 module-level `palm_side_feedback→search_palm_neck_side→render_best_run_video:16`의 absolute `stability_adapter_2.plot_joint_hold` import를 누락했다. [최종 wrapper:34](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_phase.py:34)는 plot_joint_hold.py·package __init__.py를 명시 포함하고, [absolute import 재귀추적:46](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_phase.py:46)도 추가했다. 독립 AST 재열거 결과 **41개 local .py**(plot_physx_contacts의 함수내 import도 보수적 포함)를 수집하며 누락을 해결했다. 최초누락본은 미소비였고 root가 수정했으며 검수자가 코드를 고치지 않았다.
- [wrapper 입력:32](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_phase.py:32)의 실제baseline/report·sealedinventory·trial·계획/leaf·config·fixedlower manifest/입력·기하context자료/policy/proxy·공용자산/mesh/font·local소스를 독립 열거했다. **102원입력**이 모두 존재하고 baseline입력map과 겹치는 현재SHA가 exact, fixedlower manifest의5입력SHA도 exact다. 실행시 새 condition_inputs.json을 추가해 **103입력/사본 예상**이다. 파일수는 현재코드·파일목록의 사전관측치이며 실제실행metadata에서 다시 확인해야 한다. 원quiet proposal의14,015 ancestry map을 새runner가 읽지 않으므로 재귀 복사하지 않는 범위가 명확하다. 이전봉인자료를 삭제하거나 숫자/source/actor gate를 통과한 것으로 대체하지 않는다.
- [재실행 거부:26](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_phase.py:26)는 각condition의 log/input/invocation/execution/native 경로가 있으면 중단한다. 사전입력SHA/사본/invocation 후 단한child를 실행하고 전후SHA/닫힌log/실제exit·terminal을 보존한다. [runner:130](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support.py:130)의 오류/SIGTERM은 실패·실제step/frame·가능한partial을 기록하며 자동재시작하지 않는다. Gate거절0step partial과 통과한같은init1200step/151frame/두영상 조건을 분리한다. 두trial을 연속10초로 해석하지 않으며 report의stability_success는None/diagnostic_only다. Runtime	actualstateprefix/접촉/6×1유한응답과 최종미디어는 이후 별도 검수해야 한다.

Python3.8 AST PASS 및 최종 SHA-256:

- run_quiet_index_support.py: `05890fccb5b77b42398db2745afcbb4c5b5b5af2cd3d25cc1f7bef89445a0fb2`
- run_quiet_index_support_phase.py: `9f147652dcbfb09dac0c681b5fff885b5303726200b49a9ca987b767318142e6`
- QUIET_INDEX_SUPPORT_EXECUTION.md: `3d581ec18ddf7e4c25d9163c67e5591b42f3c830fe0ccc69a27b1135d4bf63d5`
- QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md: `4d63ada7d48f5102fc246a3d50de5dcb5ba1aa2dec3c5de6e881bc585d966550`

현재 소스의 사전 실행 blocker는 없다. 사전 검수 판정: PASS. 실제 native 실행·분석·산출물 검수는 별도 후속 범위다.

## 미실행 saved analyzer 사전 검수

요약 판정: **문제없음(PASS, analyzer 코드 사전 범위)**. analyzer main/실제분석/추가native/ffprobe/renderer/solver를 실행하지 않았다. 현재 진행 중인 native에 개입하지 않았으며 실제 plus/minus 결과·보존자료·상태prefix/접촉·6×1응답 판정은 완료 후 별도 검수한다.

- [완결성:41](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:41)는 baseline/plus/minus 각각 completed·failure없음·1200steps/5초·reportchecks, states/trace1201·controls/contacts1200·orderedstep/time을 요구한다. [공통field:34](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:34)는 정확히20개이며 actual초기각/PD/nativefullstate/Ggoal·LA/physics/원trial/offset/몸통9·권한 등 baseline동일성을 검사한다. [prefix:82](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:82)는0..2초 state/trace481개, [명령:84](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:84)는 첫484개 전체81목표와 모든1200의 다른80·원clock/wrist/updateflag를 대조한다. Prefix가 실제 exact인지 여부는 저장결과가 갖춰진 뒤에만 판정한다.
- [ramp 재계산:86](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:86)은 실제원초기index3+원offset±.005의2..2.5초 ramp→float32목표를 independent 조립하고 全1200native목표bounds를 검사한다. Runner의 q+(offset+delta)와 analyzer의 q+offset+delta 산술순서를 원quiet commandtime으로 두조건1200개씩 독립 비교해 **float32 차이0**을 확인했다. 초기fresh15와 self count1188은 [audit:88](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:88)에서 검사한다. 이1188은 self쌍이며 양손검사는 directgate의 별도 bool이다.
- [원pose 대조:46](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:46)는 raw native Gpose와 trace, quaternion±동치/정규화 및 초기goal position/rotation오차를 비교한다. [후기창:52](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:52)은 2..4초 시작을4physicsstep간격(60Hz)으로 총121개, 각241sample/1초 완전창으로 계산한다. 기존2초 단일참조변화와 구별한다. [rawλ집계:54](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:54)는 human–G 양의λ가 있는 body를 step마다set으로 중복제거해 세며 actual force closure·지지력 인증으로 해석하지 않는다. Native bound 초과량도0으로 강제하지 않고 관측값을 summary에 남긴다.
- [t5 응답:91](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:91)은 각조건 world위치−동일baseline t5위치, Log(q_condition·q_baseline⁻¹)의 world회전을 구한다. [중앙 차이:94](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:94)는 plus−minus를 **.01 nominal rad**로 나눠6×1과 m/rad·rad/rad 단위를 명시한다. 실제float32목표span과 nominal입력span을 구분하며 범용Jacobian/66rank/안정feedbackgain 인증은 아니다. 제어목표와 실제상태의 PD오차를 대응physicsstep으로 계산한다. Series의 state/time은1201개, target은1200개(controlstep1..1200)이므로 후속그림에서도 해당시간을 맞춰 사용해야 한다.
- [capture/video:72](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:72)는 각run151frame/step8간격/route·LA·renderreadonly, raw/overlay **604 PNG SHA**, 두뷰151frame/30fps/151÷30초·저장ffmpeg/ffprobeexit 및 현재videoSHA를 검사한다. 이는 저장probe metadata/currentbytes 대조이며 analyzer가 새render/ffprobe를 실행하는 코드가 아니다. [실행입력 검증:80](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:80)는 실제native exit0/completed·before/after/current입력·닫힌logSHA를 확인하고 [끝검사:96](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:96)는 직접 소비원자료/media SHA가 불변인지 검사한다. Snapshot/invocation/외부 실행기록의 최종 완결성은 root의 실행 wrapper 및 저장자료 후속 검수에서 확인해야 한다.
- [결과scope:98](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support.py:98)의 physical_initializations2/physical_steps2400은 비교하는 두새native trial 합계이며 analyzer 자체의 새물리실행이 아니다. Scope는 저장응답·contact-dependent finite response 및 no simulation을 분명히 한다. Actor/train0, 전역Jacobian/feedbackgain미인증을 유지하고, 최종assert 전에 모든checks를 수집하며 기존analysis.json이 있으면 덮어쓰지 않는다. 실제 실패/partial을 성공분석으로 바꾸는 경로는 없다.

Python3.8 AST PASS, analyze_quiet_index_support.py SHA-256: `86aa526cbb5be4339b8017c1d0265b31798930e8177bef923561eea55ad4bd75`.

Analyzer 사전 검수 판정: PASS. 실제원자료/출력·산출물 최종판정은 아직 수행하지 않았다.


## minus 최초 실행 SIGSEGV 저장자료 검수

요약 판정: **실패 원자료 보존·초기 prefix 대조는 문제없음. 두조건 응답분석은 보류**. 기존 사전 코드 PASS는 실제 실행 성공을 뜻하지 않으며 아래 실패를 추가 기록한다. 분석 main/native/영상 인코딩은 검수자가 실행하지 않았다.

- [minus_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/minus_execution.json)의 실제 종료는 **−11(SIGSEGV), terminal_state=error, wall15.573737244005315초**이다. Native report.json/videos.json/MP4가 없으므로 정상5초 완료나 Python 정상 예외보고로 해석하지 않는다. 로그에는 기존 CPU PhysX/CUDA·visual geometry warning이 남아 있으나 이 기록만으로 SIGSEGV 원인을 확정할 수 없다.
- [minus trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus/trace.jsonl)는 **153행(0..152step), 마지막 t=.6333333333333333초**, states도153행, controls/contacts는152행이다. 이 전체 state/trace/contact prefix는 원quiet baseline과 exact이다. 152명령의 모든 원공통필드/全81 final target도 baseline과 exact이며 추가 index_support_delta_rad는 전부0이다. 따라서 −.005 pulse가 시작하는2초 이전 중단이며 pulse의 물리 성능·부호별 반응·6×1 중앙차분을 이 partial로 판단할 수 없다.
- Native capture.json은 **19개 완성 frame(0..144step, 마지막 .6초)**와 raw/overlay PNG76개를 기록한다. Trace 마지막152step을 완성 영상 frame으로 추정하지 않는다. 이후 partial 인코딩은 이 완성frame들만 별도 metadata/새출력으로 처리해야 하며 원 capture/raw와 실패기록을 덮어쓰면 안 된다.
- minus/plus 각각 실행 전후 입력 **103개**, 현재 원본 SHA, 103개 source snapshot SHA 및 닫힌 stdout log SHA를 독립 대조해 전부 exact를 확인했다. Minus initial_values는 원baseline에 비해 input_sha256 provenance와 index_support_command 선언만 다르고 나머지 저장필드는 exact이다. 양조건 fresh native15검사는 모두True이며 self1188과 별도 cross-hand 검사를 혼동하지 않는다.
- Plus execution은 exit0/completed, states/trace1201·controls/contacts1200·151capture와 report/영상존재까지 확인했다. Plus 전체 성능·metric/영상·후기창의 최종 검수는 아직 하지 않았다. Minus 최초 실패를 보존한 새leaf/새경로의 ONE 재시도는 추가 초기화를 명시해야 하며 기존 두initialization/2400steps 가정의 analyzer를 수정 없이 실행할 수 없다.

이 항목의 판정은 실패자료와 저장 prefix 보존에 한정한다. 재시도 wrapper/leaf는 준비 후 별도 사전 검수한다.


## 동일 minus ONE 재시도 wrapper/leaf 사전 검수

요약 판정: **문제없음(PASS, 재시도 사전 코드 범위)**. Python3.8 AST와 원 소비wrapper 대비 diff를 읽었다. 새 runner/준비/분석/인코딩/물리 main은 실행하지 않았다.

- [실패·새경로 guard:24](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_retry.py:24)는 최초 minus exit−11 및 before-input crash 분류를 요구하고 minus_retry_v2의 log/input/invocation/execution/native가 존재하면 거절한다. [child command:72](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_retry.py:72)는 **동일 원 runner에 --condition minus**를 주고 결과만 새 native/minus_retry_v2로 분리한다. subprocess는 한 번이며 반복재시작 경로가 없다. 환경·그래픽/물리 설정 및 입력trial은 원wrapper와 동일하다.
- [closure:34](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_retry.py:34)는 원 compact102 직접입력을 유지하고 새wrapper/leaf 및 crash실행/요약자료를 추가한다. 원wrapper도 유지하여 소비 provenance를 보존한다. 원runner/원wrapper의 현재SHA는 최초 minus가 소비한 SHA와 exact이다. Relative/absolute local import closure와 fixedlower/config/mesh/font 보존 로직은 직전 승인 wrapper와 동일하며 [snapshot:65](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_retry.py:65)에서 child 호출 전에 원본→사본 SHA를 대조한다. 종료 후 닫힌log 및 전후 입력SHA를 기록한다.
- [새 leaf](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_NATIVE_RETRY_V2.md)는 총 최대3초기화(최초 plus, 최초 minus crash, 새minus한번)·성공한5초 최대2회 및 1200+152+재시도실제step 합계를 명시한다. 원minus를 지우거나 성공으로 바꾸지 않고, 재시도가 다시 오류면 이 leaf에서 더 실행하지 않는다. 양방향 응답 결론은 재시도 완료 뒤로 유보한다.
- [minus_native_crash.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/minus_native_crash.json)의 output_inventory **86개 파일**에 대해 현재원본 SHA/크기/전체파일집합 exact 및 최초 execution SHA exact를 독립 확인했다. Tasks153행도 baseline prefix exact이다. 앞서 확인한153 state/trace·152 control/contact·19capture 및 초기15pass와 일치한다.
- [partial_videos/videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/partial_videos/videos.json)의 두MP4 현재SHA는 exact이며 저장 ffmpeg exit0/명령의 frames:v19·30fps와 저장probe19frame/재생.633333초가 일치한다. 마지막 시뮬레이션 capture는.6초이고5초 완료가 아니다. 검수자가 새ffprobe/영상인코딩을 실행하거나 실패원인을 확정하지 않았다.

재시도wrapper SHA-256: `f4055ea71b3edc2806f02e25e64dcfdae9b7fb8a5d0d0d3e6bc54ca476ae2828`.
새leaf SHA-256: `f5fc4f242e509794b4c2bff2982a2ab5d33eb8666075757fb225be440b9e022f`.

재시도 사전 판정: PASS. 실제 재시도 종료·분석/영상·총시도회계는 아직 검수하지 않았다.


### 재시도 wrapper 최종 미소비 보완

원실패86파일의 size/SHA를 [시작 전:27](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_retry.py:27)과 [종료 후:86](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_index_support_retry.py:86)에 대조하며 execution에 prior_partial_outputs_unchanged를 남기고 최종assert에 포함한 변경을 확인했다. 미사용 argparse import 제거 외 다른 실행조건 변경은 없다. Python3.8 AST PASS. 최종 wrapper SHA-256은 `e983280775327cb7d9b950327bf17ea2fccbf8cc2a881f9262db0837cb80a995`이며 앞 항목의 f4055…는 소비 전 중간 검수본이다. 새leaf SHA는 f5fc4f… 그대로다. 이 최종 코드에 동일minus ONE 재시도 blocker는 없다. **사전 판정: PASS**. 검수자는 실행하지 않았다.


## saved analyzer v2 사전 차분 검수

현재 미소비 analyze_quiet_index_support_v2.py SHA-256 `3b3106c2e1a8828c4530bbd415df208408916f3dc052571d642e60a1ee3538a7`, Python3.8 AST PASS. 원미실행v1 SHA86aa526c… 불변을 확인했다. [폴더:21](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:21)·[실행기록:85](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:85)은 minus_retry_v2를 소비하고 최초minus를 실패 별도자료로 보존한다. 기존20필드/81목표·other80/원prefix/float32ramp·원pose/121완전창/604PNG/151영상·명목.01rad 6×1 계산은 v1과 동일하다. [집계:106](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:106)는 baseline 재사용을 새init로 세지 않고 총새native3init·완료2400step·실패관측152step·합2552step을 구별하며 actor/training0·analyzer simulation0을 명시한다. 재시도 완료자료가 없거나 report가실패이면 완료검사/원자료로드가 거절하므로 partial을 성공으로 분석하지 않는다.

수정 권장(실물자료 오류는 아님): [실패검사:42](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:42)에 crash.execution_sha256와 실제minus_execution SHA 연결, failed실행 before/after/current·닫힌logSHA 확인을 추가하면 완료실행과 같은 closure검사를 확보한다. 또한 retry execution의 prior_partial_outputs_unchanged=True를 확인하는 것이 명시된 보존 계약과 맞는다. [실패prefix:43](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:43)는 state/trace/contact를 재계산하지만 tasks/control은 crash.checks 선언만 신뢰한다. 원자료의 이 항목들은 앞선 독립검수에서 exact였으므로 현재 실제결과 blocker는 아니며 미소비 analyzer의 fail-closed 검증 보완 권장으로 root에 전달했다. 최종 analyzer SHA/보완은 다음 항목에서 기록한다. 분석main/재시도native는 검수자가 실행하지 않았다.


### analyzer v2 최종 미소비 보완 확인

[입력closure:24](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:24)는 세실행 metadata/log와 실제검사하는 execution.input_sha256_before 원본 전체·baseline tasks를 직접입력으로 추가한다. 이전14k ancestry를 재귀복사하는 변경은 없다. [실패 provenance:47](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:47)는 실패실행 SHA↔crash.execution_sha256·입력전후/current·닫힌logSHA를 직접검사하며 [실패commands/tasks:49](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_index_support_v2.py:49)는152명령의 공통8필드와 delta0 및153tasks prefix를 재계산한다. 완료retry의 prior_partial_outputs_unchanged=True도 강제한다. 앞 항목의 권장 보완이 해소되었다. 기존20필드/목표·오차/영상/후기창/6×1 및3init·2552관측step 정의는 유지한다.

최종 analyze_quiet_index_support_v2.py SHA-256 `2503010553a3072e3735fb2908080d49f78b6174cfb5223407c0f88ac2bdb020`, Python3.8 AST PASS. **Analyzer v2 사전 판정: PASS, 실행 blocker 없음**. 기존v1미실행본은 보존되었고 검수자는 분석main/native를 실행하지 않았다. 실제 retry/analysis 결과 검수는 별도다.


## 완료 재시도·저장 분석 실제 원자료 독립 검수

요약 판정: **수치/물리 원자료 정합 PASS; 소비 wrapper canonical SHA 변경의 보존 정리 필요**. 검수자는 원자료와 SHA만 읽고 NumPy/SciPy로 수치를 독립 계산했다. Native/analyzer/producer/ffprobe main은 실행하지 않았다. 이 항목은 최종 그림/문서 검수 완료 선언이 아니다.

완료 plus와 minus_retry_v2는 각각 states/trace1201·controls/contacts1200이며 report는5초 완료이다. 원quiet baseline과 **20초기필드 exact, state/trace0..2초481개 exact, 다른80목표1200개 exact, 첫484 全81목표 exact**, 첫다른native state는 양조건 모두 **step485**이다. Index3 float32 ramp를 실제commandtime/원initial+offset으로 재조립해 양조건1200목표 exact·native targetbounds 통과를 확인했다. Wrist파형/clock/updateflag와 root하체고정·LA도 exact이다. Native actual관절 한계초과량 최대 **.00009994953870773315rad**는 baseline/plus/minus 같으며 목표한계검사와 actual의 완전준수를 혼동하지 않는다. 두 fresh15 전부True/self1188 및 별도양손 gate를 확인했다.

| 독립 재계산 항목 | baseline | plus | minus_retry_v2 |
|---|---:|---:|---:|
| t5 초기goal 위치오차 mm | 13.819696226078031 | 13.750277776454627 | 13.887982306216124 |
| t5 초기goal 회전오차 ° | 2.9182769770167227 | 2.921427734950553 | 2.9168119274840394 |
| 후기121개 완전1초창 최대위치변화 mm | .648624665739442 | .6855547270655585 | .6049953020669229 |
| 후기121개 완전1초창 최대회전변화 ° | .11530604071065459 | .12437280565838985 | .10600701856580796 |

원native Gpose/quaternion에서 구한 오차·완전창과 저장summary의 최대차이는0이었다. T5 world 위치/동일baseline 기준world회전log를 명목.01rad로 중앙 차분한6×1은 `[-.008817017078399658, -.008571147918701172, -.007355213165283203, -.01380816467622891, -.02044924380828965, .040464169087410344]`이며 앞3행 m/rad·뒤3행 rad/rad, 저장response와 최대차이0이다. 위치와 회전은 tradeoff이며 이 한 초기자세·작은ramp의 접촉분기 유한응답은 범용Jacobian/feedbackgain/안정화성공 인증이 아니다.

Raw human–G positiveλ를 body별 step중복제거하여 독립 집계한 결과도 exact이다. Index3는 세조건1156, middle3는91, ring3는38, R_Hip는1200이며 thumb3만 baseline587/plus521/minus615다. 이 λ 접촉step 수는 forceclosure·지지력 인증이 아니다. 초기오차최대는14.608483313112906mm로 세조건 같고 최대회전은2.9184118560193406°/2.9216614137521533°/2.9169990919951827°다.

각 완료run **151capture/604 raw+overlay PNG**의 현재SHA·step8/time1/30·renderreadonly·trace와route exact, 두MP4 currentSHA 및 저장ffmpeg/ffprobe exit0·151frame/30fps/5.033333초 metadata를 확인했다. 마지막 시뮬레이션은5.000초이고 MP4 151/30초와 구별한다. 실제PNG 장면/후속그림 시각QA는 후속범위다. 최초minus86원파일의 현재SHA/크기는 여전히 exact이다. 총새native는3init, 완료2400step+실패관측152step=2552이며19frame partial은 완료영상과 별개다.

[analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/analysis.json)의47checks 전부True·직접2045입력 before/after/current exact 및 stage입력의 부분집합임을 확인했다. 실행 exit0/5.364229907048866초·stage2054 before/after exact·2053사본SHA exact·닫힌logSHA exact이다. 양native 입력103/107의 before/after/current도 exact이고 retry prior_partial_outputs_unchanged=True다. 실제 analyzer가 읽는 직접원자료의 wrapper누락은 발견하지 않았다.

**해결 필요:** stage2054 현재원본SHA를 재검산하면 **run_quiet_index_postprocess.py 하나가 consumed ea42f0c7c15507726c093684fb0dde09a76e2398a8d7ca781a3b8f87cb45185b → current a52fb562384a23ab07471404850d0fe9aba670bac27462dd63c8b61e2d149fb7**로 다르다. Diff는 collection_inputs의 기존videos glob 포함 한 줄 삭제다. [실행당시 정확사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/analysis_source/stability_adapter_2/run_quiet_index_postprocess.py)은 ea42… exact로 보존되어 분석수치/원자료 손실은 없다. 소비 canonical원형과 collection변형 신규파일을 구별하고 이 변경사실을 보존 기록해야 한다. 따라서 현재 전체2054 current exact라고 판정하지 않았다. 타파일은 검수자가 수정하지 않았다.

[다음 Wrist_y 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md:3)의 숫자/접촉step/step485와 tradeoff는 위 원자료와 맞다. ±.005rad 두실험은 원quiet held목표로 index보정0을 되돌리고 기존wrist_x파형·다른80·초기81/G/LA/PD를 보존하는 미실행계획이다. 원Wrist_y 초기.17637284100055695/held.03675246983766556과도 맞다. 손가락 고정진단을 연주제어로 승계하지 않고 향후팔24/최종66·torso9 기준유지 및 checkpointqualification 별도범위를 명시한다. 추가retry는 별도leaf이고 controller/actor/train 구현·성공을 주장하지 않는다.


## canonical 복구 및 ONE 영상수집 후속 검수

요약 판정: **문제없음(PASS, 앞 항목의 source drift 보존 정리 해결)**. [source_drift/record.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/source_drift/record.json)의 소비 ea42…/미실행변형 a52…와 별도보존draft를 실제SHA로 대조했다. Canonical run_quiet_index_postprocess.py는 실행당시 ea42f0c7c15507726c093684fb0dde09a76e2398a8d7ca781a3b8f87cb45185b로 byte-exact 복구되었고 a52미실행변형도 별도파일로 exact 보존되었다. **분석2054입력 before/after/current 전체 exact**,2053사본·닫힌log exact를 독립 재확인했다. 앞서 발견한 원형불변 문제를 숨기거나 기존기록을 지우지 않고 이 항목에서 해결 상태를 구분한다. 원자료·분석 재실행은 하지 않았다.

[collect_quiet_index_videos.py](/home/ajou/yigyu/3/stability_adapter_2/collect_quiet_index_videos.py:44)의 pending은 완료4+partial2의 sourceSHA·dest부재·두뷰/저장frame metadata를 모두 먼저검사하고 이후6개를 복사한다. 기존152영상과v13 index를 보존하고 새v14/update_v13만 만든다. Collector SHA-256 `e826194d8b1581afb32e4bb5e3bf94e9cba730a9cc881dc0b0ab21da32467f88`, Python3.8 AST PASS. 실제collection은 복구ea42 wrapper로 ONE exit0, **166입력 before/after/current exact·165사본 exact·닫힌logSHA exact**이다. 누락된 기존video glob을 가진 a52변형은 이실행에 소비되지 않았다.

[video_collection_update_v13.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v13.json)의 기존152개 SHA와index SHA exact, 새6개 source/copy SHA·size exact, 새index SHA 및 기존index 원문 suffix exact를 독립 확인했다. 실제모음 **158개=152+완료4+부분2**이다. 네완료영상은재생5.033333초/151frame, 두부분영상은.633333초/19frame·partial=true이며 마지막partial capture시뮬레이션은.6초다. [VIDEO_INDEX_v14.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v14.md)는 완료와partial을 따로표시하며6개embed를 제공한다. Reviewer는 새ffprobe/인코딩을 실행하지 않고 기존probe metadata/currentbytes를 대조했다.

[ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/ROOT_VERIFICATION_NOTES.md)의3시도/2552관측step·47검사·수치tradeoff·원source드리프트 및 복구/미실행변형·152→158수집 서술은 원자료와 일치한다. NextWrist_y 계획의 현재숫자/제어권/미실행범위는 앞선 검수와같다. 현재이 범위의 unresolved blocker는 없다. 그림/최종README/CHANGED/최종audit는 준비후 별도검수하므로 review를 최종봉인하지 않는다.


## v1 보존·v2 실제 PNG/metadata 및 최종감사 코드 사전 검수

요약 판정: **문제없음(PASS, 그림/감사 코드 사전 범위)**. 두 실제PNG를 view_image로 열었다. V1은 왼쪽아래 index 패널의 upper-right 범례가 plus plateau/target 위에 겹치는 표시문제가 있다. 원v1 PNG `055ddf62ff357d97863dd0376133256064e2a52bbb129fb21851c99f4a5c0226`·producer/실행/metadata는 보존되었다. V2 producer 차분은 새파일/새출력경로와 범례 lower-right 이동뿐이고 수치/축/자료/계산은 동일하다. V2 실제PNG `760e94a7811ea26b6c6f755f932dba4cbe5cc29b3d5e7316ff1a0480a92daef0`는 빈 하단영역의 범례로 곡선가림이 해결되었고 title/단위/축/캡션·범례가 읽힌다.

V2의 위2패널은 초기worldgoal 대비 position mm/rotation deg, 왼쪽아래는 index3 actual/PDtarget rad, 오른쪽아래는 동시baseline world위치와의 거리 mm다. 목표1200개는poststep1..1200/240초, actual1201개는0..1200/240초에 맞춘다. 2초전 공통prefix와2..2.5 ramp 및 이후유지, 색상3조건/actual실선·target점선을 정확히 구분한다. 마지막오차표와곡선·범위가 맞고 오른쪽아래거리는 독립확인한 plus max.08733834984058364/end.07656824621477867mm, minus max.10694259007980318/end.06866839237940672mm와 맞다. 캡션은 저장자료·60Hz held command·자연연주/정책호환미인증을 명시한다. 실패minus partial은 이 두완료응답 그래프에 섞지 않는다.

각v1/v2 **wrapper2053입력 before/after/current exact·19selected실제사본 exact·닫힌logSHA exact**, producer manifest2049입력 exact·output SHA exact·native/physics/actor/train추가0을 독립확인했다. Producer/wrapper before/after/canonical/archive SHA도 exact다. Full원자료사본은기존analysis_source archive에 보존하고19selected사본을전체2053사본으로 부풀리지 않는다. V2producer SHA `4965484b84adb412640ec4c2680ca356eb5e606a0d862d34da491ef2f55591f2`이다. V1/v2 execution exit0·wall각2.011671781539917/1.607647180557251초를 확인했다. 재render/producer/main은 검수자가 실행하지 않았다.

미실행 [root_final_audit_producer.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/root_final_audit_producer.py:15) SHA `637a20141390190f19b0162be66d6b24a4701dea35f64b067ddc69bf324f2349`, Python3.8 AST PASS. 현재코드는plus/minus/retry expectedexit0/−11/0·103/103/107입력/사본/log,완료각1init1200/151·fresh15/self1188,최초86실패원본/19frame·retry보존,47분석·3init/2400+152·actortrain0,analysis/collection/artifact/v2각실행전후현재입력과실제사본/닫힌log를 검사한다. Source drift exact복구·미실행draft보존, 두그림manifest·추가native0,158영상/기존152+6복사/2partial·v13/v14 index 및 journalprefix,기존8phase inventory+thumb2v2 교정inventory의9개union을 검사한다. Self1188을별도양손검사쌍수로해석하지 않는다.

감사는 최종review PASS문자열을 요구하고 모든checks 통과 뒤 source_final 사본/manifest·실제final_verification·inventory를 작성한다. Append가능 canonical mainREADME/PLAN/VISUAL3개는prefix검증/최종사본보존을 유지하며inventory에서만제외한다. 과거openstdoutlog 문제를 되풀이하지 않도록 root가stdout직접실행할 예정이며 검수자는감사를 실행하지 않았다. 현재 final_verification/inventory는 아직없음이 맞다. 최종README/CHANGED/main추가분은 준비후별도검수하며 이 항목이 최종전체봉인 PASS를대신하지 않는다.


## 최종 문서·main 결과 추가분 검수 및 review 동결

요약 판정: **문제없음**. 이번 검수는 최종 [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/README.md:1), [CHANGED_FILES](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/CHANGED_FILES.md:1), [VISUAL_REPORT §118:2106](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2106), main [README:1261](/home/ajou/yigyu/3/stability_adapter_2/README.md:1261)·[PLAN:2082](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2082)의 새 결과문구와 ROOT_VERIFICATION_NOTES 마지막 추가분에 한정했다. 앞선 실제코드·원자료·그림·closure 검수결과를 재사용했으며 물리/분석/producer/감사 재실행은 하지 않았다.

- 표의 초기오차최대/t5오차/후기121완전1초창 수치와 endpoint차이, 명목.01rad 중앙차분6×1·단위/worldframe·특정접촉분기 제한은 앞선 독립 재계산과 일치한다. Plus위치미세개선/회전악화와minus반대 tradeoff를 함께 명시하며 초기goal복귀·globalJacobian/feedbackgain·자연연주/정책호환성공으로 확장하지 않는다.
- 20공통초기필드·other80/첫484명령·0..2prefix·step485첫분기, rawλ index1156/thumb587·521·615/palm없음 및 실제native한계초과.000099949539rad는 확정자료와 맞다. Targetbounds통과와actual의완전준수, rawλ와forceclosure/뉴턴힘을 구별한다. Actor/train0이며 다음Wrist_y는아직구현·실행되지 않은계획이다.
- 최초SIGSEGV 원인미확정/보정전152관측step·19완성frame/86원파일·Pythonreport없음, 총3init·완료2400+실패관측152=2552 및별도retry경로를 일관되게설명한다. 완료151frame/재생5.033333초와simulation5.0초, partial19frame/재생.633333초와마지막화면simulation.6초를 구별한다. 완료4MP4와partial2MP4는정확한절대경로embed이고t0/t5 native이미지와수학시계열그림을구별한다. 기존152→158모음과복사SHA서술도 맞다.
- 소비canonical의a52미실행변형보존/ea42 byte-exact복구를 숨기지 않고 기록했다. 원그림v1 범례가림과 별도v2 표시해결/원producer불변·추가물리/분석없음을 정확히구분한다. 2054입력/2053분석사본·2045직접입력·47검사 서술은 복구후확정검수와맞다. ROOTnotes의마지막완료서술은 최종감사를 이미실행했다고 주장하지 않는다.
- 새문서의절대파일·이미지·영상링크 및명시줄번호를 실제파일존재/범위와 대조해누락없음을확인했다. Main결과heading은실제README1261/PLAN2082, VISUALheading은2106이다. 기존review와소비sources/원자료/산출물은편집하지 않았다.

최종문서 SHA-256:

- README: `9ff58dd00af4a614a372a01bb8d2f03b4186e69b2298e8bd0b34a9921312278a`
- CHANGED_FILES: `ffdc453e225db4802172cefee2bdd99f6fc8b5aea917508bb2d5b7a6b0392a21`
- ROOT_VERIFICATION_NOTES: `328c37d5c7b3472860c39e10f4544320d35715115374e1087d1648e0f894b211`
- VISUAL_REPORT: `446acdb4bbdb1b8b455138cba1474f41d526544b9d54ee185aaa2eddcf7d25a1`
- main README: `ad81875fa61e03ef9ff39bcf26734419f9ba4b6f4f176974e44eec53c5b92fe0`
- main PLAN: `8e4a32d8eb18b2272267f25d6609de607398e2268200e902950b12820b1ccd2c`

해결되지 않은 중요blocker는 없다. 이 판정은 저장물리진단·회계/보존·산출물/문서 정확성에 대한검수이며 안정feedback/자연연주/정책qualification이나아직미실행root감사통과를 인증하지 않는다. 이추가후 review를동결하고 root가별도ONE 보존감사를실행한다.

최종 판정: PASS
