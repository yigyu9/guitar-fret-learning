# 척추 선접촉을 피하는 가슴 우선 유한 목표

정지V10은upper_target2로5초/모든각도·안전조건을통과하지만Chest접촉0이다. target2 자체의Spinegap−3.720mm/Chest−2.748mm로Spine이더많이겹쳐,접촉제약이상체·기타를밀어낼때Chest까지닫히지않을수있다. 초기source9/하체/preload−.08/normal20/gain/cap은유지한다.

upper_target3은body9축의target만다시최적화한다. world-up은전경약4.2°/오른쪽0°를우선하며total5°를하드검사한다. 작은yaw자유도를허용하고sourceG고정상태에서Spine/Torso간격≥.1mm,Chest의가상누름목표약−6mm를동시에노린다. 전체q원범위/lower24/zero8exact,양손world pose/Head방향보존,오른상완근접을검사한다. 초기source9에는여전히관통을추가하지않고,실제제어에서만기존rate/유한effort로목표를제출한다.

target형상은실제native접촉성공이아니다. source목표라도Spine/Torso비움과각도·손도달검사전에는사용하지않는다. 정지5초의실제Chest/RShoulder>95%(1초후)/upright5°·3°/모든안전조건을통과한뒤15초해제한다. 실패원자료/이전target/코드모두보존,PPO없음.
