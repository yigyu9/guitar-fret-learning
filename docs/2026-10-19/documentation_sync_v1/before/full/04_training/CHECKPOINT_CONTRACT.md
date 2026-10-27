# Full checkpoint 계약

> 상태: **G0 bundle v2 구현 / G1·G2 Stability checkpoint 계약은 재설계 대기**

G0는 `tab2body.g0_player_bundle.v2`로 source checkpoint의 실제 file SHA-256, contract SHA,
Canonical PlayEvent hash, rule Synchronizer 3-frame 설정과 105D action manifest를 봉인한다.
Fret·Strike weight를 bundle에 복사하지 않는다. Source가 final-stage/original-tempo 평가 자격을
contract 내부에 봉인하지 않았다면 integration smoke 전용으로 취급한다.

G1·G2 checkpoint의 support hardware, physics, observation, action과 assist hash는 새 환경 계약에서
다시 정의한다. 과거 `strapped-v1` checkpoint 계약은 사용하지 않는다.
