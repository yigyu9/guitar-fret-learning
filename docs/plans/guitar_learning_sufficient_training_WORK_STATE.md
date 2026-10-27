# 완료 — 충분한 학습과 결과 분석 (2026-10-20)

사용자요청을완료했다. **추가학습/평가가백그라운드에서남아있지않다.** BASE는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1`이다. 최신전체보고서는BASE/README.md와analysis_v1/FINAL.md,기계검증은verification.json/completion_seal_v1.json,독립검수는review_v1/FINAL_REVIEW.md이다.

본학습128추가·32→160·245760commit·1024episode529성공51.66%·물리0·목표접촉해제1024·0discard·wall9654.14초(선행감사제외). 첫/뒤64성공48.24→55.08%로완만한상승. 실패495중487은마지막200ms준비창clean0,전체firstclean미관측337,준비양수후유지실패8. 모든실패해제보상.75. LR1e-7/KLretry0,Actor실제변화/Critic개선,안전cost지배인과근거없음.

기준B32/중간global64(이번local32 checkpoint_000031.pt)/최종global160 평가:det각20/20,stoch8/20→11/20→11/20. 중간→최종10/20조건판정교체;finalstochhold57.458%는base45.708보다높지만mid67.917보다낮고missing187.396ms는둘보다악화. finalnominalhold98.5%로20조건모두90%이상통과,준비160ms. baseline/finalfresh6은3/6→4/6(101/103/107유지+109새성공,113/127실패유지),12initialstate전체leaf/contacthistoryexact·12PID/localcase0검증. 표본작음/단일계보/같은준비자세이므로일반화/통계우월성/숨은cache동등주장금지. 별도평가132회는훈련량합산안함. 처음14업데이트는oldC exact재현으로독립새표본합산금지.

최종modelBASE/training_long_v1/final.pt SHAae9770470cdbd7141bf47c277a4a81757a753841beab18419c60de31f2e9a7e6. 마지막모델이며최우수선언아님. 모든caseplannedfinalSHA/path/strict160+10artifact·source/runtime/final6PID검증v2passed,9mainruntime/input2389·snapshot/2398source독립재해시불일치0. 모든helper/native세션닫힘·8workerexit0·activeentrypoint0. Root생산코드는변경하지않았고source/settings/physics/reward계약을동결유지했다.

미적용후속: R1준비전구간신호,실제접촉상실/회복시연자료,획득latch를관측/해제자격과연결하는R2. actorLR/BC별도비교도새계약/명시이전/게이트가필요하다. 이번성공을두음/전곡/양손/실제현압력음향/Root자유균형/전신정책학습/엄밀EPS0해법/회복BCPPO완성으로확대하지말것. Root고정·하체유한·freeguitar/중력ON/strapOFF/105-97-8 유지. 보고서표현수정전FINAL/manifest는analysis_v1/archive/20261020_before_final_seed_wording에SHA와보존했다.

---

# 가장 최신 — 2026-10-20 01:07KST

**본학습완료/평가진행중이며사용자요청아직미완료.** main128추가/누적160/245760반영/1024에피소드529성공(51.660156%)/물리0. session46646정상종료0. stoppedupdates_complete,wall9654.138s,collection9611.775/PPO8.722s. frozenhelper검증training_long_validation_v2도exit0:2389input·9runtime·0discard·source변화0·coreSHA/128files통과. final.pt SHAae9770470cdbd7141bf47c277a4a81757a753841beab18419c60de31f2e9a7e6. Baseline/중간/최종결과혼동금지.

**현재최종평가3개진행중**(동일BASE/frozenhelper): final_deterministic_v1 session93035 PID3874988; final_stochastic_v1 session31244 PID3874984; final_fresh6_v1 session1308 PID3874992. 입력training_settings_v1.json/최종main/final.pt,protocol각20det/20stoch/fresh6. 끝까지관찰하고sessions닫고validate_evaluations_v2.py로검증할것. FreshPID관측은 **exec_command require_escalated로 /tmp/guitar_sufficient_brief_v4.py** 실행해야host/proc가보이며BASE/fresh_process_pid_observations_v1.jsonl에각child를자동기록한다. 매case4~5분이라1분이내조회로6PID를놓치지말것. 최종검증스키마는-v2만권장(예전-v1부족사항보완). CPUvalidator실행은frozenhelper -c Path(...script).read_text() exec를사용해모듈경로유지,이전실패자료는보존한다.

analysisworker에TRAINING_FINAL/summary/128snapshotSHA/6패널curve/간결2패널summarycurve및finalparameter+고정BC60관측출력비교를followup했다. agent는analysis_v1만소유/nativeGPU생산수정금지,최종평가아직미집계. final평가끝나면pairedbaseline/mid/final및fresh6비교분석followup,루트전체검증,독립reviewer최종검수,BASE/README.md·verification.json·plan체크리스트완료,전process닫힘확인후최종보고할것. 학습만완료했다고지금끝내지말것.

---

# 현재 작업 기억 — 충분한 학습

## 최신 (22:51KST)

23:09KST: main추가32·61440commit·126/256성공·물리0·LR1e-7/KLretry0,checkpoint_000031.pt=**누적64**. worker에mid32prefix로첫32파일/episode<=31분석followup완료. 중간평가를지금시작: mid32_deterministic_v1 / mid32_stochastic_v1, 각원protocol20조건동일·체크포인트main/checkpoint_000031.pt, frozenhelper_v2사용. launch/exitJSON과log에서PID/session진행확인할것. 이모델은훈련추세를보고고른독립검증model아니며비교용중간32회스냅샷이다. 마지막160회모델과도동일protocol로비교예정. main128목표는계속진행하며중간평가두개를main업데이트에합산하지않는다.

중간평가세션/PID: mid32_deterministic_v1 exec84846 PID3812684; mid32_stochastic_v1 exec37001 PID3812717. 현재진행조회는 `/tmp/guitar_sufficient_brief_v2.py` 권장(main+mid32counts). MID32.md/mid32_summary.json/mid32_snapshot_manifest.json/mid32_learning_curve.png 작성완료. 첫16→뒤16 성공66→60/128,hold57.669→56.868%,ready67.448→62.565ms. 실패130중129ready0, **1건은ready83.333ms후hold88.333%실패(update30 worker1)**이므로모든실패ready0라고설명하지말것. criticrewardloss.07828→.06832/EV.5958→.6215, costloss감소하지만costEV하락. std변화첫마지막약+.12%,BCMSE안정,LR/retry정상,weightedcost/rewardstd첫/뒤16의4.04→2.92%. 물리0·해제256/256. worker별고정실패원인단정불가. 결과provisional; main계속128목표진행.

Main training_long_v1/session46646 계속진행,추가17updates·32640commit·70/136성공·물리0·LR1e-7/KLretry0. 첫checkpoint_000015.pt는누적48이다. **baseline_validation_v1.json은완료/통과**: 두20조건의native/case/seed/source/runtime 재감사,det20/20·stoch8/20·물리0. 분석worker가BASELINE_v2.md/baselines_v2.json작성완료. 실패12모두ready0.

중간16분석도완료: analysis_v1/MID16.md,mid16_summary.json,mid16_snapshot_manifest.json,mid16_learning_curve.png,mid16_old_C_comparison.json. 처음14회는과거C와주요비시간scalar·diagnostics·rewardterms·112episodepayload/metrics까지exact동일→**독립새표본으로합산금지**. 같은B32/RNG의수치재현이고이후구간이실제확장이다. 16회전체66/128성공·hold57.669%·ready67.448ms·release128/128·물리0. 첫8/뒤8성공둘다33/64. 실패62모두ready0,50개hold0,실패도release보상.75. weightedcost/rewardadvstd1.21~6.78%→안전비용지배근거없음. 수집평균88.62초/update vs PPO.08초. 새모델/보상/탐색설정수정없이계속추가128목표로진행한다.

다음중간분석은32 또는64완료시worker에새prefix로followup. 최종평가는main완료후최종모델과훈련구간에서선정한중간후보각각동일20seed(det/stoch)로진행예정이다. 원본B32baseline결과/종료감사완료상태는재실행하지않아도된다. 평가는루트만실행하고worker는analysis_v1만작성한다.

사용자 최신 요청은 충분한 학습을 실제 진행하고 결과를 분석하는 것이다. 아직 완료하지 않았다. 새 사용자 승인 질문은 필요 없다.

- 범위: 기존 단음 A/왼손/500상태/39행동/원 refinement 보상으로 B32에서 추가128 PPO 업데이트 목표. R1/R2는 별도이며 이번에 구현/학습했다고 주장하지 않는다. 회복 시연은0건이다. 충분한 학습량 뒤 실제 성공·정체를 분석한다.
- 계획: `docs/plans/guitar_learning_sufficient_training_20261019.md`.
- 결과 base: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1`.
- 기준 checkpoint: `.../guitar_learning_contact_recovery_v1/reference_provenance_migration_v1/checkpoint_evaluation_only.pt`, SHA8bedd8d9affc16406b3fb82667429615b8f13ec5e894d1dc576e940549edfd67, optimizer32. 이전 평가용 manifest는 수정하지 않고 이번 학습 사용을 `training_use_decision_v1.json`에 새로 기록했다. strict identity 동일, 사용자 새 요청으로 학습 활용 승인됨.
- 설정: base/training_settings_v1.json =8환경·H240·추가128·maxwall14400초·checkpoint16회; 모든 PPO/BC/탐색/물리/보상/목표 계약 원본 그대로. 목표245760전이/1024에피소드. wall budget은 업데이트 사이 검사이므로 실제 달성량과 이유를 보고한다. smoke_settings_v1.json은1업데이트만, 나머지동일.
- frozen_execution_view_v2: 현재 내부화 패키지 전체(최상위 code archive만 제외, assets 안의 archive 자료는 포함)와 외부127파일 복사. namespace에서2398 SHA 전부 일치. 원본/view code는 수정하지 않는다. host의 다른 채팅 소스 변경은 되돌리지 않는다.
- base/namespace_base_argv_v2.json이 실제 권장 읽기전용 view이다. cache 때문에 v1 실패했고 원자료 보존: readonly home에서 gymtorch/lock 쓰기가 막혀 업데이트0으로 종료했다. v2는 TORCH_EXTENSIONS_DIR=/tmp/guitar_learning_sufficient_torch_extensions, 기존 gymtorch 바이너리를 복사한 별도 task cache 사용. 실제 cache_smoke_v1 import passed. 물리·학습 소스 변경 없음.
- 실행 helper `/tmp/guitar_sufficient_launch_v2.py` 사용. 정확한 사본은 base/launcher_source_v2.py. 인자 `NAME -m MODULE ...`; helper가 namespace argv+rl38 python으로 실행하고 NAME.log, NAME_launch.json(PID/argv/SHA), NAME_exit.json을 남긴다. require_escalated로 호출해야 native/CUDA/bwrap 가능. 원 v1 helper/실패자료는 보존한다.

