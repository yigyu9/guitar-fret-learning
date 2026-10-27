# strike 구현 상태 — 2026-09-07 Strike-v2 반영판

현재 규칙 우선순위와 현재/확장 경계는 [`RIGHT_HAND_RULES.md`](../RIGHT_HAND_RULES.md) 및
[`RIGHT_HAND_EXTENSIONS.md`](../archive/RIGHT_HAND_EXTENSIONS.md)를 따른다.

## 구현·검증 완료

| 항목 | 현재 계약 | 증거 |
|---|---|---|
| 음악 입력 | `strike_training.v3` 필수 `[time,frame,string]` + 선택 provenance/review → `strike_plan.v4` single/strum/direction/microtiming/transition | goal/direction/microtiming/transition tests |
| 시간 정본 | `time`; `frame`은 60 Hz 검증/추적용, 오차 ≤0.5 frame | 실제 Jazz 42 events 변환 PASS |
| 줄 순서 | Isaac `0=high-e … 5=low-E`; builder에서 `5-source` 1회 변환 | goal test |
| 방향 | `phrase_dp_microtiming_v3`의 down/up·줄별 offset과 줄 재통과 비용을 준비·통과·회복에 적용 | task/checkpoint contract v7 |
| 제어 | 어깨3+팔꿈치3+손목3+오른손21 = 30 action; 손가락은 grip 기준 residual | CPU action contract, GPU smoke 대기 |
| 피크 | geometry 없는 `RH:pick` origin, 검지에 고정 | asset + grip reference |
| 줄 | `G:stringN→G:stringN_end` 고정 유한 선분 | detector/GPU audit |
| 타현 | swept point의 유효 crossing 뒤 one-shot RELEASE | detector test CPU/CUDA |
| 중복 방지 | 줄별 `ARMED→RELEASE→WAIT_REARM→ARMED` | detector test |
| 영역 | global allowed `[-.385,-.255]`, preferred `[-.355,-.295]`; sampled lane core `±6 mm`, outer `±12.5 mm` | lane/zone test, GPU audit |
| 그립 | guitar 연구 frame 2227의 21-DOF qpos; 엄지·검지 ±0.08 rad, 자유 손가락 ±0.22 rad; 모든 단계 연속 quality gate | grip/reward/curriculum/evaluation regression |
| 단계 | A0 grip→A1 ready→A2 crossing→A3 timing→A4 strum-context recovery→S0 2줄→S1 폭→S2 timing→S3 song | curriculum tests |
| 시간 curriculum | A3는 100→67→50 ms, S2는 400→250→225→200→175→150→100→zone 100→67→50 ms 중심·성공 기반, S3는 tempo λ `0→…→1` | curriculum save/resume test |
| 승급 증거 | A0~S3 완료 episode exact 지표, grip mean/p05/group/bad-streak와 stage별 failure/FP/direction/recovery gate | curriculum regression |
| timing 통계 | timing/zone gate 전의 유효 target crossing 전체로 MAE/p95 계산 | pooled timing regression |
| 전체곡 준비 | 첫 event 30 frame 전 시작, S3 학습은 임의 시작 8 gesture, 원템포 평가는 전체 plan | GPU runtime audit |
| 회복 | exit→next-entry 경로가 줄을 재통과하면 10 mm lift·elevated transfer·re-arm을 모두 요구; 추가 RELEASE/blocked는 count reset | event/recovery/clearance CPU regression |
| 관측/보상 | 기본 303D named-block Strike-v2, scalar reward/value; 327D는 v1 호환 | CPU/GPU contract test |
| 체크포인트 | contract v14, model/optimizer/counter, goal/grip/config/code/asset hash와 exact observation manifest 봉인 | checkpoint tests + strict reload |
| 자동 산출물 | JSONL/log/eval/plot/analysis/두 카메라 MP4, manifest 오류 기록 | artifact contract + GPU end-to-end |
| 운동·안전 진단 | RELEASE depth/speed, 관절군 phase motion, recovery crossing, 오른팔 기타 관통 JSON | `audit_strike_motion.py` + artifact contract |

2026-07-29 GPU audit JSON은 역사 산출물로 정리했다. 2026-08-03 코드 정리본은 CPU 회귀를 통과했지만
현재 장비에 CUDA device가 없어 새 GPU smoke를 완료하지 못했다. 다음 CUDA 실행의 기준은
`python -m tab2body.train --task strike --smoke`가 만드는 manifest·로그·평가 JSON이다. 상세 범위는
[`CODE_AUDIT_2026-08-03.md`](../archive/CODE_AUDIT_2026-08-03.md)를 따른다.

## 구현했지만 수치 재보정이 필요한 항목

- crossing 최소 depth `1 mm`
- 최소 횡속도 `0.05 m/s`
- re-arm 분리 `3 mm`, 대기 `2 frame`
- ready/entry/exit offset `3/1.5/3 mm`
- A1 ready 거리와 보상 scale
- 각 curriculum promotion threshold
- grip residual `0.08/0.22 rad`와 연속 quality gate `0.92/0.85`

이 값들은 checkpoint에 봉인된다. 값을 바꾸면 기존 checkpoint resume을 거부하며, 정상/오류
rollout과 영상에 근거해 명시적으로 바꾼다.

## 진단 또는 사람 검토로 남긴 항목

- 오른팔/손 기타 관통 monitor는 구현했지만 성공/실패 depth 분포가 없어 termination은 아직 비활성
- phase duration, 어깨/팔꿈치/손목/손 기여율, acceleration/jerk, action saturation은 자동 JSON으로 수집
- S3 event index가 진행된 뒤에도 직전 줄·lane·방향의 follow-through 문맥이 회복 종료까지 유지되는지 GPU 확인
- 연속 down의 string-field 밖 recovery corridor와 역방향 재교차율
- legacy quaternion과 현재 Isaac qpos 자세 사이의 FK 잔차
- 충분히 학습된 A4/S0에서 recovery completion/reset/blocked와 crossing-y/tip-speed 분포
- 사람이 보기에 자연스러운지 remembered/current 영상 검토

## 명시 보류

- 얇은 rigid pick geometry와 실제 엄지·검지 grasp/slip
- 탄성 string, contact/load, 음향 생성
- same-string alternate/economy 방향 확장
- restrike 전용 계획, fingerstyle, hybrid
- palm mute, slap/tap, rasgueado
- “사람과 동일한 동작”이라는 최종 주장

다음 실행 판단은 [학습 문서](../03_training/README.md)를 따른다.
