# 곡 번들

검수한 곡별 입력의 정본을 보관한다. 현재 연속 학습 대상은 `05_BN2-131-B_solo`다.

## 파일 구조

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

곡ID는 디렉토리 이름이고 내부 파일명은 공통이다. `manifest.json`은 입력 출처·파일SHA·검수 정보를 기록한다. 학습은 실제 사용한 파일의SHA를 별도로 보존한다.

## 현재 학습 목표

[전곡 시간표 구성](/home/ajou/yigyu/3/guitar_learning/song/task.py)은 원곡의67음을 읽고 누락·중복과동일현의충돌을검사한다. 재타현 묶음의 두 음은 원note-on으로 펼치고 묶음 방향을상속한다. 원오디오와목표시계, 정책 준비3초를 구분하여1969tick의 에피소드를 구성한다.

[오디오·운지 생성](/home/ajou/yigyu/3/tab2fingermapping/README.md)에서 만든 목표를 검수한 뒤 등록한다. 곡 등록과 데이터 생성은 [guitar_learning/tool](/home/ajou/yigyu/3/guitar_learning/tool/README.md)을 사용한다. `tab2fingermapping/_gen`은 검수 전 작업 공간이며, 예전 `tab2body/_gen`은 구형 코드와 함께 보관했다.

학습 입력을 바꿀 때에는 새 버전으로 보존하고 기존checkpoint의strict resume와 혼용하지않는다. 이번 문서 정리는 곡 번들의JSON·오디오·매핑 파일을 변경하지 않는다.
