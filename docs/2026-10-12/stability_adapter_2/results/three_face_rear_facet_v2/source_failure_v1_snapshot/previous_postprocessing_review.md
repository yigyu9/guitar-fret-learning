# 직전 contact footprint v2 후처리 독립 검수

검수일: 2026-10-08. **요약 판정: 문제없음.** 직전 phase의 canonical summary와 새 source 비교 PNG에 대한 독립 검수를 완료했다. 기존 source V1/V2 및 feature-map v2·PNG 3개 검수는 완료 기록을 신뢰했으며 source 후보 검색·물리 실행은 반복하지 않았다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음. 기존 source V2 검수의 향후 간격 경계 후보에 대한 QP primal–dual 검증 권고는 그대로 유효하며 이번 후처리 검수에서 재판정하지 않았다.

## 완료 범위와 근거

- [analyze_contact_footprint_search_v2.py:20](/home/ajou/yigyu/3/stability_adapter_2/analyze_contact_footprint_search_v2.py:20), [정식 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/analysis_v2.json) — active stdout를 직접 입력에 넣지 않고 명시한 source 입력과 proposal의 SHA closure를 사용한다. 정식 분석의 입력 11,359개를 읽기 전용으로 재해시하여 불일치 0을 확인했다. 전체 네 후보 summary는 이전 `analysis.json`과 exact 같으며, 각 proposal의 label·reasons·anchor·goal·error·intersections·footprint·hull-to-patch 필드와도 exact 같다. V1 두 후보의 footprint/gap null은 기존 proposal에 해당 필드가 없는 상태를 그대로 보존한 것이다.
- [법선 변환:43](/home/ajou/yigyu/3/stability_adapter_2/analyze_contact_footprint_search_v2.py:43) — 저장 source state의 body/G-root quaternion과 anchor source normal로 독립 행렬 변환 `R_G.T @ R_body @ n_local`을 계산했다. 네 후보·두 body의 정식 법선과 최대 절대차는 `1.1102230246251565e-16`이다. 새 native normal이나 힘을 추정한 값이 아니다.
- [그림 입력 검증:35](/home/ajou/yigyu/3/stability_adapter_2/make_contact_footprint_artifacts_v2.py:35), [artifact_manifest_v2.json:6](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifact_manifest_v2.json:6) — plot 입력 11,363개 SHA 불일치 0, 입력 전후 mapping exact, 입력 개수 exact를 확인했다. Producer·brief·analysis·proposal·plan·분석 closure·해결된 NanumGothic font가 포함된다. PNG SHA `42852af5358fd61f5ee0242a163852a3f49687109c6c75416f8bf478de0856c5`, analysis SHA `7be08f9d08a23a30ba13944a575b136060e0faa56ec08152cfc8f5b957cf612f`, brief SHA가 실제 파일과 manifest에 일치한다.
- [분석 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/analysis_execution_v2.json), [그림 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifact_execution_v2.json) — 분석 producer SHA `18c38275c3bc9c2704c66544b354a931a7385515f9bf9ac4fbfe7087c2fb30ea`, 그림 producer SHA `30bdb6ee0701c4c1ad142491dfd1cecc8cddf53166de0864fe102d5784bd9a40`가 각각 작업본·실행 원문 복사본·실행 전후 기록에 exact 같다. 두 wrapper 원문도 읽어 실제 명령·복사·로그 보존 경로와 대조했다. 분석 9.202740초/exit 0, 그림 10.895391초/exit 0이고 기록된 native 호출은 0이다. 실제 로그 SHA, 그림 stderr SHA 및 manifest SHA도 일치하며 그림 stdout JSON은 manifest와 exact 같다.
- [실제 source PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifacts_v2/source_candidate_comparison.png), [엄지 panel:89](/home/ajou/yigyu/3/stability_adapter_2/make_contact_footprint_artifacts_v2.py:89) — 원 PNG를 직접 열었다. 좌측은 명시된 국소 확대이며 네 source 대표점과 목표의 G-root X/Y mm, V1/V2·0.3/0.7mm 표식, source 법선의 X/Y 투영이 저장 데이터와 맞는다. 기울어진 왼쪽 변의 unit inward normal로 만든 점선은 원 변과 평행하고 수직 간격은 `1.9999999999999984 mm`다. 확대 범위에 모든 대표점·목표가 포함되며 범례가 이 표본을 가리지 않는다.
- [손바닥 panel:133](/home/ajou/yigyu/3/stability_adapter_2/make_contact_footprint_artifacts_v2.py:133) — 우측 finite palm region, 두 source triangle, 대표점·SOURCE 방향 범례를 실제 PNG와 대조했다. 모든 triangle vertex가 표시 범위에 포함된다. Triangle GY 범위 `43.71560053776539…46.12336643457034 mm`, GZ 범위 `−7.618891400350661…12.039586766181364 mm`이며 Z 상단의 overhang을 그대로 보인다. 두 대표점의 내부 여유 4.721738/4.960842mm와 전체 triangle 내부라는 주장을 하지 않는 설명이 일치한다.
- [phase README:22](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/README.md:22), [VISUAL_REPORT §84:1605](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1605) — 그림은 source FK geometry이며 actual Gym frame·cooked shape·SDK normal·native force·해부학적 pad 인증이 아니라는 설명이 일치한다. 재사용한 실제 5초 native 영상은 이전 saved-finger-target reference 실행으로 표시한다. 네 후보 거절·승인 0·이번 native 초기화/physics 0과 다음 rear-facet 계획의 미실행 상태도 정식 분석 및 문서에 일치한다.
- [이전 보존 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/analysis_bookkeeping_v1/preservation.json), [실패 설명 README:34](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/README.md:34) — 이전 분석의 입력 SHA 불일치는 자신의 `analysis.log` 한 개뿐이다. 보존 목록 10개 모두 original/snapshot/기록 SHA가 일치한다. 이전 plot은 이 입력 guard에서 exit 1/native 0으로 실패했고 stderr 원문 SHA가 일치하며 해당 `artifacts` 경로의 PNG는 없다. 실패한 후처리를 성공으로 바꾸거나 원 기록을 덮어쓰지 않았다.
- [final_verification.json:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/final_verification.json:13), [동 파일:14189](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/final_verification.json:14189) — root의 42개 true check와 내장 audit source를 읽어 범위를 확인했다. 이 기록은 보존·source·summary·root 실제 PNG QA이고, 당시 canonical summary/새 PNG의 독립 검수는 `false`/pending으로 명시한다. [review_status.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/review_status.json), README 및 §84도 완료된 source/이전 feature-map 검수와 당시 도구 thread-limit에 따른 후처리 검수 대기를 구별한다. 본 기록이 그 후처리 독립 검수의 실제 완료 근거이며 과거 봉인 기록은 그대로 유지한다.

## 검증 방법과 한계

정식 JSON·producer·wrapper·문서를 읽고 SHA를 스트리밍 재계산했다. 요약은 proposal/이전 분석과 직접 비교했고 법선·2mm inset·triangle 표시 범위는 독립 재계산했다. 실제 PNG를 시각 검수하고 Python 3.8로 후처리 source 두 개의 `compile` 검사를 통과했다. root audit source는 보존 파일을 만드는 코드이므로 재실행하지 않았으며, 이번 범위 밖의 과거 phase 물리 판정과 전체 보존 검사를 독립 재실행했다고 주장하지 않는다.

검수 중 native scene 생성·물리 step·후보 검색·producer 재생성을 수행하지 않았다. 새로 작성한 파일은 이 검수 기록 하나뿐이다. 기존 frozen source·결과·review·final_verification·inventory·source_final은 수정하지 않았다. 이번 완료 판정은 source 후처리 정합성에 한정되며 실제 접촉·지속 지지·안정성 또는 연주 성공을 인증하지 않는다.
