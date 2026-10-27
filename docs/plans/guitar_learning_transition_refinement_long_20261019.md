# 보완 정책 장기 학습과 결과 분석

사용자가 어느 정도 길게 직접 학습하고 결과 분석하도록 승인했다. 기존 보완 경로의 단음 A를 대상으로 하며 두 음 전환·전곡 성공으로 확대하지 않는다. 기존 입력·소스·모델·실패 자료는 보존한다.

1. [x] runtime SIGFPE를 우선 확인. 동결 코드/설정으로 GDB 없는 새 native 재생을 실행하고 기존 오류와 구분한다. 물리·측정·오류 판정을 약화하지 않는다.
2. [x] 새 독립 native4회와 원자료/보상 감사, 성공자료 구성.
3. [x] 1환경/1update 저장·재로드 확인. 필요하면 최소 변경을 새 버전에 구현·별도 검수한다.
4. [x] 8환경/H240, 목표128update=245760전이(단음4초1024episode), 최대3600초의 장기 학습. 초기std0.003/ActorLR1e-7/stdLR1e-5/BC가중100/기존KL과물리안전 유지. 메모리·진행·평가·실패를 관찰한다. 실제 결과와 설정을 근거로 예산을 조정할 경우 새 실행으로 구분한다.
5. [x] 저장 모델의 결정론적 재평가, 음악/안전/BC/std/학습·수집 계수 분석과 보고.

기록: docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/

완료 조건은 실제 학습/모델 평가와 로그 분석이다. 실행 불가이면 원인·실행 범위·남은 검증을 명시한다. 재현 불가한 성공이나 중단 전 partial 값을 완주로 보고하지 않는다.

## 실행 차단 보완 기록

- 기존동결경로 직접재생1회100%완주/다음재생JSON SIGFPE. 최초runtime Decimal17은 값bit은보존했지만canonicalJSON표기SHA가달라 기존BCvalidator에서정상거절됐다. 실패와소스66파일은보존했다.
- 새 runtime_v2는 NumPyDragon4로 원JSON숫자표기/SHA를보존하고Fraction파서를사용한다. FP제어값읽기전용·이상상태실패·native감사·새4gate·모든worker종료감사 유지. 원인해결이아닌formatter노출회피다.
- 실제oldBC증거검증을새codec에서수행하는검사포함68개40.348초통과, 100k임의/경계float repr일치·실제계약SHA일치·GDBhotspot미진입검증. 별도change-reviewer미해결Critical0.
- 원본66포함79파일을runtime_source_snapshot_v2/runtime_source_pins_v2에동결했다. 새native4회는runtime_v2_native_init_v1..v4, 이어갈설정은smoke_settings_v3.json/long_settings_v3.json이다. 현재4회진행중이며아직새PPO미시작이다.

## 현재 실행 상태 (runtime_v2 native4 완료)

- runtime_v2_native_init_v1..v4 독립프로세스4/4완주, 모두cleanhold1.0/release1.0/safety통과. 각runtime관찰anomalyNone. 첫case의기존native관측/물리/새보상원자료감사도240행통과.
- smoke_v1 실행중: PID3664529, 설정smoke_settings_v3.json, 로그smoke_v1.log. 초기필수감사에서4case 전체를다시검증중이다. out폴더는이감사가완료된후생성된다.
- 이후 smoke final.pt를동일설정으로새eval에strict재로드한뒤 long_settings_v3.json/long_training_v1로8환경 장기학습을진행한다. 이시점에는아직장기학습미시작이다.
- 모든실제실행은 guitar_learning.transition_refinement_runtime_v2.run을사용한다. 잘못된canonical표기v1실패를새실행과혼동하지않는다.

## 장기 학습 시작

- smoke_v1: 실제240전이/PPO1update/저장/worker종료감사 통과. 첫탐색episode는hold0/release1로음악실패.
- smoke_checkpoint_eval_v1: final.pt strict재로드와 실제4초완주 통과, cleanhold1/release1, runtimeanomalyNone.
- long_training_v1 시작 PID3668784. long_settings_v3.json,8환경/H240/128update상한/학습wall3600초,원BC Actor에서새시작(연결시험모델을재개하지않음). 로그long_training_v1.log. 검증79파일불변. 시작UTC는long_training_launch_v1.json.
- 아직장기초기감사단계다. checkpoint_000007.pt=8optimizerupdates, checkpoint_000031.pt=32updates. 중간과최종정책별native평가를별도새out에수행한다. 예산3600초때128회에미달할수있으며실제committed횟수로보고한다.

## 비교 실험 A 종료와 본 장기 실험 B

- A=long_training_v1은8update후학습률256배감소가그대로이고KL1e-8수준이라정책이거의변하지않았다. 64완료중31성공(48.4375%),평균hold.604427,release64/64,physical0. Critic EV개선/비용adv신호표준편차가보상의1.3~2.4%라안정성비용압도증거없음.
- checkpoint_000007.pt 저장이끝난다음nextindex8tick0의parentPID3668784에만SIGINT. source/원자료수정없음. report.completedFalse/stoppedinterrupted는의도적이며수치오류가아니다. sampled15464/committed15360/discarded104,8부분prefix는완료성공분모에서제외. 8worker별runtime감사모두정상.
- A분석 long_analysis_at8_v1/, 모델평가 pilot_checkpoint8_eval_v1(4episodes) PID3676001 진행중.
- B=long_training_v2 PID3675500 새시작. long_settings_v4.json은epochs1/fullbatch2048(1920samples)/stdLR.001만변경. ActorLR1e-7·BCweight100·초기std.003·원정책·관측·목표·보상·물리·4gate불변. 새BC Actor+freshCritic/Adam으로시작(다른PPOidentity로resume하지않음).
- 별도reviewer: 변경근거적절/차단Critical0, optimizer변경이므로같은BC4gate유효. critic도16→1update로줄므로valuefit확인. 세변경묶음의개별인과를단정하지않는다.
- B는실제학습wall최대3600초/128update상한으로계속진행,중간checkpoint8/32와최종strictnative평가. A의중단을B중단으로혼동하지않는다.