현재 실행 상태(22:21 KST 부근):
1. training_smoke_v2: session73962 정상종료0,1920commit·optimizer33·성공7/8·물리0. 부모/8worker runtime·core/persistent/teacher·2391+입력재해시 모두 통과. training_smoke_validation_v1.json이 정본. 캐시수정전v1은업데이트0실패로별도보존.
2. baseline_deterministic_v2: session56184 PID3777059. contact_recovery.run evaluate --settings base/training_settings_v1.json --checkpoint 위B32 --protocol base/evaluate_deterministic_20_v1.json --out base/baseline_deterministic_v2.
3. baseline_stochastic_v2: session99772 PID3777094. 위와동일, protocol evaluate_stochastic_20_v1.json, out baseline_stochastic_v2.
4. **training_long_v1 실제시작**: session46646 PID3781253, 22:21KST. 같은helper/module/settings=training_settings_v1.json, 원기준B32에서strictresume, out=base/training_long_v1. 이main을끝까지관찰하고실제결과를분석할것. helper exit/launch/log파일과read-onlyview로provenance보존. 현재초기증거감사중.

22:45KST 갱신: main은12업데이트·23040commit·49/96성공·물리0·LR1e-7/KLretry0으로정상진행중이다. root간이조회는 `/tmp/guitar_sufficient_brief.py`(더짧은출력) 권장. baseline_deterministic_v2/session56184와baseline_stochastic_v2/session99772는정상종료0,각20회·결정적20/20·탐색8/20. root가baseline_validation_v1 helper실행(session8009)으로동결view안case/seed/source/runtime를재감사했고결과JSON을확인할것. analysis worker에baseline집계를followup했음. main추가16완료시worker에중간집계를followup할것. 과거C와첫7success합계29/56가같아초기trajectory재현여부를worker가확인할예정이며독립표본합산금지.

