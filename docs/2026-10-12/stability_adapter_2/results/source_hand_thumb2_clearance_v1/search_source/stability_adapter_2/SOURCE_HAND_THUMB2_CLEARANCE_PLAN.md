# 제어 범위 안의 초기 손자세에서 엄지2 겹침 해소

fixed_strap_source_hand_initial_v1은5관절source/native범위숫자조건을충족했지만fresh native t0의LH:thumb2–guitar source교집합으로0step거절됐다. 공통내접반경0.004288364821171085m는LP형상진단값이며PhysX관통깊이가아니다. 기타초기p/q·root하체·PD·몸통9목표·LA1.1018469719600776m·다른관절은현재값을유지하며엄지2단일hinge만먼저진단한다. 목표는범위호환만이아니라겹침없는지지를되찾아실제기타오차를줄이는것이다.

1. 실제거절장면의native전체state를고정참조로사용한다. Thumb1다축5관절은더바꾸지않는다. CoupledSnapshot의기존검증된scalar thumb2만사용해zero delta의실제bodypose동일성을먼저확인하고thumb2 초기0.3384127914905548rad 기준delta0/±0.05/±0.10/±0.20rad의총7조건 source형상을비교한다. 기존18좌표FK를새finger1변화에적용하지않으며현재finger1실제local변환을그대로기준으로쓴다. 변경thumb2의source/nativeeffective범위0..1.1171258687973022rad를유지한다. 전체source human–G/cross/self1188·palmup과thumb2/3의넥패치거리를기록한다.
2. 겹침을해소한조건중최소|delta|,동률이면엄지의넥후면패치거리작은것을한후보로선택한다. 아직접촉이아닌source거리임을구분한다. 해당thumb2초기각과유지목표를같은값(offset0)으로해시작부터의추가thumb2relaxation을없애고다른80초기각/목표와기타초기p/q·LA/PD/손목파형을보존한다. 숫자교집합조건도다시검산한다.
3. 한후보만fresh native직접gate로검사한다. 실패면0step실제초기이미지/거절을보존한다. 통과면같은초기화에서actual5초/두151frame30fps스트랩영상을저장해원래52.09°quiet지지와초기기타이동·회전/후기변화·접촉/손자세를비교한다. 추정FK를native접촉인증으로사용하지않는다.
4. 7조건모두겹침이면이탐색에서native를실행하지않고엄지2만으로해소되지않는근거를보존한다. 이후엄지기저부나손목의변경은새계획에서실제초기pose로검증한다. source범위를다시벗어나거나기타/손을고정하는방법으로통과시키지않는다. 학습·새보상·추가외력은이단위에서사용하지않는다.

- [ ] 7조건scalar source검사·zeroidentity·조건별이유
- [ ] 한후보준비 또는범위내해소불가판단
- [ ] 필요한경우fresh native직접gate와같은초기화5초
- [ ] 실제결과/이미지·영상/독립검수·다음제어방향

이번후속계획은아직미실행이며결과경로는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v1 로예정한다. 기존거절phase와모든원본을보존한다. Source필요조건이나임시자연구역을연주성공으로확정하지않는다.
