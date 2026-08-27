# tab2fingermapping — 오디오 → 탭 + 코드 트랙 (→ 운지) Stage1

> 최종 갱신: 2026-08-03. 2026-07-15 재구성에서 구 `tabtrans/`의 활성 컴포넌트(conformer v1·consonance-ACE·chordtrack)를
> 이곳으로 통합. `tabtrans/`는 아카이브(legacy 실험·examples)로 남음.
> 다음 단계인 finger mapping(설계 = `docs/finger-mapping-design.md`)도 이 패키지에 구현 예정.

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
`tab2body/tools/register_song_bundle.py`로
[`data/song_bundles/<song_id>`](../data/song_bundles/)에 등록한다. Isaac Gym은 Stage1 `_gen`
경로를 직접 읽지 않는다.

## 관례·주의

- **줄 번호**: CSV/모델 = 0이 low-E, note JSON = frets[5]가 low-E (csv_to_notejson이 반전) — PROJECT_CONTEXT §7.
- v1 그리드 86.13fps(hop 256)가 공통 시간축. ACE(43.07fps)는 .lab 구간으로만 소비.
- ACE 파라미터는 검증된 완화 세트(τ0.3, min-dur 0.25s) 고정 — 근거는 PROJECT_CONTEXT §2(07-15 ACE 평가) — ace_eval은 07-16 유실.
- 37클래스 어휘 `chords.py`는 `chordtrack/` 안에 자립(07-16 구 conformer_v2에서 추출). 구 conformer_v2 실험은 `../legacy/tabtrans_archive/`.
