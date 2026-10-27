# 손목의 회전과 팔의 위치 조정을 함께 비교하는 다음 단계

손목13source조건은8검사를통과했지만clear후보가없었다. 모든조건에서thumb2–guitar교차가남았고,특히Wrist_y−.1rad는thumb2 LP반경을4.288365→.815476mm로줄이는대신palm–guitar2.076522mm와추가fret/finger교차를남겼다. Cross-hands/self1188과palmar up은모두통과했다. 더좋은평면정렬만으로겹침없는지지를보장하지못한다. 이값은PhysX침투깊이가아니며이번source단계의actualnative/physics는0이다.

다음에는손가락의실제상대자세와기존offset을보존하고팔로손전체위치를바꾼다. 필요한경우손목회전과작은팔이동의조합도한묶음에서비교한다. 원손5관절baseline과,이번에thumb2교차가가장줄었던Wrist_y−.1rad source조건을두seed로사용한다. 두번째seed는채택된자세가아니라남은palm교차를팔위치조정으로줄일수있는지검사할가설이다. 실패한thumb1/2초기변화는승계하지않는다.

1. 각seed에서L_Thorax/Shoulder/Elbow의x/y/z아홉축을각각±.025/±.05rad로바꾼36조건과seed자체1조건,총74source조건을비교한다. 전체변화는originalbaseline기준으로기록한다. 초기float32각의실제delta를CoupledSnapshot arm12에전달하고기존실제finger1계층상대변환은그대로쓴다. 이는새범위의native정확성보증이아닌조건부source예측이다.
2. 첫seed는한축,두번째seed는Wrist_y와팔한축최대두초기각만바뀐다. 기존left33offset모두보존하고compose로全81held목표를재조립한다. 변경축외79또는80초기각·held목표exact,全81source/native/normalized교집합과손목sin±.005rad양끝을검사한다. 몸통9목표·root/하체·오른팔/손·기타초기fullstate·LA1.1018469719600776m·PD는유지한다. Thorax는기존66제어범위안이며Torso/Spine/Chest는움직이지않는다.
3. 각조건에서원sourcehuman–guitar/cross/self1188·palmup>0,손가락상대변환과비변경body/mesh를검사한다. 원baseline과두번째seed의HG결과를직전손목source결과에대조해재현성을먼저확인한다. 팔전체의움직이는body/geom은XMLL_Thoraxsubtree로유도하며handpad/top도identity대상에서잘못고정하지않는다.
4. Sourceclear후보는originalbaseline대비실제초기각delta의L2norm이작은것부터선택한다. 동률은palm/허용옆면패치·thumb3/후면패치source거리상한제곱합,soft평면정렬,고정조건순서로결정한다. Patch거리·정렬을실제접촉/자연성의인증으로취급하지않으며모든손가락동시접촉을강제하지않는다. Sourceclear없으면native0회로끝내고다음단계에서arm12의연속위치최적화를검토한다.
5. 선택한한후보만freshnative직접source HG/cross/self1188·palmup·全81actualq/PD/기타fullstate/root하체/LA를검사한다. 통과하면같은초기화에서1200step5초·두151frame30fps스트랩영상을기록한다. 거절이면0steppartial과실제겹침pair를보존한다. 별도source_prediction을actualbodypose와대조하되state를replay/덮어쓰지않는다. 예측오차가있으면원소스와실행을보존하고새버전에서원인을분석한다.
6. 5초가확보되면기타초기이탈·후기완전1초창변화·손가락각범위·palm방향·실제접촉을원quietbaseline과비교한다. 임시30mm/5°·후기5mm/1°와자연스러움/연주기능미검증을구별한다. 본목표는초기이탈축소와이후물리관절제어에의한유지및fret/strike연주전환이며sourceclear/범위호환만으로완료하지않는다. 기타고정/손부착/시작후pose덮어쓰기/인위적기타복원힘을사용하지않는다.

- [ ] 두seed재현·74source조건·全81범위/offset/비변경각·팔/손계층검사
- [ ] 최소변경한후보의actualnative직접검사·통과시같은초기화5초
- [ ] 기존실제quietbaseline비교·영상/문서·독립검수·후속결정

이계획은아직미실행이다. 예정새결과경로는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1 이다. 현재사용자자율진행지침에따라필요한조합을계획에먼저기록한다. 기존실험/공용자산은보존하고새구현만stability_adapter_2에둔다.
