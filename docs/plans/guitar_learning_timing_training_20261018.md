# 타이밍 학습 진행과 로그·실제 결과 분석

사용자 요청: 학습을 진행하여 제대로 학습되는지 로그와 결과를 분석한다. 직전 구현/스모크 성공을 장기 학습 결과로 재사용하지 않고, 확인된 새536차원 BC Actor에서 시작한다.

## 실행 조건·예산·판정

- native정착2초+policypre-roll1초,전체policy5초/300tick,firstsingleoriginaltarget(물리2번줄/7프렛/약지/down),536입력/39출력/medium. Root고정·하체유한105/97/8·기타자유/중력ON/strapOFF·원물성/충돌/범위/제어/안전유지. 가슴접촉/삼중접촉지속은성공조건으로요구하지않고진단으로기록한다.
- stage0±1.5초를손별N2/H300/24updates/각14400trans上限/soft2400초/seed7,초기std.02/cost1/actor_lr1e−5로수행한다. 설정·소스·초기BC·중간4update주기모델·전이·진행/자원/물리결과를보존한다. 이미통과한238CPU검사를소스변경없이반복하지않는다.
- 원BC기준과중간checkpoint,최종policy를비교한다. 각역할update12시점checkpoint와final을원래samepreparedstart에서결정적2회검증한다. 학습탐색episode와결정적검증을분리한다. 안전종료·현재단계성공·LH원onset/end유지율·연속유지/해제·RH최초목표cross오차/최소오차/독립50/100ms/추가통과·원jointmusic·기타/발변위/접촉·KL/실효lr/criticloss/처리속도/메모리를기록한다.
- stage0성공률만100%여도개선으로설명하지않는다. 초기모델과동일단음/준비조건의변화이며일반화/음향/양손동시성공의증거로확대하지않는다. originaljointmusic50/100은반대손조건도필요하므로독립기하timing판정과구분한다.
- 최종현재단계2/2안전성공·LH각원음coverage>=.95/RH각최초목표방향오차<=.5초일때stage1±.5초새계약의actor-only이전평가2회를수행한다. 성공하면각N2/H300/12updates/각7200trans上限/soft1500초로이어학습·최종2회검증한다. source/critic/optimizer/counter기록을별도로남기고strictresume로속이지않는다.
- stage1이전이실패하면원인을확인하고,필요하면기존scriptteacher를같은새계약에서재생·BC로재초기화한후반복평가한다. 실패/재초기화범위를명확히분리하며비교조건이나안전기준을몰래바꾸지않는다. 무리한자동승격은없다. 이번예산은stage0과조건부stage1이며전체5단계/곡완성을요구하지않는다.
- 진행중소스변경금지. 새구현결함이필요하면실패원본·sourceSHA를보존하고새버전으로한다. 결과생산용분석스크립트만이번phase에작성한다. 장기학습은외부GPU/hostresource를먼저확인했으며시작시GPU0사용·availableRAM약28.8GiB다.

## 순서

- [x] 최신매뉴얼/코드/직전봉인결과·초기모델·자원확인,계획과보관.
- [x] stage0양손학습·로그감시·중간/최종native평가. 각24updates/14400trans완료,학습목표LH46/48·RH48/48,물리실패0. update12/final각2/2안전단계성공,finalLHcoverage1/RHfirst17.680344ms.
- [x] 결과에따른stage1진입판정·필요시재초기화·조건부학습/평가. 재초기화없이각12회/7200전이,최종2/2안전단계성공.
- [x] 로그·실제정책·초기대비변화분석과그래프·결과·모델경로문서. 종합README·모델SHA목록·단계별분석·시간분석작성.
- [x] 독립검수·소스/원자료/이전결과보존감사. 독립최종문제없음,소비입력1650/SHA일치·16closedscene·168reset·모델counter검증·source143snapshot완료.

코드는guitar_learning.train_timing_v2/evaluate_timing기존동결버전,결과는docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1。기존phase와checkpoints/실패는변경하지않는다.

## Stage0 완료 후 판단

양손24회최종평가가계획gate를통과하여 stage1_entry_decision_v1.json 에근거와SHA를기록했다. source는각stage0final PPO Actor,critic/optimizer/counter는새로만드는이전사전평가2회를진행중이다. stage1성공으로미리설명하지않는다. 중간분석검수에서최종evalcheckpoint업데이트수일치검사를추가해분석기v5로별도보존했으며학습source는불변이다.

## Stage1 착수

stage1계약Actor이전평가양손2/2안전단계성공,LHcoverage1/RHfirst15.712061ms. 이전직후의stage0대비차이는추가PPO성과로집계하지않는다. stage1_training_decision_v1.json에근거SHA를기록하고각12updates/7200전이상한학습을시작했다(2026-10-18UTC11:35). source=stage0final,critic/optimizer/counter는fresh. 재초기화없이진행했다.

## 최종 실제 결과

stage1최종양손2/2안전단계성공,LHcoverage1/RHfirst12.285673ms. 같은stage1preflight15.712061ms대비3.426388ms개선이며추가up/down은남았다. 총43,200전이/144학습episode,목표LH70/72·RH72/72,물리실패0. 최종결론은초기성공유지와소폭타이밍개선,다음음전환/필요해제/추가타현억제미해결이다. 여섯개생활문서는보관SHA검증후최신결과링크를추가했고새 documentation_update_v1.json으로before/after를기록했다.
