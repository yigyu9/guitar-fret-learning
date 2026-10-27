# 동일배치 Hip 목표 보정 후속 비교

source9의정지V6와V7은초기배치/상체/발/gain/cap을같게두고R_Hip_x목표bias0/−.04rad만비교했다. V7도5초/직립각/안전조건을통과했으나Chest양의접촉0이었다. 실제종료Hip_x는−1.607989→−1.643541로유지높이가개선되고GrootZ는.717868→.726963m,Chestsourcegap10.986→4.849mm로줄었다. 같은source9에서의직접비교이므로이번보정의효과는관측됐다. 앞선source7과9는Hip초기각/G배치도달라발부유만을원인으로분리확정하지않는다.

다음한조건은R_Hip_xbias−.04→−.08rad다. 모든초기값/기존세hipinteriorbias/gain·cap/finiteStablePD/105·zero8/Root/기타자유중력ON·strapOFF/금지APIguard는같다. 원범위안이며.4rad/srate로.2초에걸쳐목표를제출한다. 실제관측된간격감소(6.137mm/.04rad)에따르면추가보정은남은4.85mm를채우는검증후보다. 이를성공으로미리채택하지않는다. 정지5초의실제Chest/RShoulder양의접촉>95%(1초이후),몸통/가슴total≤5/right≤3및모든안전조건통과후15초해제로진행한다.
