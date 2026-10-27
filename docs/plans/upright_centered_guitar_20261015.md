# 직립 상체를 유지한 기타 중앙 배치

upper_target3은Torso/Spine의yaw자유도로sourceSpineclear/Chest−6mm/up4.2°를맞췄지만RHpalm오차23.54mm/20.53°로도달실패했으므로native미사용이다. Torso/Spine각scalar_y가각+.35rad에닿아큰몸통twist를요구했다. 기존target모두보존한다.

새source10은source9의body/Head/lower24/zero8/Root/의자/물성/형상은고정하고Ginitial을world-X음방향(인체오른쪽의반대쪽,몸중앙쪽)으로추가2~8cm옮기는범위에서Chestgap.4mm/RHipgap.4mm/Spineclear2mm/PelvisBOXclear2mm를최적화한다. 기타G:body의폭이넓은구간을가슴아래로이동시킬수있는지검사한다. 기존G배치의Chestwitness는GlocalY약−.246m의좁은상부이고GlocalX는주로world높이에대응하므로world좌우와guitar축을혼동하지않는다.

양팔만기존guitar-localpalm pose에맞추고RShoulder sourcecontact/RElbowclearance를검사한다. 초기sourceChest/Spine/Torso/모든capsule/PelvisBOX/foot/원범위/zero8/손도달을새audit로통과해야native에넣는다. 동적제어는source9의normal20N/controller10/preload−.08/기존gaincap을먼저같게둔다. actual정지5초Chest/RShoulder>95%(1초후)·직립5°/3°·모든안전조건후15초왼손해제. 원자료보존/PPO없음.
