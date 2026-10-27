# 최신 초기 지지의 왼손 사이클 원자료 최종 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 동작·접촉 판정·관절 제어·원자료 분석을 확인했다. 첫해제와그이후큰기타운동을보존하고초기자세가계속유지됐다고결론내리지않는문서해석이적절하다. 산출물/최종봉인감사는후속검수대상이다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음.

## 실제 접촉·운동 독립 확인

- Native는failure=None/3840physics/960control/16초,inputs_unchanged=True/forbidden_calls=[]다. actual_contacts/left_cycle_contacts/endpoint의step1..3840,effort0..3839,target0..3836(step4)이정확히맞음을직접대조했다. 분석에서길이만대조하던actualcontacts도이번자료는시각정렬이맞다.
- A유지3–4.5/B유지10–11.5초는각360/360step에서thumb3와index3가넥root에양의rawlambda로동시접촉했다. A에는middle3–fret7도일부있고B에는index3–fret4가있다. 네손가락모두항상붙었다는증거는아니며본보고도그렇게주장하지않는다.
- A열기6–7초240/240,B이동7–8.5초360/360,B열기13–16초720/720step은실제로왼팔/손전체query접촉0이다. zero-lambdacontact도포함해free를엄격히판정하며L_Hip은LH집계에서제외한다. contactrow중복개수를step수로세지않는다.
- 전체초기기준BB최대37.287510mm/SO3최대14.515732°다. 첫release_A4.5–6초구간시작기준16.521645mm/14.716803°,open_A6–7초13.902861mm/8.432889°이며큰재배치가있다. 마지막open_B13–16초.444638mm/.212700°만으로전체사이클안정성을주장하면안된다. 선호README는이차이를명시한다.
- 평균B−A손목G변위[4.791620,41.417822,2.054299]mm다. 그중넥축41.417822mm와대각분리를포함한전체cycle넥축extent119.794403mm를정확히구분한다.
- Chest는hold_A에서0이고hold_B에서는360/360positive다. 마지막open_B는Chest716/720positive,R_Shoulder/R_Hip각720/720positive이며L_Hipraw88/positive0이다. 따라서가슴/상완/허벅지접촉변경을무시한수동평형·단일부위지지·초기pose유지성공을선언하지않는다.

## 제어·입력·로그 정합성

- Latestnear의동일initial에서cyclefactory로실행하고EW7타현factory를호출하지않는다. 왼팔12+손21목표만바뀌며other48최종목표배열을q_ref와직접수치대조해exact다. request/final/실제상태를분리하고actual상태freeze를추가하지않는다.
- 실제최종human81effort3840행을직접읽어finite·modelcap이내임을확인했다. Left12virtualtask는25N/2Nm요청cap과Jᵀ/관절cap으로제한되고other69effort는기존기여분을유지한다. 기타wrench/부착/pose쓰기추가경로가없다.
- 목표model/rate,finiteeffort/cap,endpointcoverage,입력/owner10개분석invariant는모두True다. Nativebefore1287입력SHA를현재파일과직접대조해변경0이다. 이는실제계획/소스/config/계약/XMLmesh/OMmass/near참조보존범위와일치한다.
- 실제driveMode는EFFORT33/POSITION48다. 상속POSITION57설명이나oldtrackingdisabled를현재전체제어OFF로읽으면안된다. log_scope_notes가그범위를명시하고최종권위파일을left_cycle_efforts.json으로지정한다. Root가원시로그를소급덮어쓰지않고범위설명을분리한방식이적절하다.
- Root/하체고정·selfcollisionON·freeG/strapOFF·오른타현OFF/유한상완·몸통지지를유지했다. 접촉lambda를N단위힘·힘폐쇄·학습곡·장기강건성으로해석하지않는다.

## 결과 문서 검토

- RootREADME의구간별기준/전체초기기준/2초기준을구분한숫자와동작시간이analysis와맞는다. 엄지+다른손가락이라는설명은thumb/index실제접촉을포함하는정확한일반표현이다.
- 마지막놓은상태는조용했지만처음놓을때기타가크게움직였다는counterevidence를숨기지않는다. 순차해제는미실행된다음개선후보로만표시하며주원인을접촉/반작용중하나로단정하지않는다.
- 리뷰어추가물리실행은0회다. 이테스트질문의구현/원자료정확성에추가재현이필요한우려는발견하지못했다. 결과의안정성한계는제어오류로숨기거나추가시험으로소급교체할대상이아니며그대로보고한다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/chest_left_grip_cycle_v1.py`: `ade0c307a9f9371ad4d040869bebec92778e403f5c51e4070966a31c163da74e`
- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_left_grip_cycle_v1.py`: `f64c480b4fd05c58fd1001986e52125439debfbc2ea334cf6624b9c476fc2559`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_chest_left_grip_cycle_v1.py`: `4df2ccf77b6b00adc9b7203241285668c741ff41838958b6abbb40e8b9be0d0f`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/config_v1.json`: `88b8c7fba35502875154b6663cfddb5bbfd709954afe2309c97f20714a5a3f68`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/native_v1/report.json`: `fda864e552f5689a28a65b24f7ab2843f77ef90ed0e9e6322a2cb5021cdf383f`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/analysis_v1.json`: `1c4e28d0a3de08c6f273f6616d1b08589ecf3a59e9cf06af65f551e7d31ed834`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/README.md`: `bb76cdaf03c354e3c0a847af9293a630205ed66dde18f4a92ecf8ee1c90c4417`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/log_scope_notes_v1.json`: `eafcde40cea8c1a2aa0d81b711055d87a5d7124f1d9277d7cd4d2f55c1025eb9`
