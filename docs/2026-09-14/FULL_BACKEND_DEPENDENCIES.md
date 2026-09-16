# Full backend 선행 의존성

2026-09-14 읽기 전용 코드·체크포인트 조사. 현재 실행 범위는 **독립 Stability BC → PPO**다.
이 문서는 실제 Full 연주에 남아 있는 일을 구분한다. Full 물리 rollout을 실행하거나 새 backend를
구현한 결과가 아니다. 기존 문서 목차는 [DOCUMENT_INDEX](../DOCUMENT_INDEX.md)를 따른다.

## 1. 현존 source checkpoint 자격

`fret/training/runs/*/checkpoints/*.pt` 342개와 `strike/training/runs/*/checkpoints/*.pt`
275개, 총 **617개**의 ZIP `data.pkl`을 읽었다. 필수 `g0_qualification` 키는 0개였고
읽기 오류는 없었다. 각 실행의 수정 시각 기준 최신 checkpoint 27개는 CPU에서 metadata를
로드해 `inspect_source_checkpoint_metadata()`로 검사했으며 모두 `qualified_for_g0=false`였다.
이는 **현재 loader가 인정하는 평가 봉인을 가진 후보가 조사 범위에 없다**는 뜻이다.
모든 617개의 모델 가중치·입력·asset hash를 strict loading하거나 연주 성능을 평가한 것은 아니다.

| 후보 | 저장된 단계·상태 | 다음 조건 |
|---|---|---|
| [Fret 035500](../../fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035500.pt) | `goal_pair`, 미봉인 | `full_song` 학습·평가 필요 |
| [오늘 Fret cache 035055](../../fret/training/runs/20260914_cache_success_capture/checkpoints/fret_035055.pt) | `goal_pair`, 미봉인 | cache 수집 결과가 Full 자격을 대신하지 않음 |
| [Strike 023309](../../strike/training/runs/20260911_2235_02_Jazz1-200-B_solo/checkpoints/strike_023309.pt) | `S3_SONG_INTEGRATION`, complete=true, tempo=1.0 | 자격 검사상 남은 이유는 평가 봉인 부재; 현재 코드·asset strict 검사와 재평가 필요 |
| [Strike 029964](../../strike/training/runs/20260910_1916_02_Jazz1-200-B_solo/checkpoints/strike_029964.pt) | `S3_SONG_INTEGRATION`, complete=true, tempo=1.0 | 위와 같음 |

최신 Fret 20개 실행의 checkpoint 중 `full_song` 후보는 없었다. 최신 Strike 두 후보는
원속도 최종 단계까지 도달한 **재검증 후보**이며 이미 검증된 Full source가 아니다.
기존 `full/04_training/bundles/02_Jazz1-200-B_solo.g0.json`의 001500 정책 쌍보다 최신이다.

검사 정본은 [source_policies.py](../../tab2body/full/source_policies.py)의
`_source_qualification`, `inspect_source_checkpoint_metadata`, `load_frozen_skill_pair`다.
정상 물리 runtime은 최종 단계·곡·관측 ABI·공유 asset·action scale/range·평가 봉인을 검사한다.
학습 완료 metadata만 보고 `evaluation_passed=true`를 추가하면 안 된다.

## 2. 생성자와 분리 가능한 범위

FretTask 생성자는 `task_fret.py:513`에서 `GuitarEnvBase`를 생성한다. 그 뒤 source 30축 확인,
왼쪽 thorax hold, goal sequence(`:731`), FretReward(`:747`), 접촉·관절·겹침 monitor와
학습 curriculum/cache 상태를 함께 초기화한다. 관측 전용 초기화 함수로 나뉘어 있지 않다.

StrikeTask는 설정 검사를 먼저 하고 `task_strike.py:772`에서 simulator를 생성한다.
그 뒤 source 30축, pick 관련 충돌 설정, goal sequence(`:833`), grip reference(`:847`),
detector(`:1009`), penetration monitor(`:1022`), motor/recovery/event 상태를 초기화한다.
여기도 현재 독립 policy state 생성자는 없다.

따라서 두 Task 생성자를 호출하거나 전체 다중 상속을 적용하면 simulator·reset·clock 책임이
겹친다. `__new__`와 광범위한 `__getattr__` 위임으로 초기화를 생략하는 방식도 피한다.
**공유 base를 명시적으로 참조하는 source별 state view**를 추출하는 것이 가장 작은 안전한 방향이다.

우선 분리 가능한 부분은 관측의 순수 물리 block과 이미 독립된 detector/readiness다.
전체 420D/303D를 같은 단계에서 즉시 완성했다고 할 수는 없다. goal/contact/recovery state를
실제로 연결하고 동일 입력에 대한 원본 관측과 수치 비교를 통과해야 한다.

## 3. Fret 420D에 필요한 실제 상태

재사용 대상은 [task_fret.py](../../tab2body/env/tasks/task_fret.py)의 다음 method다.

- `_fret_v2_physical_blocks`: 30축 q/qd, L_Thorax의 기타 상대 pose/twist·중력,
  L_Wrist/LH:palm 및 5개 손끝의 실제 상태. 공통 base의 `body_pose_twist_in_guitar_frame`,
  `hbody_state`, `hbody_pos`, `hbody_contact_force`, `to_guitar_frame`을 사용한다.
- `_fret_v2_event_components`, `_fret_v2_lookahead`, `_fret_v2_event_progress`:
  운지·현/fret·barre·finger transition, 다음 두 event와 현재 진행률.
- `_build_fret_v2_blocks`, `_build_fret_v2_observation`, `compute_synchronizer_observation`:
  goal geometry, press/wrong-press/sustain/slip/dwell, thumb geometry·힘 품질,
  penetration margin, 준비 단계와 실제 직전 실행 action을 결합한다.

