# Full checkpoint 계약

> 상태: **G0 bundle v2 구현 / 아래 G1·G2 Stability checkpoint는 설계 중**

G0는 `tab2body.g0_player_bundle.v2`로 source checkpoint의 실제 file SHA-256, contract SHA,
Canonical PlayEvent hash, rule Synchronizer 3-frame 설정과 105D action manifest를 봉인한다.
Fret·Strike weight를 bundle에 복사하지 않는다. Source가 final-stage/original-tempo 평가 자격을
contract 내부에 봉인하지 않았다면 integration smoke 전용으로 취급한다.

G1·G2 checkpoint는 최소한 다음 값을 봉인한다.

```text
support_hardware = strapped-v1
strap_route_hash
strap_button_exit_guide_hash
strap_physics_hash          # length/slack/stiffness/damping/cap/update rate
strap_collision_proxy_hash  # humanoid + guitar
artificial_assist_profile
```

G0에서는 `support_hardware=disabled`로 기록하고 strap force를 적용하지 않는다. G1·G2에서는
`strapped-v1` tension-only 가상 strap constraint가 기본이며, G2에서 0이어야 하는 것은 strap constraint가 아니라 artificial
hand/root assist다. 위 hash가 다르면 자동 resume·평가 호환으로 취급하지 않는다.
