# 구현 상태

> 기준: rule-based G0 Synchronizer의 CPU 계약·합성 runtime. 아래의 구현 완료는 Isaac Gym
> 물리 rollout 완료를 뜻하지 않는다.

| 항목 | 상태 |
|---|---|
| Offline canonical event compiler | 구현 (`tab2body/full/events.py`) |
| Rule-based Synchronizer | 구현·CPU contract test 작성 (ordered/directional crossing 포함) |
| Effective sounding-fret readiness evaluator | 구현·CPU contract test 작성 |
| Action Residual coordinator 독립 모델 | 구현·contract test 작성 |
| 11-head central critic 독립 모델 | 구현·contract test 작성 |
| Frozen Fret/Strike checkpoint loader와 native observation adapter | 구현·strict validation 작성 |
| Named 105D action manifest/bridge | 구현·contract test 작성 (G0: 60 active + 45 hold) |
| Source action postprocessing/actuator handshake | 구현·CPU contract 검증 (Fret synergy, Strike grip) |
| Rule Synchronizer + frozen source 합성 runtime | 구현·CPU integration 작성 |
| Reference-only G0 bundle manifest | 구현 |
| One-cursor/one-clock 및 bounded-delay 계약 | 구현·CPU contract test 작성 |
| Fret 최대 3-frame press-advance | standalone Fret hook 구현; Full G0 설정·bundle hash 연결 미구현 |
| `task_full.py` one-step transaction bridge | 구현 (callback seam + strict post-physics ABI validation) |
| `task_full.py` one-simulator Isaac `FullG0Task` backend | 미구현 |
| `hold.py` | 빈 스텁 |
| `train_full.py` strict checkpoint assembly CLI | 구현·실제 checkpoint tensor probe 통과 |
| G0 CPU 병합 계약 테스트 | 구현 |
| G0 고정 기타 physical rollout | 미실행 |
| G1 자유 기타 | 미실행 |
| `strapped-v1` 독립 Isaac Gym probe | 구현·GPU 4-view 검증 완료 |
| `strapped-v1` 공용 물리식 | `tab2body/env/strap.py`로 이관; probe와 main base가 공유 |
| `strapped-v1` main `GuitarEnvBase` 선택 연결 | 구현 (`guitar_fixed=False`, `strap_enabled=True`); GPU smoke 대기 |
| 초기 pelvis-relative guitar pose pre-play stability gate | 구현·CPU contract test 통과 |
| StabilityAdapter 43D named action/15D calibration observation | 계약 구현·CPU test 통과 |
| StabilityAdapter 264D block observation/43D actor/5-value critic | 모델·CPU contract 구현; task tensor 연결 전 |
| 독립 Stability 사전학습 97D/317D | 구현·GPU 검사, 연주 context 없음 |
| Stability named-radian → 105D source/hold bridge | 구현·CPU 검사; Full G1 backend 연결 전 |
| StabilityAdapter actor/PPO와 Full G1 결합 | 미구현 |

Action Residual 코드는 `full/action_residual/`에 격리했다. 이는 source hidden activation을 수정하는 향후 `full/latent_sync/`와 다른 architecture ID와 checkpoint 계약을 사용한다.

현재 `tab2body/full/runtime.py`는 simulator를 만들지 않는다. 향후 하나의
`FullG0Task`가 동일한 humanoid/기타 상태에서 Fret·Strike 관측을 만들고, runtime의
105D command에 common EMA/PD를 한 번 적용한 뒤 physics step과 detector 평가를 각각 한
번 수행해야 한다. 기존 FretTask와 StrikeTask를 별도 simulator로 동시에 실행하는 것은
이 계약의 구현으로 인정하지 않는다.

Frozen source actor가 보는 Synchronizer 입력은 학습 분포를 보존하기 위해 `(1, 0)`으로
유지한다. 실제 readiness permission, event별 최대 3-frame·실제 0~3-frame safe delay, hold와 multi-string
partial 처리는 actor 밖의 rule supervisor가 소유한다.

G1 시작 순서는 `STABILIZING → common pre-roll → score frame 0/audio`로 정했다. 현재
pre-play gate는 CPU 계약으로 구현했고 main base에 free-guitar/strap force를 연결했다. 다만
main base의 strap 외력은 현재 60 Hz control step마다 계산되어 4개 PhysX substep 동안 유지된다.
독립 probe의 240 Hz 갱신과 동등한지는 GPU에서 재검증해야 하며, 그 전에는 Full G1 물리 완료로
판정하지 않는다.

현재 독립 정책을 Full에 연결할 때의 관측 확장·단계 전환·action/history 계약은
[StabilityAdapter 통합 계약](../../stability_adapter/INTEGRATION.md)을 따른다.
