# Rear facet V2 실제 source 결과·후처리 독립 검수

검수일: 2026-10-08. **요약 판정: 문제없음.** 실제 네 source 후보와 정식 분석·실행 증거·새 PNG·한국어 문서의 최종 독립 검수를 완료했다. 네 후보 모두 거절, 승인0, 이번 native 초기화/physics step0이다. 기존 source/recovery 사전 검수는 유지하며 실제 후보 검색을 재실행하지 않았다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음.

## 실제 후보·불변 조건

- [source 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/search_execution.json), [proposal](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/proposal.json) — 검색9.785138958초/exit0/native0, rejected4/accepted0이다. Source producer SHA `0120843f1a07d51f65f35fe0666652dbcbf319b6408260719a22b24badc2be33`가 실행 전후·현재 producer·실행 원문 복사본에 exact 같으며 source log와 wrapper 입력 전후 SHA도 일치한다. Proposal 입력11,353개 SHA 불일치0을 확인했다.
- [정식 분석 검증:8](/home/ajou/yigyu/3/stability_adapter_2/analyze_rear_facets.py:8) — 이전 중단 실행의 첫 partial 후보와 새 첫 후보의 q81/T81·anchor/goal·source intersection·reasons를 직접 대조해 exact 반복을 확인했다. 원 실패를 네 후보 정상 완료나 native 실행으로 바꾸지 않았다.
- [row 검증:10](/home/ajou/yigyu/3/stability_adapter_2/analyze_rear_facets.py:10) — 실제 네 후보의 예상 초기각 배열과 source DOF pos가 exact 같다. 팔12/엄지5의 row별 .10/.20rad bounds 및 native limit 안에 있고 나머지64 초기각·전체81 절대 목표가 원 값과 exact 같다. 기타 body state 전체와 절대 LA `1.1018469719600776m`도 기준 저장 native 입력과 exact 같다. 실제 팔 최대 변화는0.012212/0.012294/0.017386/0.049005rad, 엄지 최대 변화는0.063163/0.057612/0.051610/0.199907rad이다. 기존 gain·root/하체 고정·다른 손가락·오른팔손/몸통 제어 재사용 계약은 사전 검수 범위로 유지한다.
- [facet 선택 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/facet_selection.json) — 기록된 triangle323/eligible367과 proposal·analysis의 선택 기록이 일치한다. 저장 local triangle의 centroid와 anchor가 exact 같고, vertex cross product로 독립 계산한 면적은 `4.433116826174715mm²`로 기록에 일치한다. 실제 네 엄지 대표점의 finite rear patch 외부 여유를 독립 segment 거리로 재계산해 `9.853196/10.034031/10.548651/9.208566mm`를 확인했다.
- [source geometry 검사:315](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:315) — 저장된 각 후보 body pose에서 활성 source mesh를 읽기 전용으로 재구성했다. 실제 thumb/palm anchor 재계산의 최대 절대차는0이다. 네 후보의 기록된 양의 human–guitar 교차10개를 별도 centered-mm Chebyshev-radius LP로 계산했고, 첫/마지막 후보는 모든 human–guitar 쌍을 대조했다. 교차 수3/4/2/1 및 body pair가 일치하며 반경 최대차는 `7.88079454125401e-17m`다. 마지막 후보도 index3–fret3 공통반경 `0.059610375mm`가 남는다. 이 값은 source convex intersection의 공통 내접반경이고 실제 물리 관통 깊이가 아니다.

## 실제 거리 구간·정식 분석

- [root 거리 원자료 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/interval_data_verification.json) — 실제 네 후보·두 body의 저장 witness8개를 독립 재계산했다. Hull의 모든 plane 잔차와 finite quad 두 triangle에 대한 witness 포함을 대조했고, 거리 상한 및 source vertex support-plane 하한을 다시 계산했다. 최대 hull violation0mm, 최대 polygon witness 오차 `5.5669825123761294e-15m`였으며 원 gap/새 root 검사와 상·하한 차이는 각각 `1e-12m` 미만이다.
- [거리 gate:369](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:369), [README:20](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/README.md:20) — solver success=false는 둘째(.10rad/.7mm) 후보의 palm 한 개다. Proposal 구간 `4.281297406580361…4.281297551999994mm`와 독립 재계산 구간 `4.281297406580675…4.281297552000064mm`가 일치하며 README의 `[4.281297407,4.281297552]mm` 표시는 올바르다. 1mm 상한을 넘으므로 거절된다. False를 최적해나 통과로 바꾸지 않았고 다른 모든 명확한 교차·목표 오차·patch 여유 거절도 유지된다.
- [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/analysis.json) — 네 summary의 모든 직접 field를 proposal과 대조해 exact 같음을 확인했다. Thumb/palm 오차는 anchor−goal의 3차원 norm(mm)으로 독립 계산해 일치한다. 분석의 입력11,363개 SHA 불일치0이며 first-partial/불변 조건/거리구간/봉인 checks가 실제 자료와 맞는다.
- [analysis_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/analysis_execution.json) — 실제 명령은 `python /tmp/summarize_rear_facets.py`이며 실행 원문·phase의 `analysis_source.py`·보존용 구현 `analyze_rear_facets.py`가 SHA `6611fa6a88006b9814d493206e7e9787b063e239c277fc18a0b68ea89abd7952`로 exact 같다. Exit0 관측·analysis SHA·native0 metadata를 확인했다. 이 기록은 분석 runtime 측정을 주장하지 않으며 main 구현 copy가 당시 실행 경로였다고 설명하지 않는다.

