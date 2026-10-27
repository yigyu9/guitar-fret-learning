# 수평·원 좌우 위치 유지, 수평 yaw 탐색 확대

source1은넥각0°/좌우오차7.1nm로사용자두조건을맞췄지만Chestgap2.560mm로로컬접촉기준2mm미달,source미채택/native미사용이다. 다른gap은Spine1.911mm/RShoulder.400mm/RHip12.178mm였다. yaw+5°상한에있었다.

source2는G몸통의humanoid우측좌표+150.035mm와넥수평을parameterization으로정확히유지한다. user조건이아닌수평yaw범위만±5°→±20°로넓힌다. 넥을올리거나좌우로옮기지않으며body/head/lower24/range/물성등나머지조건유지. 원palmlocal목표5mm/2°·전체sourceaudit후에만native정지5초. native neck3°/원우측좌표±20mm/몸통5°/옆3°/Chest·RShoulder동시95%기준은원계획동일. 기존code/input/result/계획보존,새PPO·왼손시험은정지검증전금지.

- [ ] source2fit와정확한사용자배치조건확인
- [ ] 전체형상검사
- [ ] 통과시에만정지5초