다음:
- smoke감사와main시작은완료. main 출발counter32, 최종목표160, 새nativeepisode이다. smoke업데이트는 main계보에 합산하지 않는다.
- baseline20조건det/stoch는 학습과 별도. 두 protocol seed=[101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,193,197], persistent reset이며 물리 초기자세 다양화/통계 독립성 아님.
- main 실제 update/log/학습률·KL·안전·자원/전이 무결성을 계속 확인한다. source/lower/root/freeguitar 조건 유지. 128회 실제 완료 목표, 낮은성공률 자체로 조용히성공주장하지않는다. 심각한물리·무결성·LR고갈 등실패면원자료보존하며조치한다.
- 중간/최종모델을 같은 protocol로 실제 재평가하고 결과·앞뒤구간·perworker·접촉준비/유지/해제·물리/KL/LR/std/BC/value를 분석한다. 최종 completed 플래그만으로128 달성을 추정하지 않는다. candidate 선택에 쓴 evaluation을 독립검증이라고 주장하지 않는다.

에이전트:
- training_path_audit, reward_training_design: read-only 탐색 완료. R1은500 유지가능, R2 획득 latch는현재관측에없어최소추가2채널필요하므로 이번baseline과분리했다.
- sufficient_training_review(change-reviewer): 준비 검수 완료,2398SHA 독립일치·차단없음. 마지막분석 검수에 재사용할 것.
- sufficient_training_analysis(worker): **base/analysis_v1/**와/tmp helper만 소유, 생산/검사/설정/frozen입력 수정금지. 스트리밍 분석·정적 학습곡선 준비중. root가 main시작/충분한중간/최종data시 followup할 것. Native/audit/eval 실행은 root만한다.

상태조회간이도구: `/tmp/guitar_sufficient_root_status.py`를 실행하면 main/smoke/baseline 마지막phase·update·logtail을 짧게 출력한다. analysis_v1/analyze.py는worker가준비완료했고oldC14회56/112/26880commit를재현했다. 16~32업데이트에서실제새자료분석을followup할예정이다.

도구/보고: rl38 Python3.8, Isaac Gym을 NumPy/Torch보다먼저import. 모든환경 thread1. commentary는 진행중60초이상 비우지말고 sleep/wait는60초미만. 기존코드 수정없어 기존64 CPU 검증은재수행하지않았다. 원래 baseline의8환경당 약80~90초/update로128회가 대략3시간이며, 실제 속도와 RAM을 확인해야 한다.

23:20KST: main추가41회·78720commit·161/328성공·물리0, 중간평가각5/20. analysis worker가 PARAMETER_MID32.md/parameter_mid32.json/.py를완료: originalB32와migratedresume모든modeltensor exact동일,mid32와identity/schema동일. LHActor상대L2변화0.0008554%,95.12%scalar변경이지만작은폭,Valueencoder6.136%,RH완전동일,std평균+.1245%. Actor완전정지라고하지말고LR/BC원인단정금지. 다음은mid32양쪽평가종료감사와local64고정prefix분석.

23:40KST: main55회·105600commit·210/440성공·물리0. mid32_deterministic_v1/session84846와stochastic_v1/session37001둘다exit0,각20/20·11/20성공. frozenview검증mid32_validation_v2/session91213도exit0;실제출력은mid32_validation_v1.json. 입력/런타임/case/seed모두통과했다. 첫검증호출mid32_validation_v1은파일직접실행으로sys.path에project가빠져ModuleNotFoundError;native실험실패아니며자료보존. helper -c에서Path스크립트exec로해결했으므로최종검증도 -c방식으로실행할것. worker에MID32_EVALUATION.md/JSON paired분석followup완료. BASE/validate_training_long_v1.py는128/160/245760사전기대검증용으로준비했지만아직미실행;실제완료후실행할것.

23:49KST: main62회·119040commit·238/496성공·물리0. 분석worker가MID32_EVALUATION.md/JSON/initial_state_leafdiff완료. 중간탐색11/20대기준8/20이지만paired13/20교체(3성공유지,8새성공,5새실패,4실패유지). 모든20쌍초기human/guitar pose/vel/target/codec/previousaction/controllerhistory동일;contact_history만다름. '초기자세다름'이나'완전coupled'라고하지말것. 독립reviewer의권고대로최종생성전fresh_process fixed6seed(101,103,107,109,113,127)를기준/최종에추가하기로기록(fresh6_evaluation_decision_v1.json,프로토콜evaluate_stochastic_fresh6_v1.json). 기준baseline_fresh6_v1실행중session40737,launcherPID3831608,첫childPID3831612. 각case새프로세스에서BC/4gate선행감사를매번수행해총약30분소요예상. 최종fresh6은main/final.pt생성후시작할것. status는 /tmp/guitar_sufficient_brief_v3.py가main+mid+fresh진행및childPID관측을BASE/fresh_process_pid_observations_v1.jsonl에기록한다. **실제host PID를보려면exec_command require_escalated가필요하다**(기본sandbox/proc에는안보임). 매case약4~5분이므로주기상태조회로PID/start_ticks를기록할것. freshbatchparent는runtimeaudit없고각process_XXX자식audit를검사하며case는모두case_000/localcaseindex0·protocol_case_index는0..5다.

00:22KST(10/20): main89회·170880commit·355/712성공·물리0·LR1e-7/retry0. local64분석MID64.md/JSON/curve완료:247/512,첫32→뒤32성공126→121/256,hold57.269→53.213%,ready65.007→66.081ms,실패265중ready0=261(준비양수후hold실패4). Critics예측개선이나성공추세상승없었음. 이후최근25회는108/200성공으로일부상승이있으나최종128분석대기.
baseline_fresh6_v1/session40737정상종료0,3/6(101/103/107성공). baseline_fresh6_validation_v1/session26652종료0,출력BASE/baseline_fresh6_v1_validation.json passed. BASE/validate_fresh6_v1.py는최종fresh에도사용가능; frozenhelper -c 'from pathlib import Path;exec(Path(.../validate_fresh6_v1.py).read_text())' final_fresh6_v1 으로호출. validator는batch6childruntime/2391pins/artifacts10종/source/checkpoint/seedafterload/localindex0/한scene생성종료/6PID를검사한다. childPID기록6개확보됨. agent BASELINE_FRESH6.md/JSON완료:6initial_state전체SHA/contact_history까지exact동일(d0981b...),hold48.333%,ready68.750ms,release6/6·물리0. 기존persistent첫6은2/6(101,127)라fresh와교체있음. 동일모델실행조건차이이며독립학습/개선으로설명하거나pool하지말것. 현재추가평가모두닫혔으므로status_v3은기본sandbox로읽어도됨,**최종fresh실행시에는require_escalated로주기조회해PID관측기록필수**. main끝나면추가128실제달성/optimizer160/245760전이검증후finaldet20+stoch20+fresh6(3개독립out)실행할것. 최종학습분석·파라미터/관측출력비교·보고서/curve·독립review·전프로세스닫힘까지아직남음. 사용자요청은아직완료아님.

00:51KST: main115회·220800commit·464/920성공·물리0·LR1e-7/retry0. 최종검증파일주의: 독립검수가checkpoint경로/SHA/누적160연결과persistent20의10artifact검사를권고하여기존v1보존후 **BASE/validate_evaluations_v2.py** 를추가했다. 지원name=baseline_fresh6_v1,final_fresh6_v1,final_deterministic_v1,final_stochastic_v1, argv[1:]로여러name가능. frozenhelper -c 'from pathlib import Path;exec(Path(.../validate_evaluations_v2.py).read_text())' final_deterministic_v1 final_stochastic_v1 식. 최종fresh는별도로같은스크립트 final_fresh6_v1. 모든case의source_checkpoint/initialization_checkpoint_sha256/seedSHA/initialization strict_PPO160을main/final_checkpoint.json의path/SHA160에대조,10artifact/runtime/2391pins/seed검사. baseline은명시B32/path/SHA/32고정. 기준fresh6에 v2 실행(baseline_fresh6_validation_v2/session14606) exit0,출력baseline_fresh6_v1_validation_v2.json passed. 학습검증은 **validate_training_long_v2.py** 를권장(128추가/160global/245760각회계/0discard/9runtime/persistent/teacher/core에core_reportSHA/128update파일확인추가), 아직미실행이며 -c exec로실행할것. 검수agent가v2수정재검수완료문제없음. 기존v1스크립트/출력보존. main끝난뒤최종3평가,worker FINAL.md/summary/curve/parameter+actoroutput분석,root검증,최종결과검수,모든process닫힘,README/plan/WORK_STATE완료가남음.
