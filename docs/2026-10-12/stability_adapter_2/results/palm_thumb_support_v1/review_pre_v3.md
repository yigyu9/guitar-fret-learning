# 손바닥·엄지 지지 v3 및 분석기 — 실행 전 독립 검수

요약 판정: **수정 권장**. v3 runner·wrapper·shell·leaf 계획에는 확인된 Critical/Warning이 없다. 아직 실행하지 않은 분석기에서 아래3개 보완을 권장한다. 검수자는 trial과 producer를 실행하지 않았다.

## Critical

없음.

## Warning

- [analyze_palm_thumb_support_v1.py:71](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_support_v1.py:71): 직접 읽는 각run의 `inputs_after.json`이 실행 전 `paths` SHA 목록에서 빠졌다. 세 파일을 목록에 포함한다.
- [analyze_palm_thumb_support_v1.py:97](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_support_v1.py:97): `(a,z]` bin은 t0 표본을 누락하고 upper edge+`where='post'` 그림은 계산 구간보다0.25초 뒤에 비율을 표시한다. before-step 시각의 `[a,z)`로300표본을 전부 포함하고 실제 bin 경계에 맞춰 stairs/step을 그린다.
- [analyze_palm_thumb_support_v1.py:113](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_support_v1.py:113): wrapper의 각run `inputs_unchanged`를 요약에 저장하지만 검사에 포함하지 않는다. 세 물리 실행의 입력 불변성도 필수 check로 확인한다.

## Suggestion

없음.

## v3 확인 사항

- [run_palm_thumb_support_v3.py:78](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v3.py:78)의 접촉 query는 기존 native 상태를 대상으로 목표 제출 후·다음 physics step 전에60Hz로 수행한다. 제출 직후 native 상태 불변 검사도 있다. 접촉 표본300개는1200개 모든물리step 접촉 증명과 구별해야 한다.
- 물리240Hz·실제 palm-up/유한 상태/고정 root와하체 검사240Hz·camera30Hz·제어60Hz를 유지한다. 이전 v2 대비 접촉 query 위치·빈도와 journal 접촉 묶음만 바꾼다.
- [palm_thumb_support_preserved_v3.py:56](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_preserved_v3.py:56)는 subprocess exit code와 finally 입력 SHA 대조를 남긴다. SIGSEGV partial을 정상 완료로 판정하지 않는다.
- [PALM_THUMB_SUPPORT_V3_PLAN.md:3](/home/ajou/yigyu/3/stability_adapter_2/PALM_THUMB_SUPPORT_V3_PLAN.md:3)은 두 이전 카메라 실패·표본 빈도 변경과 원인 미확정을 명시한다. 조회 빈도 변경만으로 camera crash 원인을 확정하지 않는다.
- 분석기의 실제 guitar main body pair 필터, 양의 raw lambda 비율, 초기 대비 actor-root 변위·shortest quaternion 회전, 기존 actor-root 위치 box 및 Fret gate의 세조건은 leaf 계획과 일치한다. raw lambda는 N/마찰 성공으로 변환하지 않는다.
- 비교 이미지의 native PNG를16:9 비율로 동일 resize하며0/2/5초 각 세조건을 같이 표시한다. 정상 완료151frame·1200step·300접촉 표본 검사 후에 결과를 사용해야 한다.

기존 review와 실행 기록은 보존했다. 분석기 보완과 실제 결과·산출물 대조는 후속 검수에서 확인한다.
