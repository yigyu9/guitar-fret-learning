# tab2fingermapping — 오디오 → 탭 + 코드 트랙 + 운지 Stage1

> 최종 갱신: 2026-08-03. 2026-07-15 재구성에서 구 `tabtrans/`의 활성 컴포넌트(conformer v1·consonance-ACE·chordtrack)를
> 이곳으로 통합. `tabtrans/`는 아카이브(legacy 실험·examples)로 남음.
> Finger mapping까지 이 패키지에 구현되어 `*.fingering.json`을 생성한다.

## 구성

| 경로 | 역할 |
|---|---|
| `pipeline.py` | **통합 컨트롤러** — 오디오 1파일 → 탭 CSV + ACE .lab + 융합 코드 트랙(+note JSON) |
| `SETUP.md` | **환경 매뉴얼** — conda env `tab2fm` 생성·검증·트러블슈팅 |
| `conformer/` | v1 탭 전사 (transcribe.py + conformer 패키지 + ckpt, frame F1 0.835/note 0.596) |
| `ace/` | consonance-ACE 클론 (ISMIR 2025, 로컬 패치 2건 — SETUP.md §4) |
| `chordtrack/` | 코드 트랙: 탭→규칙 1차 + 시간 필터 + ACE 융합 게이팅 (moum 게이트 통과, `REPORT.md`) |
| `fingermapping/` | **왼손 운지 배정** — 규칙 1~5(그립 사전+포지션+빔 서치+생체역학+울림 유지), 설명 = `ALGORITHM.md` |
| `csv_to_notejson.py` | 탭 CSV → note JSON (tab2body goal 입력, stdlib만) |
| (`ace_eval/`, `onset_split/` → `../../legacy/`로 이동, 07-16) | ACE 평가·onset분리 실험 아카이브. 현 파이프라인 미사용, `legacy/README.md` 참조 |

## 실행

```bash
export PROJECT_ROOT="/path/to/yigyu/3"
conda activate tab2fm                         # 환경 셋업 = SETUP.md
PY="$(command -v python)"
cd "$PROJECT_ROOT/tab2fingermapping"
$PY pipeline.py <audio.wav> --bpm 117        # 전체 번들
$PY pipeline.py <audio.wav> --skip-ace       # 탭→규칙+필터만
```

출력 번들 `<stem>_stage1/`: `*.notes.csv`(탭), `*.lab`(ACE 2차 증인),
`*.chords.json`(융합 코드 트랙 — conf: 3=합의, 2=단독증인, 1=불일치 플래그, 0=N),
`*.fingering.json`(왼손 운지 — 노트별 finger/barre/grip/t_cut + 손 상태 P + 진단),
`*.notes.json`(--bpm 시).

`_gen/<stem>_stage1`은 검수 전 작업 산출물이다. 환경 입력으로 확정한 곡은
프로젝트 루트에서 `python -m guitar_learning.tool.register_song_bundle <song_id> --stage1 <stage1_directory>`로
[`data/song_bundles/<song_id>`](../data/song_bundles/)에 등록한다. Isaac Gym은 Stage1 `_gen`
경로를 직접 읽지 않는다.

타임라인은 프로젝트 루트에서 `python -m guitar_learning.tool.render_timeline <fingering.json> <out.png> [strike_training.json]`으로 생성한다. 곡 입력 생성·계획·감사는 [도구 안내](/home/ajou/yigyu/3/guitar_learning/tool/README.md)를 따른다.

## 관례·주의

### 물리 학습용 프렛 범위 (2026-11-02 추가)

물리 학습에 전달할 탭·운지는 **압현하는 음을 1~14프렛으로 제한**하는 것을 작업 기준으로 한다.
개방현(0프렛)은 별도로 허용한다. 15프렛 이상은 기본 학습용 목표에서 제외한다.

- 전사 결과에 15프렛 이상이 있으면, 같은 음높이를 유지하면서 다른 줄의 0~14프렛으로
  옮길 수 있는지 확인하고 동시음·지속음·운지를 함께 재검사한다. 단순히 프렛 값을 14로
  잘라내면 음높이가 바뀌므로 그렇게 처리하지 않는다.
- 대체 운지를 찾지 못한 음은 범위 밖 목표로 기록하고 검토 대상으로 남긴다.
  조용히 삭제하거나 음높이를 바꾼 결과를 원곡과 동일한 입력으로 등록하지 않는다.
- 현재 운지 배정기는 입력 탭의 줄·프렛을 고정한 상태에서 손가락을 배정한다.
  따라서 범위 밖 음의 줄 변경은 운지 배정 전에 처리하고, 번들 등록 전 최종 산출물에서도
  범위 위반을 확인해야 한다. **이 문서 추가만으로 실행 코드에 자동 제한이 적용되지는 않는다.**

이 제한은 현재 휴머노이드·기타의 접근성에 맞춘 운영 기준이다. 1~14프렛의 모든
손가락·줄 조합에서 압현 성공을 보장하는 것은 아니다. 15~16프렛은 별도 경계 검증,
17~22프렛은 학습 보류로 구분한다.
[기타 범위 이미지](../docs/2026-11-02/기타_14프렛_범위.png)와
[검증 근거](../docs/2026-11-02/압현실험/단일압현/재실험_공통출발_v1/분석/최종결과.md)를 참고한다.

### 기존 입력·실행 관례

- **줄 번호**: CSV/모델 = 0이 low-E, note JSON = frets[5]가 low-E (csv_to_notejson이 반전) — PROJECT_CONTEXT §7.
- 물리 학습에 등록한 뒤에는 Full compiler가 source event ID와 string-convention manifest를 다시
  검증한다. Stage1 `_gen` 산출물을 checkpoint 입력으로 직접 사용하지 않는다.
- v1 그리드 86.13fps(hop 256)가 공통 시간축. ACE(43.07fps)는 .lab 구간으로만 소비.
- ACE 파라미터는 검증된 완화 세트(τ0.3, min-dur 0.25s) 고정 — 근거는 PROJECT_CONTEXT §2(07-15 ACE 평가) — ace_eval은 07-16 유실.
- 37클래스 어휘 `chords.py`는 `chordtrack/` 안에 자립(07-16 구 conformer_v2에서 추출). 구 conformer_v2 실험은 `../legacy/tabtrans_archive/`.
