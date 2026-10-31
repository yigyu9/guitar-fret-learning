# 7시간 연구 인계 상태

2026-10-31 05:42 KST. 종료 예산11:02:53, 학습10:27:53. Production과frozen3148파일은원본보존.

완료: 중지/약지/소지 A각100/200 모두32/32·clean2.5초·실패0,초기0/32. 검지B0/100/200 모두32/32이지만clean2.4345/1.8861/2.2625로초기이전모델best. free-v9 A네손가락+검지B0 모두32/32;팔은학습전IKbias상수, 실제wrist31~55mm운반. 핵심범위FREE_TRANSFER_ANALYSIS.md.

고정모델잡음진단13개완료DIAGNOSTICS.md. 검지A100 scale0/.25/.5/1 안전32/0/0/0, 중지32/32/13/3. 추가검지.05=32/32 clean2.439714, .1=31/32 clean2.107813. 신호는목표별noise취약성;학습개선증거는아직아님.

현재GPU 세션74105: fixed_reset_evaluate.py로Binitial32env seed4242. 끝나면 B100,B200도같은도구로평가하고assert_same_initial_conditions 세실제q/hold캡처비교필수. 이후initialize_stage.py sourceA100→free_v9/v9 zeroexport·기본evaluate32·render검증. indexAseed17(research.py)·full33_comparison.py 200절차대조대기.

worker implement_research_runtime은R/variance_variant의새53MB runtimecopy/newschema sigma.05훈련모듈+CPUtests작성중. oldRT/oldcp미수정. sourceA100byteexact복사완료. GPU권한독점보장:worker는CPU만,완료/독립review후smoke→paired100train→detBfixedseed+freev9평가. controlA100→B100은기존동일seed7/100updates결과. GPU작업하나씩.

새도구initialize_stage(4CPU),fixed_reset(4CPU),full33comparison(2CPU),noise_probe_fine(normal/error2mock)는change-reviewer문제없음. baseline8CPU더해서18tests통과. 새full33stage지원하도록analyze_all자유분류/terminal/chart3곳만정정했고재검수승인.

영상아직새연구분0개:4A의free_v9 exportedcheckpoints실제hand/fullbody영상만publicvideo/seven_hour_v1로출판,중간log/pose/frames는R/renders. render_policy.py사용. 마지막보고서/원시로그QA/독립review/sourceSHA검증/plan체크완료필요.

## 06:10 KST 갱신(이 절이 앞 상태보다 우선)

seed17검지 A재현은100/200 둘다32/32·clean2.5초,통과완료;best200. GPU세션13348정상종료확인. 현재GPU세션10600=variance_variant2회smoke 실행중. functions store vrt=R/variance_variant/runtime, vp=기존prefix에서PYTHONPATH만그새runtime으로변경. smokeout=R/variance_variant/runs/smoke_factor005_u2. report.initial_transfer_audit에서weights/source동일+control CPU/CUDA RNG동일을확인한뒤sameoldA100→B100 variancefactor.05/seed7실행. 이후fixed4242 initial/final+freev9평가,oldcontrol actual105q/hold동일성검사필수. newvariantstrictmodule/README/source_seal은독립review문제없음+CPU7통과. sealed변경금지.

paired_B_initial/100/200_seed4242 실제q105/hold105 env별exactidentitySHA57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b 동일증명완료(R/paired_B_comparison.json). clean2.433854/1.888672/2.263672·32/32·fail0.

initialize_stage GPU검증: indexA100→free_v9/v9 export완료R/model_only/index_free_v9;학습0·transitions0·physicssteps0·freshAdam·가중치exceptmaskexact. 기존baseevaluate도32/32 clean2.496484로원래freeprobe와동일. 실제renderer로R/renders/index_A100_free_v9완료,publicvideo/seven_hour_v1의hand/fullbody6sec180frames각2개,checkpoint/source미변경. nativeenv0달성1/1 clean2.5초. 프레임3.5초손/전신검토완료:전신발까지포함,타깃검지blue관절MCP/PIP움직임있음.

