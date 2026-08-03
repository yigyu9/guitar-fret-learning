# strike 구현 상태 — 2026-07-27 재설계판

## 구현·검증 완료

| 항목 | 현재 계약 | 증거 |
|---|---|---|
| 음악 입력 | `tab2body.strike_training.v1`, 사건은 `[time, frame, string]` | `test_strike_goal_timing.py` |
| 시간 정본 | `time`; `frame`은 60 Hz 검증/추적용, 오차 ≤0.5 frame | 실제 Jazz 42 events 변환 PASS |
| 줄 순서 | Isaac `0=high-e … 5=low-E`; builder에서 `5-source` 1회 변환 | goal test |
| 방향 | 입력에 없으므로 `down_only_v1` (`+x_g`) | task/checkpoint contract |
| 제어 | 어깨3+팔꿈치3+손목3+오른손21 = 30 action | GPU runtime audit |
| 피크 | geometry 없는 `RH:pick` origin, 검지에 고정 | asset + grip reference |
| 줄 | `G:stringN→G:stringN_end` 고정 유한 선분 | detector/GPU audit |
| 타현 | swept point의 유효 crossing 뒤 one-shot RELEASE | detector test CPU/CUDA |
| 중복 방지 | 줄별 `ARMED→RELEASE→WAIT_REARM→ARMED` | detector test |
| 영역 | global allowed `[-.385,-.255]`, preferred `[-.355,-.295]`; sampled lane core `±6 mm`, outer `±12.5 mm` | lane/zone test, GPU audit |
| 그립 | guitar 연구 frame 2227에서 얻은 21-DOF qpos target | `pick-grip-reference.json` |
| 단계 | A0 grip→A1 ready→A2 crossing→A3 timing→A4 zone | curriculum tests |
| 시간 curriculum | A3에서 성능 gate로 100→67→50 ms | curriculum save/resume test |
| 승급 증거 | A1~A4 완료 episode의 exact `strike_*`만 사용; no-episode rollout은 streak 유지 | curriculum regression |
| timing 통계 | timing/zone gate 전의 유효 target crossing 전체로 MAE/p95 계산 | pooled timing regression |
| 전체곡 준비 | 첫 event 30 frame 전 시작, 현재 goal 최대 894 frame | GPU runtime audit |
| A4 episode | 학습은 임의 시작 연속 8 events, 평가는 전체 42 events | task/evaluation smoke |
| 회복 | hit 뒤 12 frame; 마지막 A4 hit도 보존, miss는 회복 없이 종료/진행 | task audit |
| 관측/보상 | 263D observation, scalar reward/value | GPU runtime audit |
| 체크포인트 | model/optimizer/counter, goal/grip/config/code/asset hash, curriculum·task RNG; 평가 시 saved PPO/std 복원 | checkpoint tests + GPU reload |
| 자동 산출물 | JSONL/log/eval/plot/analysis/두 카메라 MP4, manifest 오류 기록 | artifact contract + GPU end-to-end |

2026-07-29 GPU audit JSON은 역사 산출물로 정리했다. 현재 검증은
`python -m tab2body.train --task strike --smoke` 실행 폴더의 manifest·로그·평가 JSON을 기준으로 한다.

## 구현했지만 수치 재보정이 필요한 항목

- crossing 최소 depth `1 mm`
- 최소 횡속도 `0.05 m/s`
- re-arm 분리 `3 mm`, 대기 `2 frame`
- ready/entry/exit offset `3/1.5/3 mm`
- A1 ready 거리와 보상 scale
- 각 curriculum promotion threshold

이 값들은 checkpoint에 봉인된다. 값을 바꾸면 기존 checkpoint resume을 거부하며, 정상/오류
rollout과 영상에 근거해 명시적으로 바꾼다.

## 진단 또는 사람 검토로 남긴 항목

- 오른손 손목 작업영역, 기타 관통, 비정상 지지의 strike 전용 calibrated safety proxy
- phase duration, 어깨/팔꿈치/손목 기여율, jerk, path curvature, action saturation
- legacy quaternion과 현재 Isaac qpos 자세 사이의 FK 잔차
- 충분히 학습된 A4에서 crossing-y/timing/re-arm 분포
- 사람이 보기에 자연스러운지 remembered/current 영상 검토

## 명시 보류

- 얇은 rigid pick geometry와 실제 엄지·검지 grasp/slip
- 탄성 string, contact/load, 음향 생성
- up/alternate/economy 방향 입력 확장
- strum, restrike 전용 계획, fingerstyle, hybrid
- palm mute, slap/tap, rasgueado
- “사람과 동일한 동작”이라는 최종 주장

다음 실행 판단은 [학습 문서](../03_training/README.md)를 따른다.
