# 영상 모음 v20 metadata 독립 검수

요약 판정: **문제없음 / PASS**. Critical 없음, Warning 없음, Suggestion 없음. [v19 review](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/video_collection_v19/review.md:1)에 남긴 두 HOLD 표기 오류가 별도 v20에서 해소됐다. 원 v19의 소비 소스·색인·manifest·검수 기록은 수정하지 않았다.

- 원 timed-ENTRY retry report는 completed/HOLD/source-terminal이고, 원 controls의 마지막 79행 및 trace의 41행은 HOLD다. 첫 HOLD는 3.683333333초, 마지막 trace는 5초다. 같은 native 실행의 실제 raw를 읽어 확인했으며 재실행은 없다.
- v19/v20 manifest를 독립 구조 대조했다. 두 source-inventory row와 두 new-copy row의 동일 experiment metadata만 정정했고, version/보정 감사 설명 이외의 값은 exact다. 색인 두 행도 “예 (HOLD 시작 3.683333초; controls 79행)”로 정정됐고 절대 링크는 유효하다.
- producer의 7개 직접 입력 SHA 시작/종료 기록 및 현재 bytes가 모두 일치한다. 원 v19 SHA도 이전 독립 검수 값과 같다. archive 266개 SHA를 다시 대조했고 v19 inventory와 동일하다. 이번 영상 추가·복사·인코딩은 0개이며 기존 172 + 이전 추가 94의 스냅샷 범위를 유지한다.
- `correct_metadata.py`는 저장 report/controls/trace와 v19 metadata를 읽고 별도 v20 metadata를 쓴다. native/physics API 호출은 없다. 파일 재생시간·HOLD 지속은 음악 완주나 물리 평형의 인증이 아니다. snapshot 밖 lateral-staging 영상의 포함 여부도 바꾸지 않는다.

검수 SHA256:

| 파일 | SHA256 |
|---|---|
| correct_metadata.py | `f888748fef9f53fbbfff119cb782278ba7bbb9ffceddd136f02c115655de7d83` |
| video_manifest_v20.json | `f6546c7d44253fcc5505673fe9b2e4502f2fe2ddb0a8f6d1561e44d9b0cc6dbe` |
| VIDEO_INDEX_v20.md | `9482df4fb01a43bb0b6e5d8dcac87d1d069c212bc1574438bdfdb97debcba82c` |

남은 actionable finding은 없다. 검수 중 물리 실행·수집기 재실행·다른 담당 파일 변경은 없었다.
