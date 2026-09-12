# 01. Audio → Tablature

> 상태: **현재 Stage1 파이프라인 구현 / 공통 schema 정식 봉인 전**

## 책임

오디오 또는 주어진 음악 annotation을 기타에서 연주할 수 있는 음표와 선택된 줄·프렛의 시간 이벤트로 변환한다.

이 단계의 출력은 아직 어느 왼손 손가락을 사용할지, 오른손이 어떤 궤적으로 칠지 결정하지 않는다.

## 입력

```text
AudioSource {
    audio_path
    sample_rate
    channel_layout
    optional_bpm
    optional_time_signature
    optional_key
}
```

추가로 사람이 검수한 annotation이 있으면 confidence와 provenance를 함께 입력한다.

## 처리 단계

```text
audio normalization
→ onset / offset extraction
→ pitch / chord / beat estimation
→ note grouping
→ guitar feasibility search
→ candidate tablature
→ human or rule-based validation
```

## 출력 계약

```text
TablatureSong {
    song_id
    tuning
    tempo_map
    timebase_fps
    notes[] {
        note_id
        onset_s
        offset_s
        pitch
        string_index
        fret_index
        velocity
        confidence
    }
    chord_groups[]
    source_hash
    schema_version
}
```

`onset_s`와 `offset_s`가 이후 모든 event의 시간 기준이다. 각 손이 이 시간을 별도로 재작성하지 않는다.

## 이 단계에서 하지 않는 일

- 왼손 finger 번호 확정
- 왼손 finger와 hand position 확정
- 오른손 down/up 방향 확정
- 관절 action 생성
- 물리 환경의 readiness 또는 strike 성공 판정

## 실패와 검수

초기 학습에서는 confidence를 이유로 Tablature event를 제외하거나 reward weight를 낮추지
않고 생성된 결과를 모두 사용한다. confidence와 provenance는 사후 오류 분석과 subgroup
평가를 위해 보존한다.

다음 항목도 confidence만 낮다는 이유로 제외하지는 않는다. 다만 schema나 기타의 표현
가능 범위를 실제로 위반하면 학습 데이터가 아니라 입력 계약 오류로 처리한다.

- pitch confidence가 낮은 구간
- onset이 겹치거나 불명확한 구간
- 기타 tuning으로 표현할 수 없는 음
- chord의 줄 수가 물리적 손가락 수를 초과하는 구간
- tempo map이 불연속인 구간

각 note와 chord group은 `confidence`, `source`, `review_status`를 가져야 한다. 이 값은
초기 training inclusion gate가 아니라 진단 metadata다. 음수·역전 duration, 유효 범위 밖
string/fret, 비단조 시간처럼 실행 불가능한 구조 오류는 명확히 validation failure로
보고하며 정상 event로 변환하지 않는다.

## 현재 코드와 연결

기본 실행 진입점은 `tab2fingermapping/`에 있다. 생성된 중간 산출물은 곡 단위 [song bundle](/home/ajou/yigyu/3/data/song_bundles/README.md)에 등록하기 전에 schema와 시간 convention을 검사한다.