시계열TIMING_ANALYSIS.md,json/png: 손목90%firstcross.233s는정착아님(초기overshoot→준비중box밖9mm). 손가락초반펴짐동시발생→2.5s경MCP/PIP굽힘→clean3.004s,달성4s. freev9에는강제phasegate없음. 팔명령상수IKbias이지만압현3→5.5s actualwristG21.14mm이동,기타root.72mm;유한PD/접촉동역학과learnedfinger구별. Note중 MCP41/PIP59/DIP13°로마지막관절만꺾임아님.

Fine잡음분석새도구fine_noise_analysis.py+FINE_NOISE_REPORT.md/json+chart.png 완성;480원시episodes/551pin검증,그림320noiseepisodes. 검지.05=32/32 clean2.439714,.1=31/32 clean2.107813.

현재structured_geometry agent는paired B0/100/200 유지감소원인 read-only R/B_BASELINE_DIAGNOSIS.md,json 분석중. implementworker새sealedvariance/fine분석완료idle. reviewervariance문제없음완료. full33_comparison.py+tests2+analyze_all3분류수정검수승인,대조군아직미실행. GPU대기열EXPERIMENT_QUEUE.md 참조. CURRENT_STATUS.md 신규연구문단수치갱신.

## 06:34 KST 갱신(최신우선)

현재GPU4717=full33_comparison.py (원RT/prefix),freshfull33 seed7 100+100 대조실행중. initial파일생성후old A7초기모델과active_mask외모든tensor/CPU·CUDA RNG exactequal 증명(full33_initialization_audit.json).

variance .05 smoke는첫KLguard실패0optimizer/0committed/lifecycletrue. 원본보존,성공으로세지않음. .1smoke2통과초기CPU·CUDA RNG control동일. Native.1 B100학습session8948종료0:513완료eps335safe/phys1/wrist0,LR7.5e-6~9.375e-6 retries3. 첫가중치sourceA100exact+cpu/cudaRNG controlTrue. 이후newv1CLI3평가모두완료:eval_factor010_initial_fixed4242 mean2.433854,finalfixed2.3729167,both32safe0fail; eval_factor010_final_free_v9 safe32/clean2.42265625/0fail. actualq/hold全32 exactSHA57a7... oldcontrolsame. 기존B100은1.888672이므로改善하지만B0최고2.433854/freeA1002.496484보다낮아최고source모델보존. 추가학습을자동승급하지않음.

compare_variance.py worker2reviewwarnings수정(2firstepisodeformat허용+sourceSHA/initialweights/cpuCUDA RNG+budget/completed+qpairfailclosedgate). 재검수문제없음. 실제완료입력으로collect후ready/eligibletrue는추가실험가능뜻,production자동반영아님. Main은writer만표broken수정·100개LR/KL arrays는JSON에두고MDsummarytable·trainingrewardlabel·B0stillbest 명시. 새renderdoc 갱신session18807. 별도focusreview필요. fine_noise_analysis.py 검수480raw문제없음.

다음개선 승인: arm_refinement_variant 새복사본만worker작성중(15-20min). 동일A100/.1/seed7/B100에서core.finger_encoder/heads/logstd+actor_extra 가중치만동결,arm/supportcore+가치망학습. 관절/출력은동적이고active_mask16(팔12+목표finger4)·native범위·PD·보상·guard같음. 새schema/explicitpins/settingsflag, CPUfixedobs fingerμ unchanged afteractualPPO 및optimizerdisjoint/armμ changes/RNGproof/free-v9strictbridge필요. oldv1sealed수정금지. worker인계후reviewer검수→GPU2smoke→100train/eval. full33session끝나기전GPU중복금지.

structured_geometry B_BASELINE_DIAGNOSIS.md/json완료: 오압현/법선veto/관절limit0;B100mean손실.545초=geometry減.277+load없음増.255+양끝연속차.014. env0 3초손가락이더펴져pad거리가5→36mm,첫contact+.283s지연+초반하중끊김. actorbranch보존다음실험근거. 다른A3모델free export/B0eval/render,seed17free/noise,최종전체리포트/실제영상/독립review는아직남음.

