# 자유 기타 V5: 새 기타 기하에 맞춘 양팔 초기 정렬

V4는source2 Spine5mm/Chest.3mm로시작했으나실제정지5초Chest지속접촉0. 기타회전1.1557°/이동5.8987mm/전체넥max1.00885°/상체3.8376°/발통과이며,초기넥1.0088°가settle에서는약0°로돌아왔다. 전human q를유지하여Foot대비왼palms-G상대위치9.57mm/회전1.215°차이가남아있다. 고정된손목표와새G초기배치의불일치가기타평형을옛방향으로유도하는지분리확인한다. 이는가설이며raw접촉/회전축을대조한다.

## 새source3 범위
source2의Gpose/몸통·머리·Root·좌석·하체·손가락q를그대로두고양팔12축씩(Thorax/Shoulder/Elbow/Wrist)만원본가동범위안에서refit한다. 양palms의Grelative p/r를FOOTsource3의상대기준으로복원한다. 오른상완 sourcegap .5mm와전면접촉범위,Elbow여유도검사한다. 새selfcollision은기존원본parent/exclude/filter정책으로감사하며왼팔몸통간새교차가있으면선택하지않는다. lower24/zero8/원105순서는보존한다.

새upper_deltas는실제81관절원reference에서재계산해native초기exact검사와연결하고새upper_target105는새initialq에맞춘다. 예상전체human state는calibrated fullFK로만생성한다. source3는source2와동일G·기하목표이나팔q가다르므로모든capsule/convex·selfpair·BOX/좌석·지면감사를새로수행한다. handmesh완전인증은하지않고palms재정렬허용오차≤5mm/2°와실제native초기/contact/safety를분리한다.

## 제어와검증
V2 initialworldright/Chest기본3mm/gain/cap/성공발제어그대로다. 새candidate/refsupport/upperq/refSHA만새입력으로준다. 기타G직접힘·고정·강제부착·매step상태덮어쓰기없다. source변경은초기조건이고실제인체는유한제어로움직인다.

- [ ] source3원래limits/zero8/onlyarm24/하체·Root·좌석·몸통불변/손정렬/전체활성pair·SHA검사.
- [ ] 독립검수후실제static5초V5,기존15gate모두유지.
- [ ] Chest+상완/Spine/Hip/왼손접촉및Gneck변화를V4와비교.
- [ ] 전체성공재현후압현·타현·해제;static실패중PPO없음.
