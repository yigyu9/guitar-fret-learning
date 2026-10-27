# Full G0 Synchronizer 통합 진단

## 사용 checkpoint

- Fret: `fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt`
- Strike: `strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt`
- 곡: `02_Jazz1-200-B_solo`

## 판정 범위

두 checkpoint의 420D/303D 관측 및 30D/30D action 계약, 105D named action 병합,
공통 score clock, post-EMA history commit은 CPU interface probe를 통과했다. 다만 두 source는
최종 G0 승급 봉인이 없는 checkpoint이다. Fret은 아직 `goal_pair` 단계이며 Strike는
`S3_SONG_INTEGRATION`이지만 qualification evidence가 checkpoint contract에 봉인되지 않았다.

따라서 이 디렉터리에서 만드는 물리 결과는 `diagnostic_unqualified`로만 해석해야 한다.
영상이 생성되더라도 G0 성공 또는 학습 완료 증거가 아니다. 물리 gate 위반, hold 역산 포화,
NaN, 관절 속도 폭주가 있으면 이를 숨기지 않고 summary와 trace를 실패로 저장한다.

## 구현된 경계

- 하나의 Strike 물리 backend에 Fret 정책 view를 연결한다.
- simulator, humanoid, 기타, 물리 tensor와 PD target은 하나만 소유한다.
- Fret/Strike의 관측, goal state, 30D action history는 분리한다.
- 105D ABI를 joint name으로 Isaac DOF에 매핑한다. Isaac에서 생략되는 zero-range joint를
  위치 인덱스로 잘못 실행하지 않는다.
- Fret synergy와 Strike grip constraint 뒤에 공통 EMA와 PD 변환을 한 번만 적용한다.
- Strike entry hold 첫 프레임은 현재 자세가 다음 PD target이 되도록 EMA를 역산한다.
- permission이 닫힌 crossing도 detector에서 숨기지 않고 blocked violation으로 기록한다.
- post-physics Fret press detector는 reward tracker와 분리된 hook으로 갱신한다.

## CPU 계약 검증 명령

```bash
python -m tab2body.train_full \
  --song 02_Jazz1-200-B_solo \
  --fret-checkpoint fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt \
  --strike-checkpoint strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt \
  --device cpu \
  --output /tmp/full_g0_bundle.json
```

현재 결과: interface probe `passed`, canonical event 42개, actor-facing synchronizer
context `(1, 0)`, source parameter frozen integrity 및 runtime resume 검증 통과.

## 2026-09-21 물리 smoke 결과

- 상태: `diagnostic_failed_gate`
- GPU PhysX single-simulator step: 360회
- 영상: 640×360, 30 FPS, 180 frame, 6초
- 관찰된 canonical event: 0--14
- closed-permission crossing: 4회
- accepted crossing: 0회
- current-pose hold 역산 포화: 0회
- 비정상 수치/관절 속도 폭주 frame: 0회
- 최대 관절 속도: 약 1.600 rad/s
- 최소 관절 한계 margin: 약 -0.000672 rad
- 최악 관절: `L_Thorax_x` (`q=-0.087939`, lower=`-0.087266` rad)
- 첫 hold joint-velocity braking horizon: 25 ms

즉, 단일 물리 환경 연결과 영상 생성은 동작하지만 현재 hold만으로는 진입 시점의 오른손
관성을 모두 제거하지 못했다. 첫 자세 latch와 25 ms joint-velocity braking을 적용해도 frame
54, 61, 77, 317에서 permission이 닫힌 crossing이 detector에 기록되었다. 또한 PhysX hard
limit보다 최대 약 0.67 mrad 벗어난 frame이 기록되었다. 이 결과는 crossing과 관절 한계
오차를 숨기지 않는 fail-closed 동작이 실제 물리 rollout에서도 작동한다는 진단이며, 통합
성공 판정은 아니다. 다음 구현 단계는 target string만 보는 joint-space braking 대신 모든 줄의
거리와 pick Jacobian을 사용하는 barrier/안전 후퇴를 추가하는 것이다.

