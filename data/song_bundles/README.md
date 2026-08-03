# 곡별 입력 정본 (`data/song_bundles`)

> 최종 갱신: 2026-08-03

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
│   └── strike_training.json         # 단음 pick 입력만
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
→ Isaac Gym
```

Stage1 결과 등록:

```bash
cd /path/to/yigyu/3
python tab2body/tools/register_song_bundle.py <song_id> \
  --stage1 tab2fingermapping/_gen/<song>_stage1 \
  --annotation guitar_v3/data/moum/annotation/audio_mono-mic/<song>.jams
```

fret 입력은 검수된 `mapping/fingering.json`에서 만든다.

```bash
cd /path/to/yigyu/3
python tab2body/tools/build_fret_training_data.py \
  --fingering data/song_bundles/<song_id>/mapping/fingering.json \
  --audio data/song_bundles/<song_id>/source/audio.wav \
  --out data/song_bundles/<song_id>/training/fret_training.json \
  --hand-targets-out data/song_bundles/<song_id>/training/hand_position_targets.json
```

pick-only strike 입력은 onset이 엄격히 증가하고 60 Hz 한 프레임에 한 음만 있을 때 생성한다.

```bash
cd /path/to/yigyu/3
python tab2body/tools/build_strike_training_data.py \
  data/song_bundles/<song_id>/mapping/fingering.json \
  --out data/song_bundles/<song_id>/training/strike_training.json
```

동시 onset이 있는 곡을 임의로 한 음으로 줄이지 않는다. 해당 곡은 `manifest.json`에
`training_status.strike.state=ineligible`로 남기고 향후 strum/polyphonic mapper를 기다린다.

## 환경에서 선택

기본 곡은 `02_Jazz1-200-B_solo`다.

```bash
conda activate rl38
export PYTHONPATH="$PWD/isaacgym/python:$PWD${PYTHONPATH:+:$PYTHONPATH}"
python -m tab2body.train --task fret --song 02_Jazz1-200-B_solo --smoke --num-envs 8
python -m tab2body.train --task strike --song 02_Jazz1-200-B_solo --smoke --num-envs 8
```

`--song`은 각 번들의 `training/` 파일을 해석한다. 외부 파일을 일시적으로 시험할 때만 기존
`--goal /absolute/path.json`을 사용한다. `--song`과 명시적 `--goal`은 함께 사용하지 않는다.

## 2026-08-03 등록 상태

| song_id | tablature/fingering | fret | pick-only strike |
|---|---:|---:|---:|
| `02_Jazz1-200-B_solo` | 준비됨 | 준비됨 | 준비됨 |
| `00_SS1-68-E_comp` | 준비됨 | 준비됨 | 보류: 동시 onset |
| `02_BN3-119-G_solo` | 준비됨 | 준비됨 | 보류: 동시 onset |
| `03_Rock1-130-A_solo` | 준비됨 | 준비됨 | 준비됨 |
| `05_BN1-129-Eb_solo` | 준비됨 | 준비됨 | 준비됨 |
| `05_BN2-131-B_solo` | 준비됨 | 준비됨 | 준비됨 |
| `05_Jazz1-200-B_solo` | 준비됨 | 준비됨 | 준비됨 |
| `05_Rock2-142-D_solo` | 준비됨 | 준비됨 | 준비됨 |