## B 실제 학습 첫 업데이트

- B원자료전검사·8worker초기화완료. 첫rollout은A와동일5/8성공. 실제epoch1/fullbatch1step에서KL.0018134<.005,backoff0,ActorLR1e-7/stdLR.001유지. Stdmean.0029995467, BCMSE2.9066e-10. 지속유지/성능개선은추가학습으로확인한다.
- 초기4회/실제fullcapture감사/1PPO업데이트·저장·strict재평가 완료. 아직남은것은B장기학습완료와중간·최종모델평가/분석이다.

## B 16회 시점과 중간 평가

- 실제16update/30720committed전이/128완료episode 중65성공(50.78125%),physical0. 학습률Actor1e-7/std.001유지. 아직음악개선결론없음.
- A checkpoint8의pilot_checkpoint8_eval_v1과B checkpoint8의long_v2_checkpoint8_eval_v1 모두4case완료/hold1/release1/runtime관찰정상. 반복은각평가내동일persistentenv reset이며4독립process초기평가와구분한다.
- A와B 첫8비교는31/64 대32/64, 평균hold60.44%대56.85%. BC시연오차와표준편차변화가작고현재costadvantage분산은reward의약2%; BC지배나안정성비용압도를단정하지않는다.
- B는설정변경없이학습wall3600초까지진행. 다음checkpoint32와최종모델평가후실제수치로결론작성.

## 평가 해석 제한 확인

- 현행probe는settings seed설정후checkpoint.load가저장RNG를복원하고case마다다시load한다. 따라서evaluation_mode stochastic만바꾸고seed를달리해도초기/최종동일탐색난수대조나독립noise반복이되지않는다. 이비교는시작하지않았고봉인소스는수정하지않는다.
- 현재4case결정론적평가는같은환경의reset반복에서기본동작보존을확인하며,독립seed8회견고성증거로설명하지않는다. 향후별도버전에서strictload후case별평가seed를기록/적용하는평가가필요하다.
- B첫16회원자료진단:128완료/65성공63실패,실패모두마지막200ms의prepare_ready_s0(완료시각아닌누적접촉기간). 실패중41은clean관측없음/22늦은접촉. release128/128/physical0. 기타최대3.616mm/.5355deg,전체지지및양발접촉소실0. 상관관계이며인과확정은아님. long_v2_failure_diagnostics_at16_v1/참조.

## 외부 공유코드 변경 감지와 격리 복구

- UTC11:26:14부터다른작업의dependencyinternalization으로공유코드가변경됨. checkpoint32 첫eval은원BCinputs검증에서정상거절되어실패원자료보존. 우리코드변경/guard완화/원작업되돌림없음.
- 호스트B를ownedparentSIGINT로중단:36update69120committed/368discard,report.completedFalse/changed_inputs31개. 이실행을정상원무결성완주로보고하지않는다.
- guitar_learning/archive/20261019_before_dependency_internalization의334파일과B시작의1907입력을정확한SHA로frozen_execution_view_v1에복사. bwrapnamespace에서전체package와외부입력1615파일을읽기전용으로원래절대경로에제공. 실제1907/1907SHA검사통과(return0),호스트현행파일유지.
- checkpoint32는UTC11:25:36저장으로최초외부변경보다앞선다. 여기서PPO/optimizer/RNG strictresume하고nativeepisode는새시작한다. 새C설정isolated_resume_settings_v1은max_wall_seconds만3600→1200,그외구조/보상/탐색/BC/gates/PPO동일. 모든원검증을격리view에서그대로수행한다.
- C성공은B의과거소스무결성을소급복구하지않는다. 비교시B0..31진단과C의local/누적optimizer index·분모·새reset범위를명확히구분한다.

## 최종 완료 상태

- C 정상종료 completedTrue/wall_budget,1247.157초/추가14updates/global46,112episodes56성공(50%),26,880sampled=logged=durable=committed/discard0. core/persistent/teacheraux/runtime부모+8worker 모두통과. 독립검수보고서·workerSHA일치.
- 비중첩앞7/뒤7 성공29/56→27/56,hold56.9494%→54.4196%. 개선·악화확정불가. 실패56모두prepare_ready_s0이며neverclean41/늦은음구간10/종료후5. 기타최대3.610mm/.5393deg,지지·양발접촉소실0.
- 최종46 native격리재평가4case모두안전완주/소스·runtime감사통과, 음악성공3/4(hold1,0,1,1;release모두1). 비교32모델은4/4. 32를참조로유지/46및실패모두보존. 독립seed·범용성·통계우열주장없음.
- B32+C14 모델계보46updates/88,320전이,collection벽시계합58.3228분. B전체무결성실패·중단은소급복구하지않으며정상검증C분은별도26,880전이.
- 최종문서: docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/README.md. 원자료/실패/모델/격리snapshot/해시/실행argv/분석그림보존. 새보상·정책·자세·두음/전곡학습추가작업없음.