이 6초 결과는 과거의 제한 실행이며 전체 곡 결과가 아니다. recorder의 기본 동작은 이제
canonical timeline의 준비 구간, 마지막 이벤트 deadline 및 지연 여유를 이용해 안전 상한을
자동 계산하고 마지막 이벤트가 resolve될 때까지 실행한다. `--max-steps`를 명시해 그 전에
중단하면 summary는 `diagnostic_incomplete_timeline`으로 기록되어 전체 곡 결과로 취급되지 않는다.
수동 cap은 MP4 생성을 위해 최소 두 video frame을 포함해야 한다(30 FPS에서는 최소 3 step,
60 FPS에서는 최소 2 step). 이보다 작은 값은 입력 오류로 fail-closed 처리한다.

## 현재 실패 원인 분리

양손 source action은 각각 왼팔·왼손 30 DoF와 오른팔·오른손 30 DoF이며 이름이 겹치는 관절은
없다. 따라서 한 정책의 action이 다른 정책의 관절 command를 직접 덮어쓴 것은 아니다.

주된 병목은 Fret source 자체이다. `fret_035000.pt`의 단독 전체곡 평가도 F1 약 0.293,
chord-ready rate 약 0.0087, sustain-event success 2/35에 머물며 checkpoint stage도 아직
`goal_pair`이다. 통합 trace에서 모든 audible string의 Fret-ready 조건이 한 번도 Strike-ready와
동시에 성립하지 않아 permission이 0 frame이었다.

간접 상호작용은 존재한다. Synchronizer가 Fret 미준비를 보고 오른손 action을 hold로 교체하므로
Strike 정책은 단독 학습 때와 다른 실행 action/history를 받는다. Strike checkpoint의 단독 전체곡
평가는 F1 1.0, blocked crossing 0이지만, 통합에서는 이미 움직이던 pick의 관성을 현재 joint-space
hold가 완전히 제거하지 못해 closed-permission crossing이 4회 발생했다. 즉 왼손 action이 오른손을
직접 망가뜨린 것이 아니라, 왼손 미준비에 반응한 동기화 제어가 오른손의 학습 궤적을 끊었고 현재
hold가 그 전이를 안전하게 처리하지 못한 것이다.

공유 물리계의 수동 몸통 결합과 Strike backend의 관절 한계를 Fret view가 함께 사용하는 차이도
남아 있지만, 현재 자료만으로 이것을 주원인이라고 볼 근거는 없다. source별 동일 초기 상태 비교
rollout을 추가해야 그 영향량을 분리할 수 있다.

## 물리 영상 산출물

```bash
python -m tab2body.tools.record_full_g0_rollout \
  --fret-checkpoint fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt \
  --strike-checkpoint strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt \
  --song 02_Jazz1-200-B_solo \
  --device cuda:0 \
  --fps 30 \
  --width 640 \
  --height 360 \
  --braking-horizon-ms 25 \
  --output-dir docs/2026-09-21/synchronizer/full_g0 \
  --video-name full_g0_02_Jazz1-200-B_solo.mp4 \
  --trace-name full_g0_02_Jazz1-200-B_solo.trace.json \
  --summary-name full_g0_02_Jazz1-200-B_solo.summary.json
```

물리 recorder가 성공하면 다음 파일을 같은 디렉터리에 저장한다.

- `full_g0_02_Jazz1-200-B_solo.mp4`
- `full_g0_02_Jazz1-200-B_solo.trace.json`
- `full_g0_02_Jazz1-200-B_solo.summary.json`

MP4의 watermark와 JSON의 mode가 `diagnostic_unqualified`이고 source hash가 위 checkpoint와
일치해야 같은 실행의 결과이다. 현재 summary status는 물리 gate 위반 때문에
`diagnostic_failed_gate`이다. 실행 자체가 실패하면 성공처럼 보이는 대체 영상을 만들지 않는다.
