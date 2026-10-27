# 전경 목표의 가슴 접촉 높이 보완

upper_target_v1은native초기변경이아닌미실행제어목표로Torso/Spine/Chest모두4.2°를계산했다. 양손오차는1e−9m미만이나목표sourceChestgap은−1.531mm여서현재동적gap약3mm를확실히줄이는여유가작다. 원target/보고서/소스를보존하고v2는Torso/Spine4.7°,Chest4.2°로부모위치와가슴원점의접근을조금더허용한다. 모든body오른쪽목표0°,모든total목표5°안이다. link방향차이는.5°로작고모델의해부학적offset을삭제하지않는다.

양손world pose와Head방향보존을다시계산하고targetq105원범위/lower24/zero8exact를검사한다. 초기source9/G/shape/gain/cap/preload−.08/normal20N과rate제한은불변이다. target형상의작은Chest음수gap은유한제어의누름목표이지실제초기관통허용이아니다. 이목표로정지5초모든각도·실제Chest/RShoulder접촉·안전조건을검증하고통과후15초해제한다. 원자료/실패보존,PPO없음.
