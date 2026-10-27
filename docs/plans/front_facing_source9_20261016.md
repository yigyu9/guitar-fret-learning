# source9: 초기 오른허벅지 지지 여유 복원

source8의32개형상gate통과를실제성공으로채택하지않는다. native_static_v4는10초완료/발정면·접지·sole 유지에도기타회전8.06559°/몸통5.23577°/유지가슴+오른상완0%로실패했다. 오른상완실제접촉은전체2401시점중1시점뿐이다. 원source8/입력/실패raw는보존한다.

source7 대비Chest/Spine/오른상완초기간격은비슷했지만R_Hip초기sourcegap은.499872mm→2.350681mm로커졌다. 형상비관통만으로초기중력지지의붙잡힘을보장하지못했다. 첫step~.5초실제G이동/회전·contact·인체worldanchor/IK목표를비교해관련성을기록하고인과확정과구분한다.

source9은source8에서warmstart하고원3.8°body/2°right/2°heading/G이동10mm·회전3°/neck1.5°/lateral2mm/손오차/zero8/원범위·충돌감사기준을그대로유지한다. **초기R_Hip sourcegap 목표.5mm,엄격허용.1~.8mm**를새설계조건으로추가해원thigh cradle와비슷한여유를복원한다. Chest.5~.8mm/RShoulder.5~1mm/Spine≥5mm/Elbow≥7mm와실제nativepolicy/SAT/self/ground검사를float32값으로검증한다.

Root/의자/발24/손가락·공용자산은유지한다. 새G배치는초기한번만설정하며native에서는free·gravityON·strapOFF,직접G힘/고정/부착/매stepstate주입/PPO없음. 원유한제어gain/cap/rate는변경하지않는다. 새source/spec/config를발행해원25actualgate로준비5+정지5를검사하고통과후반복한다. 실패는다음새버전으로보존한다.
