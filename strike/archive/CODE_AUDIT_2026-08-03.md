# Strike 학습 환경 코드 정리·검증 보고서 — 2026-08-03

> **상태: HISTORICAL AUDIT.** 당시 코드 상태의 증거이며 현재 Strike-v2 303D 계약의 상태 문서가 아니다.

## 결론

Strike 전용 의미는 유지하면서 중복 설정, 학습 lifecycle, run I/O, recorder 복원 경로를 각각 하나의
owner로 합쳤다. 상태기 감사에서 확인한 회복 인과관계와 A4 READY 우회 등 실제 오류도 함께 수정했다.
현재 CPU 계약·구문·Fret 호환성은 통과했다. 이 장비에는 CUDA device가 없어 최신 Isaac Gym 물리 step은
검증하지 못했으므로 장시간 학습 전에 GPU smoke 1회를 반드시 다시 수행한다.

과거 Strike 로그와 영상은 삭제하지 않았다. 실행 의미와 관측 의미가 달라졌으므로 과거 Strike
checkpoint는 새 코드에 직접 resume하지 않고 새로 학습한다.

## 합치거나 제거한 부분

| 영역 | 정리 결과 | 현재 owner |
|---|---|---|
| task 설정 | task 내부의 중복 기본값을 제거하고 closed config로 변경 | `strike_cfg.py` + `env/config.py` |
| 단계 이름 | 여러 파일의 문자열 사본을 한 계약으로 통합 | `strike_contract.py` |
| 학습 단계 wiring | config 매핑, fixed stage, 전후 iteration 적용을 실행기에서 분리 | `strike_training_runtime.py` |
| checkpoint 생성 | trainer/recorder가 같은 semantic builder와 file set 사용 | `strike_checkpoint.py` |
| run metadata | manifest, artifact 성공/실패, resource preflight를 공용화 | `learning/run_io.py` |
| recorder | 구형 checkpoint 추측 fallback과 constructor introspection 제거 | `tools/record_strike_rollout.py` |
| strike lane | allowed/quality 중복 계산을 한 gate 결과로 통합 | `env/strike_detector.py::strike_lane_gate` |
| task 임시 tensor | 사용되지 않던 last-hit/miss/timing/zone 사본 제거 | `env/tasks/task_strike.py` |
| Isaac task import | Fret/Strike를 동시에 eager import하던 package 경로를 lazy import로 변경 | `env/tasks/__init__.py` |

Fret의 task, base, trainer 구현은 수정하지 않았다. Strike 때문에 검증된 Fret 계약을 공통 리팩터링하는
대신 실제로 공유되는 run/config helper만 사용했다.

## 수정한 실행 오류

1. 물리 crossing을 만든 action의 phase가 아니라 전이 후 phase로 같은 frame을 재해석하던 순서를
   고쳤다. RELEASE frame 자체는 회복 frame으로 세지 않는다.
2. matcher 성공 여부와 무관하게 실제 RELEASE가 있으면 직전 string, lane, direction을 저장하고
   `RELEASE_RECOVER`로 들어간다. wrong/timing/zone 실패도 실제로 줄을 통과했다면 회복한다.
3. A4가 event index를 먼저 진행해도 직전 release 문맥을 유지한다. 잘못된 up release의 회복 목표도
   실제 방향을 따라가므로 즉시 역전하는 목표를 만들지 않는다.
4. detector가 재무장됐더라도 12개 완전한 회복 frame을 채우지 못한 horizon 종료는 성공이 아니라
   `recovery_incomplete_timeout` 실패다. 이 실패율이 0이 아니면 curriculum 승급도 거부한다.
5. A4에서 READY를 얻지 못한 채 첫 event를 miss했을 때 다음 event를 APPROACH로 강제하던 우회를
   제거했다. RELEASE가 없는 miss는 기존 READY/APPROACH phase를 그대로 유지한다.
6. WAIT_REARM에서 차단된 중복 crossing을 false positive에 포함했다. 감사 JSON에는 accepted/blocked
   crossing별 string, direction, subframe, y, zone 허용 여부와 quality를 따로 남긴다.
7. timing/zone gate 밖의 target attempt도 timing 표본에 남기고 canonical episode metric이 live alias보다
   우선하도록 evaluation/plot alias 순서를 통일했다.
8. 목표 window가 겹치거나 전역 motor recovery보다 사건 간격이 짧은 v1 곡을 fail-fast한다. 간격 판정은
   파생 `frame`이 아니라 정본 `time`을 사용한다.
9. detector의 depth/speed/displacement/re-arm 거리를 0으로 꺼버리는 설정, 불가능한 episode horizon,
   READY lead 부족, crossing depth/re-arm 거리 불일치와 unknown curriculum key를 생성 시 거부한다.
