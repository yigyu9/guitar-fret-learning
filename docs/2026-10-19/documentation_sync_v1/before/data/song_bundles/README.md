# 곡별 입력 정본 (`data/song_bundles`)

> 최종 갱신: 2026-09-07

이 디렉터리는 검수를 마치고 fret/strike 환경에 넣을 곡별 입력의 **정본**이다.
`tab2fingermapping/_gen`과 `tab2body/_gen`은 재생성 가능한 작업 공간이며 학습 기본 경로로
사용하지 않는다.

## 고정 구조

```text
data/song_bundles/<song_id>/
├── source/
│   ├── audio.wav
│   └── annotation.jams              # 있을 때만
├── mapping/
│   ├── tablature.notes.csv          # string,start,end,pitch
│   ├── fingering.json               # 왼손 운지 정본
│   ├── chords.json                  # Stage1 생성 시
│   └── notes.json                   # Stage1 생성 시
├── training/
│   ├── fret_training.json           # 60 Hz 왼손 goal
│   ├── hand_position_targets.json
│   ├── strike_training.json         # 원본 [time, frame, string]
│   └── strike_plan.json             # single/strum/down/up 확정 RL 입력
├── preview/
│   └── fingering.png
└── manifest.json                    # 해시·출처·진단·학습 입력 가용성
```

폴더 이름인 `song_id`가 곡의 식별자다. 내부 파일명은 모든 곡에서 동일하다. 학습 run과
checkpoint에는 실제 goal 파일의 SHA-256이 별도로 봉인되므로 같은 song ID의 내용을 바꾸면
기존 checkpoint를 그대로 resume하지 않는다.

## 데이터 흐름

```text
원본 오디오
→ tab2fingermapping/_gen/<song>_stage1 (작업 산출물)
→ 검수
→ data/song_bundles/<song_id> (정본 등록)
→ training/fret_training.json 또는 strike_training.json
→ strike는 전체 phrase compiler → strike_plan.json
→ Full은 네 입력을 Canonical PlayEvent로 compile
→ Isaac Gym 또는 G0 CPU contract probe
```

Stage1 결과 등록:

```bash
cd /path/to/yigyu/3
python -m tab2body.tools.register_song_bundle <song_id> \
  --stage1 tab2fingermapping/_gen/<song>_stage1 \
  --annotation guitar_v3/data/moum/annotation/audio_mono-mic/<song>.jams
```

fret 입력은 검수된 `mapping/fingering.json`에서 만든다.

```bash
cd /path/to/yigyu/3
python -m tab2body.tools.build_fret_training_data \
  --fingering data/song_bundles/<song_id>/mapping/fingering.json \
  --audio data/song_bundles/<song_id>/source/audio.wav \
  --out data/song_bundles/<song_id>/training/fret_training.json \
  --hand-targets-out data/song_bundles/<song_id>/training/hand_position_targets.json
```

pick strike 원본과 최종 계획은 다음 두 단계로 생성한다.

```bash
cd /path/to/yigyu/3
python -m tab2body.tools.build_strike_training_data \
  data/song_bundles/<song_id>/mapping/fingering.json \
  --out data/song_bundles/<song_id>/training/strike_training.json

python -m tab2body.tools.build_strike_plan \
  data/song_bundles/<song_id>/training/strike_training.json \
  --require-original-tempo-feasible \
  --out data/song_bundles/<song_id>/training/strike_plan.json
```

compiler는 물리 최소 간격 안의 서로 다른 줄을 하나의 strum 후보로 묶는다. 시간차가 충분한
단조 줄 순서는 방향 증거로 사용하고, 나머지는 전체 phrase의 회복·이동 비용으로 결정한다.
같은 묶음 안의 동일 줄 재타현은 아직 지원하지 않으므로 fail-closed 한다.

Full G0 조립에서는 `mapping/fingering.json`, `fret_training.json`, `strike_training.json`,
`strike_plan.json`을 함께 검증한다. 실제 sounding fret은 strike frame의 dense Fret raster가
아니라 `source_event_id`로 연결한 fingering note에서 가져온다. Barre, finger가 없는 fretted
note, 지원되지 않는 strike gesture는 strict compiler에서 fail closed한다.

계획 생성 전후에는 전체 데이터 품질을 검사한다.

```bash
python -m tab2body.tools.audit_strike_goal_quality \
  --all \
  --format human \
  --strict
```

검사는 fingering/raw/JAMS onset, 묶음 경계, 실제 traversal edge 간격과 방향 반전 재통과를 함께
확인한다. `INFEASIBLE`은 full-song 학습을 시작하지 않는다. upstream 시각이 서로 충돌하면 원본을
조용히 덮어쓰지 않고 별도 JSON에 연속 source ID, `merge|separate`, 이유, 근거와 선택적
`resolved_times_s`를 기록한 뒤 `--review-overrides`로 raw/plan을 재생성한다.

## 환경에서 선택

fret의 기본 곡은 `02_Jazz1-200-B_solo`, strike 코드의 기본 곡은
`00_SS1-68-E_comp`다. 2026-08-30에 source 147~149를 하나의 down strum으로 승인해 정본 plan을
재생성했으며 original-tempo preflight를 통과한다.

```bash
conda activate rl38
export PYTHONPATH="$PWD/isaacgym/python:$PWD${PYTHONPATH:+:$PYTHONPATH}"
python -m tab2body.train --task fret --song 02_Jazz1-200-B_solo --smoke --num-envs 8
python -m tab2body.train --task strike --song 02_Jazz1-200-B_solo --smoke --num-envs 8
```

`--song`은 각 번들의 `training/` 파일을 해석한다. 외부 파일을 일시적으로 시험할 때만 기존
`--goal /absolute/path.json`을 사용한다. `--song`과 명시적 `--goal`은 함께 사용하지 않는다.

## 2026-08-30 strike 품질 감사 상태

| song_id | strike 감사 | 핵심 판정 |
|---|---:|---|
| `00_SS1-68-E_comp` | `AMBIGUOUS` | 승인된 source 147~149 merge 적용; 최소 edge 51.0 ms, 물리 불가 전이 0 |
| `02_BN3-119-G_solo` | `AMBIGUOUS` | strike raw/plan 없음, source onset 추가 검토 |
| `02_Jazz1-200-B_solo` | `PASS` | 원속도 전이 통과 |
| `03_Rock1-130-A_solo` | `AMBIGUOUS` | 일부 source onset 차이 검토 |
| `05_BN1-129-Eb_solo` | `AMBIGUOUS` | 일부 source onset 차이 검토 |
| `05_BN2-131-B_solo` | `AMBIGUOUS` | 일부 source onset 차이 검토 |
| `05_Jazz1-200-B_solo` | `PASS` | 원속도 전이 통과 |
| `05_Rock2-142-D_solo` | `AMBIGUOUS` | source onset 및 묶음 경계 검토 |

위 표는 Strike 입력 감사 결과이며 Full G0 source qualification을 뜻하지 않는다. 현재 알려진
Full compiler 예외로 `00_SS1`의 finger 없는 fretted note, `02_BN3`의 strike 입력 부재,
`05_BN2`의 지원되지 않는 alternate-restrike가 있다. `02_Jazz1`은 canonical timeline 조립
검증에 사용할 수 있지만, 실제 G0 평가는 별도의 qualified Fret·Strike checkpoint가 필요하다.

전체 상세 결과는 `docs/archive/dated/2026-08-30/strike_goal_quality_audit.txt`와 JSON에 저장한다.