## 06:58 KST 인계
미디어12/12완료, 공개8MP4 원본SHA/ffprobe 검수통과. 중지/약지B0 32/32, 소지27/32. 손가락 함수 보존형 arm2회 smoke 통과(실제 .1 control 초기tensor/CPU/CUDA RNG일치), arm100 GPU session95362 진행. 이후 arm initial/final fixed4242와 free평가, no_alignment_prior100+100 대조 순서. full33 200실패는32/32 own_wrong_string2.5초(접촉부족아님); 100final→200initial model/Adam/allRNG/config완전일치. 최고100보존.

## 2026-10-31 07:58 KST 인계

현재 GPU 단독 세션63175: pinky_variance_variant/runs/pinky_B_factor010_seed7 100회 진행(2회smoke는완료, 실제pinkycontrol초기전체모델+CPU/CUDA RNG/원본A200sha일치). Prefix functions store pp/prt. 다음3평가 경로는 README대로 eval_initial_fixed4242/eval_final_fixed4242/eval_final_free_v9.

소지 기본 B100 완료: pinky_B_seed7_v1/100/train, stochastic513완결/96성공/실패1/mean safe clean2.2235055. 같은reset4242 control초기30/32 clean2.34375→최종21/32 clean1.640625, free-v9최종32/32clean2.5. B지지clamp와초기분포차이를섞어원인단정금지. 새unclamped_B_probe.py(sha947514...)가같은B16/aligned/source/reset에서press팔clamp만빼는진단, CPU6통과/structured_final_review 검수중. 추후원본Pinky B0/B100 및Index B0/B100 4조건실행가능. 생산/봉인원문변경없음.

no_alignment_prior full100/200완료: 각평균0/32/실패0, 확률학습706episode씩0달성·기타이탈314/303. 초기armbias외tensor/모든RNG, strictresume model/Adam/RNG 전부일치. 실제12축은왼쪽L_Thorax/Shoulder/Elbow/Wrist xyz(양팔아님). 기존full33 100평균32/32→200평균0은다른줄오압현2.5초; 학습블록평균은4/512→133/513로개선하나이는서로다른100개정책평균이므로최종고정stochastic가좋다는증거는아님.

시점별보상 native5조건완료: R/reward_trace/{full100,full200,full200_initial,index_A100_free}, noPrior는 R/no_alignment_prior_variant/runs/reward_trace_no_prior100_v2. mean32/모델불변/9항원시합정산<8e-7/Φ할인잔차<2.2e-7/실제q·hold전부정확대응. DISCOUNTED_REWARD_ANALYSIS readyTrue: full100및200initial rewardγ.99할인.179795369/32성공, full200 .015306221/0, A100free.179372776/32, noIK100.035836701/0. 비용γ1.0모두0. shaping비할인음수는γΦnext−Φprevious특성이라reward loophole아님. γ.99@60Hz반감1.149s/3초보존16.38%. actualq105/hold105는32환경전체unique1(ptp0)이라서nominalv9초기DOF자세반복이지32다른자세일반화아님; geometryagent가collectorJSON/MD에반영중.

NoPrior계측초기setup실패2건은반드시보존: R/reward_trace/no_prior100(output외부경로), N/runs/reward_trace_no_prior100(helper경로). native물리시작전portablepath오류. immutable reward_trace_probe.py SHA41b42... 원문보존. no_prior_trace_adapter.py SHA94bf8... 정확3helper경로만whitelist(native매핑우선/othersdelegate)하여v2성공, CPU2+독립검수통과. 실패는모델성능아님.

준비완료/검수통과(아직GPU없음): fresh_variance_variant/runtime (store frt/fp): goal4σ.1만변경 full33fresh(무A이전),114줄entry genericVariancePolicy재사용+freshmarker, CPU3/strictresume/실제초기모델RNG감사, seal4ad364... . GPU2회smoke→fresh100+100/control같은평가 계획. frozen_sampling_probe.py SHAb8c0ce... : immutable rewardtrace+noise_probe.sampling_override(scale1)재사용하여원본저장분포33축표본, 명확stochastic주석/pins/outputSHA/실패분모, CPU6+검수완료. 향후 sourcefull100/full200/A100free의고정stochastic32스냅샷으로평균정책과비교. R/DISCOUNTED_REWARD_ANALYSIS 파일은sourcecheckpointpins없음(보고서수정가능); 기존trace/fixed/noise/native봉인helper는완료자료pin되었으므로수정금지.

