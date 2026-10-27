# V10 실제시험: 포화압력 이후의 유한 Chest 방향 목표

V9 schedule8→10mm에서last1 actualvirtualnormal20N cap100%인데Chestsourcegap.032358~.062496mm/실접촉0. 실제전체Chest최대4.86548°는1.541667s,종료Chest약4.6°. depth추가로는같은20N이라무효이며중단한다. 기존실패와source4는보존한다.

## 새유한인체목표
초기candidate/105q/G/Root/chair/발은source4그대로다. 실행목표upper_target만Chest3을worldhip-right축의전방+.2°로calibrated fullFK fit한다. suffix를world축으로해석하지않는다. 기존순수query에서+.2°는initialChestgap.300026→.182354mm를줄이고Spine5mm는그대로였다. LH팔/손가락고정시palmworld변화는약.79mm. 필요시활성selfclearance와LHworldpalm유지를위해leftarm12만작게refit하고명시한다. 오른팔은기존actualinitialworldIK가유지한다. upper_target은초기state가아니라유한PDgoal이다.

상체각여유를위해virtualnormal의startup은검증된7mm로낮추고.75..1.25s에9mm로늘린다. K150/D1/cap20/원jointcaps/footstablePD/worldright는유지. 실제7mm시험V6max4.6028°에+.2°기하추정을더하면약4.79°,schedule9mm의settled4.54°에더하면약4.73°로5°안여유를기대한다. 이는서로다른제어/기하의단순예상이며실제성공보장이아니다. 세목표변경(Chest방향/startup/finalpreload)의개별인과기여를분리주장하지않는다.

## source target 검증과실제기준
새posture_target_v1 producer는원105limits/zero8/하체·손가락·Torso/Spine·초기후보불변, Chest방향/손변화와활성caps/convex/self·BOX·chair를실제nativefilter로감사한다. initialsource검증과targetFK예측,actualnative지지를구분한다. newtargetSHA와입력을pin한다. 기타직접힘/고정/부착/매stepstate쓰기0.

- [ ] 새targetproducer/좌표·FK·clearance/입력beforeafter/independentreview.
- [ ] 신규runtime_v11(7→9mm 동일springpreload식)/wrapper/analyzer/compile. 변경된목표로prefix동일성은기대하지않는다. 기존15criteria+schedule/KD/target정합은유지.
- [ ] native_static_v10 actual5초. 전0..5G회전5°/넥3°/몸통total5°/right3°/이동30mm/lateral20mm,1..5Chest+상완95%/양발95%/last1발4parts 기준완화0.
- [ ] 전체통과재현→압현·타현·왼손해제. 아직PPO0.
