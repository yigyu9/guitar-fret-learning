# 봉인 V2 형식 교정 독립 검수

요약 판정: 문제없음. Critical: 0

검수는 V1→V2 diff·원본 형식 오류·정규화 객체 및 예외 범위만 대상으로 했다. 봉인 전체 실행·추가 물리 실행·기존 파일 수정은 하지 않았다. 원물리/수치/문서 판정은 소비된 [review_final_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/review_final_v1.md:1)을 유지한다.

## Critical

- 0. [seal_outputs_v2.py:9](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/seal_outputs_v2.py:9)는 특정 resolved 절대 파일 하나와 원본 SHA를 확인하고, 마지막 두 문자가 literal backslash+n인 경우에만 제거한다. 실제 read 호출 결과가 [archive_pd_provenance_normalized_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/archive_pd_provenance_normalized_v1.json:1)의 original_object 및 원본 raw의 마지막 두 문자만 제거한 JSON과 정확히 같았다.

## Warning

- [archive_pd_correction_provenance_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/archive_pd_correction_provenance_v2.json:1)은 형식 오류를 가진 원본 그대로 보존한다. 일반 strict JSON reader에서는 계속 ExtraData 오류가 난다. 이 파일의 분석에는 SHA가 고정된 제한적 교정 또는 별도 normalized 기록을 사용하며, 원본을 정상 JSON이라고 인증하지 않는다.
- [sealer_v1_failure.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/sealer_v1_failure.json:1)은 metadata 형식 실패이고 물리·수치 실패가 아니다. 검수 시점 V1/V2의 source_final·artifact_inventory·final_verification 총6개 출력은 모두 존재하지 않았다. 새 V2 완료는 실제 실행 후 생성되는 파일로 확인한다.

## 확인 근거

- [seal_outputs_v2.py:14](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/seal_outputs_v2.py:14): 다른 경로에 동일한 잘못된 JSON을 공급한 순수 mock 검산은 JSONDecodeError를 유지했다. 일반 JSON에 대한 범용 strip·재시도·오류 무시를 추가하지 않았다.
- [seal_outputs_v2.py:107](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/seal_outputs_v2.py:107): 출력은 source_final_v2/artifact_inventory_v2/final_verification_v2 새 경로이며 exclusive 생성 정책을 유지한다. read 함수와 이3개 출력명 차이를 제외한 AST 전체가 V1과 정확히 같았다. 이전 audit/물리/math/copy/link 조건이 변경되지 않았다.
- [sealer_before_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/sealer_before_v2.json:1)의 현재 SHA 두 개 모두 일치했다. 새 sealer AST도 통과했다. 검수 코드 SHA는 `1b5fe64e203a9fb22e459e0c37c1455c81aa7efc296afb21415e014eff25b5fe`, 원본 오류 파일 SHA는 `ad9574b803518877f68bbfb5e989cb1bb6ee88492daf28b009c97f7dc89e57c6`이다.

## Suggestion

- 선택 사항 없음. root가 동일 SHA를 확인하고 V2 봉인을 실행한다.