필수 state는 `FretGoalSequence`의 읽기 데이터, canonical clock의 frame/event projection,
preparation count, source별 30축 index, `FretReward`의 all-cell press hysteresis와 hold streak,
thumb 계측, penetration monitor, 실제 실행 history다. `FretReward.active_press_cells()`는
`[N,6,22]`의 goal-independent 압현 snapshot을 이미 제공한다.
`observe_fret_v2_state()`는 read-only이며 현재 hysteresis 갱신은 `FretReward.compute()`에
결합돼 있다. **측정·hysteresis 갱신을 별도 post-physics method로 추출**해야 관측을 여러 번
만들어도 streak가 중복 진행되지 않는다. reward 전체를 단순히 두 번 호출하면 안 된다.

운지·hand target 데이터는 기존 goal loader를 재사용하되 Full에서는 독립 `goals.advance()`를
호출하지 않는다. canonical score frame에 대응하는 실제 goal 조회와 최대 3-frame PRESS
advance를 연결한다. 준비·미래 event가 없는 경우에만 해당 contract의 invalid mask/값을 사용한다.
실제 접촉·readiness를 임의의 0 또는 true로 대체하지 않는다.

## 4. Strike 303D에 필요한 실제 상태

재사용 대상은 [task_strike.py](../../tab2body/env/tasks/task_strike.py)의 다음 method군이다.

- `_strike_v2_physical_blocks`: 30축 q/qd, R_Thorax, RH:palm/RH:pick pose/twist,
  `PickGripReference.measure()`와 실제 penetration margin.
- `string_segments_g`, `_string_lane_geometry`, `_current_target_geometry`,
  `_current_target_string/time/direction/offsets/sweep_duration/masks`,
  `_current_timing_tolerances`, `_current_motion_context`, `_strike_v2_lookahead`.
- `_recovery_clearance_points`, `_current_motion_target` 및
  `_build_strike_v2_blocks`/`_build_strike_v2_observation`.

필수 state는 canonical event/time projection, source execution context의 tempo·tolerance·lead,
READY/APPROACH/RELEASE_RECOVER motor phase, ready streak, event별 release mask,
`PickStrikeDetector`의 armed/wait-rearm 상태, 직전 pick 좌표·release pulse,
recovery context의 exit/next-entry·방향·필요 프레임·clearance 진행, 실제 실행 history다.
`strike_events.py`의 순수 recovery/phase helper를 재사용하고, 독립 `StrikeTask.step()`의
학습 종료·자체 event cursor·reward 집계까지 복사하지 않는다.

검출기는 `PickStrikeDetector.step(previous_tip_g, current_tip_g, string_segments, dt)`를
물리 control frame당 한 번 진행한다. reset 후 이전 tip도 같은 새 물리 pose로 초기화한다.
readiness는 `full/readiness.py:evaluate_strike_readiness()`에 phase, grip, entry distance,
pre-crossing signed distance, detector armed, 방향을 실제 측정값으로 공급한다.

## 5. 공통 backend와 Stability 연결

`FullG0TaskController.step()`은 `G0RuntimeCommand`를 받고 단 한 번 호출되는
`simulate_once`를 이미 제공한다. 새 공유 backend는 다음을 맡는다.

1. 단일 `GuitarEnvBase`, 양손 state view, canonical clock의 goal projection 초기화.
2. source 30축별 actuator handshake, Fret synergy·Strike grip 후처리, 105축 named merge.
3. 공통 EMA/PD 한 번, 물리 한 번, 압현·pick detector 한 번, 실제 실행 action commit.
4. 닫힌 release 경계에서 pick의 관성 crossing을 제어하는 entry-plane 방어와 위반 계측.

후처리는 `full/postprocessing.py`, transaction은 `env/tasks/task_full.py`, clock/runtime은
`full/clock.py`와 `full/runtime.py`를 재사용한다. 관측 추출과 source state 계층이 첫 변경 대상이며
simulator를 추가하는 것은 해결책이 아니다. 변경 후 source별 원본 관측 parity, 한 번만 갱신되는
clock/detector, 부분 reset 격리, action history/범위 parity를 확인해야 한다.

독립 Stability는 470×8 입력·97축 출력이다. `full/stability_bridge.py`는 그 proposal의
**43축만 허용**하고 손목·손가락·목·머리를 보존하는 seam이다. Full용
`learning/stability_model.py`의 264D→43D 모델은 별도 모델이며 직접 checkpoint 호환은 없다.
실제 Full context를 수집해 43축 teacher target으로 BC 증류한 뒤 PPO로 진행할 수 있다.
이전 독립 정책이 왼손 엄지/손목을 사용했다면 43축 mask 후 성능 보존은 새로 검증해야 한다.

## 6. 미자격 진단 모드 권고

미자격 source로 배관을 개발할 필요가 생기면 별도의 명시적 `diagnostic_unqualified` 모드를
설계할 수 있다. 이는 현재 구현된 기능이라는 뜻이 아니다. 생산용 자격 gate는 유지하며,
source hash·곡·차원·관절 범위·후처리 의미 검사는 진단에서도 생략하지 않는다.

현재 postprocessor는 `VerifiedSourceQualification`을 요구하므로 runtime의 bool 한 개만
바꾸어 해결되지 않는다. 진단 provenance를 따로 받아들이는 계약이 필요하고
`qualified_for_g0=false`, `full_physics_validated=false`, 실패 이유를 결과에 보존해야 한다.
identity 후처리나 가짜 readiness로 실행을 통과시키면 source 정책을 동일하게 재사용한 검사가 아니다.
현재 우선순위인 standalone BC→PPO를 위해 이 진단 Full 모드까지 만들 필요는 없다.