## 실제 그림·문서·입출력 봉인

- [실제 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifacts/rear_facet_source_comparison.png), [producer:109](/home/ajou/yigyu/3/stability_adapter_2/make_rear_facet_artifacts.py:109) — 원 PNG를 직접 열어 양 panel·한국어·legend·label leader를 대조했다. 왼쪽은 명시된 국소 확대이며 초기점·후보4점·목표가 모두 X `[−40,−16]mm`, Y `[50,82]mm` 범위 안에 있다. 범례가 실제 점을 가리지 않고 leader는 후보와 연결된다. 각 patch edge의 inward-offset 직선 교점을 독립 계산해 수직2mm inset 오차0mm를 확인했다.
- [목표 표시:134](/home/ajou/yigyu/3/stability_adapter_2/make_rear_facet_artifacts.py:134), [paired bar:161](/home/ajou/yigyu/3/stability_adapter_2/make_rear_facet_artifacts.py:161) — 네 엄지 목표는 XY가 exact 같아 별표 하나로 표현되지만 GZ는 `−0.0083/−0.0087m`로 clearance별 다르다. 범례와 README가 이 차이를 명시하며 우측 막대는3차원 norm이다. 막대/표의 thumb 오차14.047475/13.682516/14.499266/12.609899mm, palm 오차5.701879/4.772728/4.270202/1.810477mm와 교차3/4/2/1을 원 field·brief에 대조했다. 작은 마지막 palm 오차를 승인으로 해석하지 않는다.
- [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifacts/artifact_manifest.json), [artifact 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifact_execution.json) — 그림 입력11,367개 SHA 불일치0, 입력 전후 mapping exact이다. Producer·brief·analysis·source/recovery 기록·분석 입력 closure·NanumGothic font가 봉인된다. Producer SHA `91fb9fac6da825d59959880e4d3c4a937765af306f96e4bee32cf7fc39c62584`가 작업본/원문 복사본/실행 전후 exact 같고, 5.638160799초/exit0/native0이다. Wrapper 원문·log/빈 stderr SHA·manifest SHA·stdout JSON도 대조했다. PNG SHA `bc50e4cb7a7956c88ccc887eff71c08aba7e23bd0b0927a422320feaa464345e`가 실제 PNG와 일치한다.
- [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/README.md:1), [VISUAL_REPORT §85](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1619), [CHANGED_FILES](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/CHANGED_FILES.md:1) — 결과표·선택면·단위·파일/줄 참조·실제 재현 명령이 현재 파일과 맞는다. CPU source 그림을 Gym 렌더/native 접촉·힘/cooked shape/해부학적 pad 인증으로 설명하지 않는다. 이번 후보 native 영상이 없음을 명시하고 원 실패 단계의 새 README도 첫 partial/exit1을 정상 네 후보 완료와 구별한다. 문서의 pending 표시는 이 독립 검수 이전 상태이며 본 기록이 최종 완료 근거다. [다음 catalog 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_CATALOG_PLAN.md:1)은 미실행이고 성공/실제 지지를 주장하지 않는다.

## 방법과 완료 범위

원 JSON·실행 metadata·producer/wrapper·문서를 읽고 입력/출력 SHA를 스트리밍 대조했다. 실제 PNG를 시각 검수하고 producer 두 개를 Python3.8 `compile`로 확인했다. Source pose·witness·교차 재계산은 `PYTHONDONTWRITEBYTECODE=1`, `MUJOCO_GL=disable`, `LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib`, BLAS/OMP 각1 thread로 정적 source model/FK query만 수행했다. 초기 library import 조건은 geometry 검사 전에 바로잡았으며 native scene·물리 step·후보 검색·producer 재생성은 호출하지 않았다.

최종 보존 감사/source_final/inventory/final_verification은 root의 별도 범위다. 본 담당자는 이번 단계에서 이 review.md만 생성했고 소비된 source·입력·출력·이전 봉인 파일을 수정하지 않았다. 이번 완료 판정은 source 후보 거절·후처리 정합성 검수이며 실제 접촉·후면 지지·지속 안정화 또는 연주 성공을 인증하지 않는다.
