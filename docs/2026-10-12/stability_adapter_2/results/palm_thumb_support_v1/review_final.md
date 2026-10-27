# 손바닥·엄지 지지 — 독립 최종 검수

요약 판정: **문제없음**. 이번 구현·정식 원자료·분석 v3·최종 문서 범위에서 확인된 Critical/Warning/Suggestion은 없다. 접촉 응답 증가와 안정화 개선 실패를 구분한 결론이 원자료와 일치한다. 검수자는 새 native 실행이나 학습을 하지 않았고, 이 검수 문서 외 소스·결과를 수정하지 않았다. 최종 보존 감사·봉인은 root의 별도 기록으로 판정한다.

## Critical

없음.

## Warning

없음. 검수 중 전달한 결과 README의 실행 집계 오류와 MP4 표시, 분석 초안의 버전 구분은 담당자가 수정한 최종 문서에서 해결을 확인했다.

## Suggestion

없음.

## 코드·검증 범위

- 신규 leaf 계획4개, Python18개, shell4개와 기존 `review_pre*.md`를 읽었다. v1→v2→v3 차이와 posture 제어/분석 차이를 확인하고, 사전 검수의 수정 확인을 재사용했다. 이번 Python18개는 AST 문법 검사를 통과했다.
- [지지 제어기:61](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_v1.py:61)와 [자세 결합 제어기:58](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_posture_support_v1.py:58)는 native 한계·초기 기준 cap·목표 속도와 적분 포화를 적용한다. [native runner:62](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v3.py:62)와 [posture runner:62](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_posture_support_v1.py:62)는 ON의 외부 왼팔 PI를 비활성화하고 하나의81 PD 목표를 제출한다. 기타 상태 쓰기·손 부착·기타 외력 경로는 추가하지 않았다.
- 저장 native 상태를 이용한 두 [수치 계약 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/verification/numerical_contract.json:1), [posture 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/verification/posture_numerical_contract.json:1)의10개 검사 통과를 확인했다. 이는 live 접촉 효과의 추가 실험이 아니다.

## 원자료·분석·그림 대조

[최종 분석기:27](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_posture_support_v3.py:27)는 직접 읽는 native guard metadata를 SHA 목록에 포함하고, 완료/입력 불변 조건을 검사한다(37–38). [분석 사후 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/inputs_after.json:1)의1695개 입력과6개 check 통과를 확인했다. 현재의 직접 소비 raw JSON·PNG·guard SHA도 분석 시작 목록과 일치한다. 분석 및 정식 native 실행의 `source_before` 사본은 해당 입력 SHA와 일치하며, 이후 메인 문서 갱신본과 실행 당시 원문을 구분했다.

네 정식 실행 모두5초·1200 physics step·151 pose/camera frame·300 contact 표본이다. 접촉 기록은 step0부터1196까지4step 간격, 자세 기록은 step0부터1200까지8step 간격임을 독립 대조했다. 실제 초기 기타 p/q, PD/shape/self-collision 조건은 네 실행에서 동일하다. fresh initial audit·source-clear 및 native 제약 검사도 통과했다. root/하체 고정·몸통 PD·자유 기타·무스트랩 조건을 성공 주장으로 확대하지 않는다.

`contacts.json`에서 기타 main body pair와 양의 raw lambda를 다시 분류하고, `trace.json`의 위치·quaternion에서 초기 대비 이동과 최단 회전을 다시 계산한 결과 [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/summary.json:1)과 일치했다.

| 정식 조건 | 최대 이동 mm | 최대 회전 ° | 동시 양의 raw 응답 |
|---|---:|---:|---:|
| baseline_v4 | 62.9606 | 13.6314 | 0/300 |
| candidate_off | 62.7971 | 13.7047 | 66/300 |
| candidate_on | 96.2238 | 16.2361 | 221/300 |
| posture_on_retry | 63.3030 | 13.7575 | 133/300 |

[gate:80](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_posture_support_v3.py:80)는 기준보다 동시 응답이 늘면서 최대 이동과 회전이 모두 감소해야 한다. 후보 모두 이 조건을 충족하지 않아 `fret_gate_passed=false`가 맞다. 최대값은30Hz 자세 표본이고 접촉은60Hz 제어 직전 표본이다. 모든240Hz step의 연속 접촉, 정확한 cooked 접촉면, 뉴턴 힘, 마찰/미끄럼 안전, 전체 자연스러운 자세 집합의 성공은 인증하지 않는다. 엄지의 Fret 정책 목표와 지지 목표를 합성하는 소유권 계약도 아직 구현하지 않아 Fret/학습0이라는 기록이 정확하다.

timeline을 실제로 보고0.25초 `[a,z)` bin과 원자료의 추이를 대조했다. 대표 그림6개의24개 영상 영역은 각 조건 원native PNG의 동일 resize와 pixel-exact로 일치한다. 정식 MP4의 현재 SHA도 각 native report 기록과 일치한다. 프레임의 조건·시점 표기는 실제0/2/5초이며 source 그림을 native 렌더로 설명하지 않았다.

## 실패·초안·최종 문서

- native 시도8회 중 카메라 SIGSEGV3회와 물리5초 완료5회를 구분했다. `baseline_v3`는 물리 완료했지만 [입력 사후 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/baseline_v3/inputs_after.json:1)의 분석기1개 SHA 변경으로 정식 비교에서 제외됐다. 보수적인 전체A 목록에 든 파일이었다는 이유로 실패 기록을 없애지 않았다.
- 첫 baseline의 권위 있는 보존 개수는 [crash_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/baseline/crash_audit.json:1)의1251개다. 과거 사전 검수/leaf에 적힌1258개와 혼동하지 않는다. 당시 변경 불가 원문은 보존한다.
- source 탐색은 `search`/`search_v2`의2실행·총6후보이며 새 native 초기화/physics0이다. 실제 결과가 없는 physics-only3회 주장은 최종 README에서 제거됐다. 접촉추종 분석 v1의 실제3조건 결과와 미실행 posture 분석 v1/v2, 최종 posture 분석 v3을 구분했다.
- `posture_on`의 [부분 영상 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/partial_posture_videos/manifest.json:1)는165개 원입력 SHA 불변을 기록하며 현재 입력과 일치한다.82frame의 마지막 캡처2.7초와 journal의 마지막 완료652step/2.716667초를 구분한다. 실제 crash 발생 최종 step은 확정하지 않는다. baseline/baseline_v2의 기존 부분 영상도 정상5초로 설명하지 않았다.
- 결과 README/FILE_INDEX/CHANGED_FILES와 [메인 PLAN 추가:694](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:694), [A README 추가:1892](/home/ajou/yigyu/3/stability_adapter_2/README.md:1892), [D README 추가:587](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:587), [VISUAL_REPORT 추가:2335](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2335)를 확인했다. 접촉 증가만 관측됐으며 안정화/연주 성공은 미확인이라는 결론과 다음 제어권 설계의 미구현 상태가 일관된다. 이번 채택 gate를 전역 자연스러운 연주 성공 기준으로 새로 바꾸지 않았다.