10. recorder는 현재 checkpoint schema와 environment/training context 일치만 허용한다. MP4와 manifest는
    임시 파일 뒤 원자적으로 교체하고, 성공한 재생성은 같은 artifact의 과거 오류를 지운다.
11. 단순 거리 차 reward가 discount 때문에 가까이/멀리 왕복에 양의 누적 이득을 주던 문제를 제거했다.
    bounded reach potential에 `gamma·Phi(next)-Phi(previous)`를 적용하고 `reward.reach_discount`와
    `ppo.gamma`가 정확히 같은지 학습 시작 전에 검사한다.
12. 내부 `APPROACH` phase를 matcher의 숨은 성공 조건으로 쓰던 중복 gate를 제거했다. motor phase와
    entry waypoint는 계획·shaping 진단이며, RELEASE 정답은 물리 crossing과 줄·방향·시간·영역만으로
    판정한다. phase 불일치는 `release_phase_violation`으로 별도 노출하고 PPO rollout 진단에도 집계한다.

## 입력 곡의 현재 A4 호환성

현재 `50 ms`, re-arm `2 frame`, 최소 follow-through `1 frame` 계약을 적용한 결과다. `HOLD`는 파일을
삭제하거나 잘못된 곡으로 판정한다는 뜻이 아니라, ordered overlapping-window matcher 또는 더 빠른
motor primitive가 구현되기 전 현재 단일-event A4에 넣지 않는다는 뜻이다.

| song bundle | 상태 | 이유 |
|---|---|---|
| `02_Jazz1-200-B_solo` | PASS | 현재 기본 학습곡 |
| `05_BN1-129-Eb_solo` | PASS | window/recovery 간격 충족 |
| `05_Jazz1-200-B_solo` | PASS | window/recovery 간격 충족 |
| `03_Rock1-130-A_solo` | HOLD | 최소 92.9 ms로 ±50 ms window 중첩 |
| `05_BN2-131-B_solo` | HOLD | 최소 23.3 ms, same-string/motor re-arm과 window 모두 불충족 |
| `05_Rock2-142-D_solo` | HOLD | 최소 11.6 ms, motor re-arm과 window 불충족 |

## 검증 결과

- `python -m compileall -q tab2body`: PASS
- Strike와 관련 공용 CPU 실행 검사 18개: PASS
- `git diff --check`: PASS
- active Fret checkpoint `fret_002000.pt`의 구현 fingerprint:
  저장값과 live 값 `919f22d7…6202d26` 일치
- 공용 Strike smoke, Python 3.8 환경: 시작 전 resource guard가
  `CUDA is unavailable; refusing Isaac Gym allocation`으로 중단

CPU 묶음에는 goal/detector/event/recovery/reward/curriculum/evaluation, lazy runner, runtime-fingerprinted
curriculum wiring, checkpoint, configured kwargs, run I/O/layout, 공용 task dispatch, plot·이중 카메라 artifact
계약과 terminal logging이 포함된다. 같은 줄과 서로 다른 줄 모두의 motor/re-arm 간격을 검사한다.
CUDA가 없는 현재 결과를 GPU PASS로 표기하지 않는다.

CUDA 장비에서 다음 명령을 통과해야 이번 정리를 물리 환경까지 완료로 올린다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -m tab2body.train \
  --task strike --smoke --run-name strike_refactor_smoke
```

## 의도적으로 남긴 진단·보류

- 실제 rigid pick grasp/slip, 탄성 string/contact force와 음향
- up/alternate 입력과 방향 이력을 포함한 양방향 re-arm
- string field 밖 recovery corridor의 실제 경로와 역방향 재교차율
- phase별 어깨·팔꿈치·손목 기여율, acceleration/jerk/path curvature, 최대 depth/speed
- phase-aware motion cost와 사람 reference 기반 naturalness gate
- strike 전용 wrist envelope와 기타 관통 calibrated safety proxy
- sub-half-string across offset의 실제 GPU geometry reachability audit
- 실제 `StrikeTask.step`의 READY→APPROACH→RELEASE→A4 advance→RECOVER→종료 전 구간 scripted 회귀
- do-nothing/hover/jitter/전줄 sweep/왕복 crossing의 실제 GPU discounted-return 전수 감사
- 겹친 window를 처리하는 ordered multi-event matcher, strum/fingerstyle/hybrid

위 항목은 무시된 기능이 아니다. 현재 측정 근거가 부족하거나 다음 입력 schema가 필요하므로 reward나
성공 조건에 섣불리 넣지 않고 진단 또는 명시 보류로 남겼다.