GPU권장대기열: 현재pinkyσ.1 100완료→3평가→frozenstoch3조건→Bunclamp4조건→freshσ.1 2smoke/100+100(실제native감사통과시)→full100/200native손전신영상(원래render_policy.py labels index_full33_100_free_v9/index_full33_200_free_v9)→가능하면seed17 A200 free export/eval/render. 각job완료확인후다음, 단일GPU. 예산학습마감10:27:53KST/전체11:02:53, 현재약3시간남음. 결과에따라Bclamp제거의격리학습개선추가여부선택, 불필요한시간채우기금지. 끝에masterFINAL_REPORT/selected_models/README/CURRENT_STATUS/review.json/source seals를정리·독립검수하고실제영상을제공. 생산guitar_learning기본값은변경하지않음.

## 2026-10-31 08:50 KST 인계(이 절이 앞보다 우선)

현재 GPU 단독33975=expected_angle/index_A100_free_normalized_action_mean. existingprefix/rt로R/expected_angle_probe.py CLI. 직전 A100free requested_angle_mean 완료(결과수집기는worker가추가finger section편집중이어서지금실행금지, 완료메시지후재집계). CPU집계중편집이겹친1회실패는selfSHAguard가정상검출했으며native결과무관.

fresh_variance100/200모두완료 nativeinitial 전체model/Python/numpy/CPU/CUDA RNG exact,strictresume model/두Adam/updates/allRNG exact. 기본full10032/32→2000/32, .1fresh1000/32→20014/32 clean1.0440104·fail0. 학습stoch164/512→373/512·fail0 vscontrol4/512→133/513·fail1. FRESH_VARIANCE_ANALYSIS readyTrue959pins,최고기존full10032보존.

소지.1 B도완료: B0 30/32clean2.34375→기본B10021/32clean1.640625, .1B10030/32clean2.34375,free양쪽32/32clean2.5. 학습96/513→490/512,fail1→0. B0초과안해서자동채택X. PINKY_VARIANCE_ANALYSIS readyTrue945pins.

중요발견: frozen_sampling 실제3조건완료/actualqhold exact/source/model0변경 검증 FROZEN_SAMPLING_ANALYSIS readyTrue. full100 mean32/32총/연속2.5,Gaussian7/32총2.405599/최장연속.834115; full200 mean0/32→Gaussian31/32총2.491927/최장연속2.140755; A100free mean32/32총2.496484→Gaussian2/32총.646094/연속.349479(A4학습→free33zeroexport여서추가축noise미학습한계명시,기존A4noise1도0/32). 그래프frozen_sampling_comparison.png를root가작성/시각검수완료.

firstfrozen full100은physics0에spimport전nestedpath미진입으로double-rootfile실패. 새wrapper2개(frozen/unclamped)최소수정+CPU7+독립review. 재시도full100_v2성공. 기존원본reward_trace/noise/모든봉인runtime불변. helper성공핀있으니이제수정금지.

핵심개선 expected_angle_probe.py (SHA e3b70ff9e092b8974c748b4949013ad4466e29b88ea5addb0dae300c88d1a596) CPU8+독립검수후GPU. modes latent_mean / normalized_action_mean / requested_angle_mean. 원본Gaussian μ/std유지+GH64/analyticfoldednormal로E요청각→기존codec역변환; inactive6유지,active33action/latent/logp동일지점검사. full200_latent_mean 원래mean8개trace배열/성과bitwise exact재현0/32. full200_normalized_action_mean0/32. **full200_requested_angle_mean32/32clean/best2.5/fail0**, full100 normal+requested둘다32/32clean2.5/fail0. Arequested완료,Anormal현재GPU. root선택결론은다른finger/seed까지regression대기이며보편해결/물리기댓값아님.

newrender_deployment.py/test CPU4+review완료,예시prefix R/render_deployment.py --checkpoint CP --label full200_requested --mode requested_angle_mean (stochastic/latent_mean/normalized_action_mean도지원). oldrender_policy.main재사용,실제mode태그/report/publication교정/argv·source·MP4SHA/3148seal검사. 이제성공전이지만검수완료. 기존3helpers절대수정금지.

