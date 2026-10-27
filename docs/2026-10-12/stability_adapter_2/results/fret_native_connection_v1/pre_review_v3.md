# Fret native 전이 연결 v3 수정 검수

요약 판정: **문제없음 — 사전 검수 PASS**. Critical / Warning / Suggestion 없음. Native 재실행 차단 사항 없음.

이번 검수는 v2 대비 변경된 두 누락 파일 분류 조건과 wrapper 실행 대상만 확인했다. v2 실행은 누락된 chair XML의 SHA를 읽다가 physics 0 / actor 0 / camera 1 frame에서 종료했으므로 Fret 물리 실행 성공으로 취급하지 않는다. 기존 출력과 소스는 보존된다.

- [run_fret_native_connection_v3.py:68](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v3.py:68): asset 지문 파일이 없으면 `not path.is_file()`에서 단락 평가되어 SHA 읽기를 생략하고 해당 경로를 차이 목록에 기록한다. 누락 자산을 복원하거나 검증된 goal/profile/model 계약을 완화하지 않는다.
- [run_fret_native_connection_v3.py:70](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v3.py:70): implementation 지문에도 같은 누락 처리 조건을 적용한다. 물리·정책·제어·준비 시간·원본 종료 조건의 변경은 없다.
- [fret_native_v3_preserved_run.py:54](/home/ajou/yigyu/3/stability_adapter_2/fret_native_v3_preserved_run.py:54): 실행 대상만 새 v3 runner로 변경한다. 실행 전 입력 보존과 실행 후 SHA 불변 검사는 유지한다.

검증: 새 Python 2개 AST parse PASS. [missing_asset_preflight.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/missing_asset_preflight.json)의 누락·동일 SHA·다른 SHA 분류 3개 검사 PASS를 확인했다. 실제 운지·안정성 결과는 재실행 후 검수한다.
