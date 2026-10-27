# 손 준비와 시간창 커리큘럼 구현

사용자 승인: 가슴 접촉의 지속은 필수 조건이 아니다. 기타가 이탈하지 않고 연주 가능한 위치·각도와 접지가 유지되도록 한다. 준비시간 증가와 초기 성공 범위 확대를 허용하고 실제 구현을 요청했다.

## 범위와 기본 결정

- 기존 Root고정/하체유한·105/97/8·기타자유/중력ON/strapOFF·기존안전/물성/충돌/39출력범위를 유지한다. 가슴·삼중접촉은 진단지표이며 성공 필수조건으로 추가하지 않는다.
- native 정착2초를 유지한 뒤 **정책행동가능pre-roll1초**를 추가한다. u>=0을 물리/정책경과시간,곡시각t=u−P로구분. 실행목표에동일P를더하고원악보target/source시각을메타데이터에보존한다. 원50/100ms음악ledger는동일상대시각으로유지한다. 실제정책반응은native로새검증하며기존궤적시간이동만으로성공을선언하지않는다.
- 첫단음·LH/RH개별학습, 시간창±1.5/.5/.2/.1/.05초를고정된새단계실행으로구분한다. 성공률과결정적평가를확인한후다음단계명시전달; 실행중숨은window전환을하지않는다.
- LH는지정손가락/현/프렛의원래접촉후보를사용하고짧은연속유지부터악보구간유지로강화한다. RH는원래현/방향/깊이/속도/영역판정을그대로쓰며시간오차가작을수록보상을더준다. 완화성공과엄격음악성공은별도기록한다.
- 기존505관측·역할39출력을재사용하고, 새목적의reward이력을추가관측하여숨은상태를만들지않는다. Actor입력확장이필요하면활성Actor의첫입력행렬에0열을붙이는명시적이전으로초기응답을보존한다. task/관측시간규약변경을명시하고Critic/optimizer/counter는새로만든다. strictresume는완화하지않는다.
- 이번범위는구현·CPU회귀·독립검수·실제reset/step/초기화/짧은PPO와평가검증이다. 장기수렴·음향·다른곡일반화·양손결합성공을주장하지않는다.

## 순서와 검증

- [x] 최신지침·코드·봉인결과확인, 기존파일원형보관.
- [x] 타이밍ledger/관측가능이력·사전준비환경 구현 → 시간창경계/연속유지/중복/엄격판정독립검사.
- [x] BC/PPO명시이전·새실행/평가/단계설정연결 → 허용변경외거부/strictresume검사.
- [x] 전체CPU회귀·독립코드검수 → 발견결함수정후통과.
- [x] 실제양손환경·모델전달·짧은PPO/eval → 원자료·실패도보존하고조건/지표확인.
- [x] 구현/실행법/완료·미완료기록·독립검수, 이전봉인보존 사전감사.

코드는guitar_learning,검사는guitar_learning/tests,결과는docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1. 기존phase와원소스는수정하지않는다. archive/20261018_before_timing_curriculum/manifest.json에원경로와SHA를기록했다.

## 실제 연결에서 확인한 보완사항

- 직접 oldPPO→536입력확장 자체의동일관측응답은보존되지만, pre-roll로바뀐event/deadline/remaining입력에대한폐루프동작성공은보장되지않았다. LH직접이전native2회는u.183333s의기타80mm변위기준에서실패했다. 이를성공모델로채택하지않는다. oldteacher240행을새timing관측에서재생하고추가60행은마지막유한목표를유지해300행BC초기화자료를만드는연결을추가한다. 새BC실제평가와짧은PPO를분리검증한다.
- CPU_v1 230PASS/RH_initial_eval_v1수행중worker의optional소스보완이겹쳤다. old/new2파일모두archive/20261018_timing_source_interruption에보존했고exact핀원본복원했다. source_interruption_v1.json에기록, 해당CPU/RH기록은최종근거에서제외하고최종동결소스로다시검증한다. LH실패는수정전에완료했고입력무변경이었다. 원결과/실패파일은수정하지않는다.

## PPO worker 연결 검증

- 새BC정책은양손각2/2 native안전5초·완화단계성공. LH원음구간coverage1.0,RH최초목표down+19.449ms. fit목표1e−6는미달(True수렴으로보고하지않음).
- 첫PPO스모크v1은freshspawn의lazy compact logger순환으로update0에서실패했다. archive/20261018_before_timing_worker_v2에원runner/tests보관,새train_timing_v2가원base logger를먼저import하도록수정. freshsubprocess재현·dispatch복원2검사통과후새PPO스모크v2와전체CPU_v3를진행한다. v1원자료/실패/복구모델은보존하며학습성공으로집계하지않는다.

최종동결CPU_v3 238통과. 새BC양손각2/2안전성공,스모크PPO_v2각1up/300trans와결정적각2/2성공·입력무변경. LH원audiblecoverage1.0/RH최소목표오차17.42178ms,원jointmusic0. 현재stage0의연결검증이며전체5단계학습/수렴/양손결합성공은미완료다. 문서와최종보존명세를정리한다.

최종독립검수미해결항목없음. runtime_analysis의인증10episode/12000physics검사전체True,1658pin union충돌·현재불일치0. 원음악판정과완화stage0성공을분리했고실패/소스중단기록은성공통계에서제외했다. 마지막source byte snapshot·artifact inventory·final_verification_v1.json명세생성으로이번구현과검증을봉인하며이후파일을수정하지않는다.
