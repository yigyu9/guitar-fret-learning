# 정면 자세 source8: 초기 직립 여유와 기타 지지 배치 공동 조정

source7은발/상체정면과형상24gate를통과했으나 초기몸통4.8°로실제5°기준여유가작았다. native1은정면·발·기타지지를유지했지만Chest5.31°로실패했다. 초기source7불변인finiteChest-onlytarget1은가슴지지가0%가되었고,Torso/Spine5°를넘었다. 공동몸통직립target2도기타회전7.227°/몸통5.383°/우측3.091°/Spine5.096°/지지로실패했다. 세원자료/코드/입력/목표/검수는모두보존하고채택하지않는다. 각도목표만바꾸는후속을중지하고새초기형상부터검사한다.

새source8은source7의Root/좌석/하체24/손가락/원영범위8축과공용자산을고정한다. 발정면/평평한접지형상은이미원자료로확인된새발목값을유지한다. 몸통9+오른팔12+기타초기pose6을공동으로맞춘뒤왼팔12와머리6을보상한다.

사전설계조건:
- 초기Torso/Spine/Chest tilt≤3.8°,right≤2°,heading≤2°로원실제5°/3°/5°에여유를둔다. Head/네발body도heading2°유지.
- 초기G는source7대비actor위치변화norm≤10mm,전체회전≤3°범위에서기하학적으로조정할수있다. 넥고도목표0°/초기허용1.5°,기존원hip/Pelvis기준lateral오차≤2mm를요구한다. 실제3°neck/20mm lateral/30mm이동/5°회전기준은완화하지않는다.
- 오른팜은새기타좌표에서기존목표와변화15mm/6°를허용한다. 이전world palm5mm/2°는현재사용자필수제약이아닌재현참조였으며,가동범위한계와상체직립·지지형상확보를위한새설계선택으로분리한다. 왼팜은새G상대참조5mm/2°를유지한다. 새연주인증은상속하지않는다.
- Chest양의간격.5~.8mm근방/Spine≥5mm(선호5.5~6mm)/RShoulder.5~1mm/RElbow≥7mm/RHip및모든활성support비관통,원105범위/zero8·실제nativefilter·capsule/self/BOX/G/의자/바닥검사를float32전달값에서다시검사한다.

G배치는초기한번뿐이다. native에서기타는자유강체/중력ON/스트랩OFF이며직접힘·고정·부착·매stepstate주입·PPO는없다. 기존bodygain/cap/rate·하체안정제어는바꾸지않고새candidate에서유한anchors만초기화한다. rightworldaffine/Hipbias구숫자는검증전가설이며새candidateSHA로새spec을발행한다. 초기형상검사와native준비5+정지5성공을구분하며실제기준25개/동일설정반복을끝까지검사한다.

소비한계획·실행코드·결과는수정하지않는다. 실패는새source/target/native버전으로남긴다.
