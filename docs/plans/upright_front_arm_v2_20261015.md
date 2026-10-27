# 오른손 여유를 둔 상완 앞모서리 후보

source11 strictpalmIK는최선normalG_Z.2776/palm14.11mm·4.35°로원5mm/2°·normal.45hardgate를실패하여native미사용이다. source12는왼손그립/body/head/lower/G고정·기존모델/물성/유한제어조건은같게두고오른palm보존weight를1000m/80rad→250m/30rad로줄여최대50mm/15°이내의오른손위치/각도변경을허용한다. 기타안정지지를먼저검사하는자세후보이며원래의정밀연주위치유지를주장하지않는다. 실제palm과손끝변화를기록하고후속연주검증은별도다.

RShoulder sourcegap.4mm/frontnormalG_Z≥.65soft(최종≥.45hard)/RElbowclear8mm/모든관절원범위와sourcecapsule·box·발원조건을검사한다. 통과전native미사용. 원G/Root/왼손/몸통/하체를움직여손오차를숨기지않는다. 통과후기존controller10/scene8/preload−.08동일정지5초·Chest/RShoulder실제양의접촉및upright5°/3°를검증한다. 성공후15초해제,PPO없음.
