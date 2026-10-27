# 위팔의 앞모서리 접촉 후보

source9/10의RShoulder source법선은GlocalX지배적이고worldZ성분+.966/+.953이다. 주로위에서누르는접촉이며Chest와RShoulder의초기법선각도는41.6/49.8°로마주누르는배치가아니다. 실제cooked마찰/3Dtask와같다고확정하지않는다. 정지V11(중앙배치)도5초·각도·안전통과/Chest0으로실패했다.

source11은source10의Root/body/Head/왼팔/lower24/zero8/G/의자/형상·물성을그대로두고오른팔12유효축만다시IK한다. RPalm기존world pose를우선보존하고RShouldergap.4mm/법선GZ≥.65/RElbowgap≥8mm를목표로한다. GZ는기타앞뒤방향이며G_X/world_X와혼동하지않는다. 유한한팔목표/접촉만사용하고기타직접힘/고정/부착/상태overwrite는없다. 왼손sourcegrasp는그대로다.

sourcehardgate:Rpalm오차5mm/2°안,frontnormalGZ≥.45/gap.05~2mm/forearmclear,원범위/lower24·zero8exact,새sourcecapsule/box/foot검사. 목표가실패하면native미사용. 통과시기존controller10/scene8/preload−.08/normalChest20/RShoulder3D20을먼저같게두고정지5초후실제Chest/RShoulder접촉·각도·안전기준을판정한다. 성공후15초해제,실패보존/PPO없음.
