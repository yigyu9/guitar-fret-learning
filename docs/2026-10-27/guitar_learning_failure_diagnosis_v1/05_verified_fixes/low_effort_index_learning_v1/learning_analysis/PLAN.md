# 검지 낮은 상한 fresh300 학습·고정 평가 분석

- [x] root train+7eval 전체실제종료 통보 전에는 학습raw를 읽거나 최종 결과를 만들지 않는다. 준비/프로브/실제precheck분석 전체·source·이전결과는 동결하며 이새 learning_analysis/만 수정한다.
- [x] `02_train_eval_launcher.json` completed/returncode0 및 train/evaluate_000000/000050/000100/000150/000200/000250/000300 순서8child의 실제exit0, 각8scene native128×105/90pairs·상한·입력·alias·닫기·strict계약을 검증한다.
- [x] 전체300 metrics·1,228,800 K1 raw전이·종료episode 전부/실패를 감사한다. 글로벌control9600tick/physics38400step과128환경 합산전이를 구분한다. reward9개 각각의 raw평균과 전체episode항·합산잔차/비용·critic학습을 기록한다. 원gamma/costhead/PPO를 변경하거나 head0으로 덮지 않는다.
- [x] fixed7×128=896첫시도 전부를 분석한다. NN initial0 대비와 비NNGaussian random31/128 대비는 별도이며 서로exact초기정책으로 부르지 않는다. 원criterion 달성≥90%·평균clean≥90%·평균wrong≤10%·물리/손목실패0을 각각검사하고, 학습후고정50/100/.../300의 인접2평가통과를수용기준으로한다. 초기0은기준선/전체공개대상이며학습후연속쌍에는넣지않는다.
- [ ] **영상 사전선정순위**: 초기0포함7평가를모두공개하고 best를 `(달성률,평균clean,−평균audiblewrong,−물리OR손목실패시도비율,update큰순)` 내림차순으로선택한다. 두실패가겹친시도는1회로센다. latest300은별도다. best==300이면1모델,다르면2모델을동일128장면env0손/전신native영상으로저장한다(root만실행). 단일best와연속2pass수용은구분하고낮은평가를삭제하지않는다.
- [x] 고정7각env0 60Hz trace에기존검수 helper.trace_audit/arm_audit를재사용한다. selectedtarget/actual·gate/손목·armbounds·body1/2/3합력·과도한목표/추종차이를기록한다. 나머지127환경 상세force는추정하지않고전체128의저장된각도통계와env0상세를구분한다. 몸체합력을접촉쌍압력/모터torque/240Hz최대로부르지않는다.
- [x] actualinitial73tensor를원동일seed7/large/index1 CPU초기화와비교하고 저장본identity/source핀·원costhead/gamma를확인한다. CPU분석에서CUDA RNG를우회하여재개하지않고실제native평가의원strictload완료와CPUidentity대조를구분한다.
- [ ] 분석/그래프/전체분모/입력SHA를새 results_v1/에저장하고별도실제검수. 통과해도고정기타·유한팔/손목·검지단음·seed7 조건이다. 자연스러움/해제·다음음/다른손가락/자유기타/J33/전곡은별도미확인으로남긴다. 이후seed17재현과원곡시간전환을따로진행하며이분석중설정변경/추가GPU는하지않는다.