대기순서: 33975끝→EXPECTED main7case집계ready확인→seed17원래full33fresh100+100(기존spCLI --song virtual_finger_v9_index_s3_f4 --geometry RT/guitar_learning/assets/structured_press_v2/catalog.json --stage free_v9 --size large --num-envs64 --updates100 --seed17 --out R/full33_seed17/{100,200}/train;200은--resume100/J/final.pt). 평가R/full33_seed17/evaluate/{initial_latent_mean,100_latent_mean,100_requested_angle_mean,100_stochastic,200_latent_mean,200_requested_angle_mean,200_stochastic};expectedhelper는고정μ/요청각,EAL scopes/collect. source7→17은seed만변경(A이전없음),사전학습RT/fixedIKbias유지. worker가SEED17_FULL33_ANALYSIS.py/md/json준비중.

추가finger평가예정: R/model_only/{middle,ring,pinky}_free_v9/J/final.pt source각A200, R/expected_angle/{finger}_A200_latent_mean + {finger}_A200_requested_angle_mean 6조건. 기존EXPECTEDcollector에별도other_fingers section/gate추가중(main7gate와분리). helperGPU공유금지.

아직해야함: unclamped_B4조건(동일B16/actualqpair에서pressarmclamp만제거;읽기helpers/test검수완료), full100/full200mean/native+full200stoch/expected대표native손·전신영상; selected_models.json/MD는reviewer가실행규칙별결과추가중; root최종단일보고서/README/큐/status/plan/budget/update/currentstatus+최종sourcepin/모든영상검증·독립review. 학습마감10:27:53,전체11:02:53. 현재생산코드는유지.

agents: implement_research_runtime(collector otherfinger+seed17완료후idle,render도구완료), structured_geometry(최신FULL33_MOVEMENT분석완료:env0DIP mean16.917→stoch19.078±2.084→expected19.275±.088deg,expected32safe;고정pad벡터분해도추가), structured_final_review(선택모델manifest2파일업데이트중,각도/optimizer/분석/렌더도구review모두통과). 새 GPU agent 없음.

## 09:18:43 KST (평가 queue 시작시각)
GPU 단일 순차 queue: remaining_evaluations_queue.json 및 queue_*.console.log. seed17 full33 100+100 학습 완료, 요청각200 평가완료. 남은16평가(seed17 5/다른손가락6/B16 5) 자동직렬 실행. 원본CPU36806 unclamped gate readyTrue. expected_B helper 검수+CPU4통과. 후속 영상4조건/최종문서검수 예정.

## 2026-10-31T09:40:46.761859+09:00
GPU session76185: fresh_variance_variant/runs/seed17 v2 train100→initialeval→100eval→stricttrain200→200eval. PreviousGPU58983render4allcompleted0. CPU NATIVE_VIDEO_QA delegatedgeometry, selectedmodel2filesreviewerowned. All16 evalqueue completed0, EXPECTED_ANGLE otherfinger gateTrue, SEED17_FULL33 gateTrue, EXPECTED_B gateTrue. Rootseed_executionplot reviewed. Failed firstseed17 bootstrap is prephysicsinputpin failure0transition preserved; v2 SHA4c1d9b2 actualpathCPU3+reviewpassed. No primary runtimechanges.

## 2026-10-31T10:06:06.474057+09:00
GPU session20528: seven remaining group evaluations run sequentially. First seed7_all completed and reproduced trace8 plus initial arrays exactly, source/model/qhold verified, original31/32. New probe4894769b/test8c35e581/collector300a1bcc passed independent review and CPU4 tests. Native33 normal draws and39 outputs preserved; only nonselected active groups become latent mean in hybrid diagnostics. All new training completed2408updates. Fresh.1 seed17 final0/32,10032/32: no adoption. Seventeen native MP4 and graph QA completed. Canonical RESEARCH_REPORT draft awaits final group results, final review, and completion tracking.

## 2026-10-31T01:17:16.104335+00:00 COMPLETE
All GPU jobs exited; no active training/evaluation. Final independent review passed,1345 input hashes and3148 frozen runtime files verified. Total2408updates/4931584transitions,63CPUtests,17publicMP4. Canonical RESEARCH_REPORT.md complete; old best/production defaults preserved. Deferred scope recorded explicitly in progress.json.
