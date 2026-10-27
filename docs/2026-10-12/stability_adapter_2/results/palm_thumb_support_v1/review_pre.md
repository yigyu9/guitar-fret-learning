# 손바닥·엄지 지지 v1 — 실행 전 독립 검수

요약 판정: **문제없음**. 정적 검수이며 search/native 실행은 검수자가 하지 않았다. 최초 지적과 nonfinite 실패 원자료 저장 경로의 수정 확인을 마쳤다. 물리적 지지 성공은 실제 결과로 별도 판정한다.

## Critical

현재 확인된 항목 없음. 최초 controller 목표 한계 anti-windup 누락과 두 왼팔 적분기 경쟁은 root에게 전달했고, 실행 전 작업본에서 수정된 것을 확인했다. `palm_thumb_support_v1.py:61`의 unclipped `raw`–최종 목표 차이를 사용하는 판정과 blocked 후 목표 재계산, `run_palm_thumb_support_v1.py:59`의 ON 왼팔 hold PI 비활성화가 해당 수정이다.

## Warning

없음.

## Suggestion

없음.

## 해결 확인

- 초기 실제값을 gate 이전에 저장한다(`run_palm_thumb_support_v1.py:30`, gate는36).
- 각240Hz step의 실제 손바닥 법선을 검사하고 위쪽 반구 이탈은 실패로 종료한다(86–89).
- 실패 상태를 `failure_state.json`에 저장하고 마지막 partial frame을 추가한다(102–109).
- nonfinite 실패 상태와 trace는 NaN/Infinity를 명시 문자열로 변환해 `allow_nan=False` 원자료 저장에서 다시 실패하지 않도록 한다(105,110).
- 사용되지 않던 신규 `self.arm`은 제거됐다.

## 확인한 범위와 검증 한계

- 신규 source search/controller/native runner/preservation wrapper/shell 5개와 leaf 계획, 직접 재사용 helper를 읽었다. 기존 git 작업 트리의 다른 변경은 이번 검수 범위에서 제외했다.
- source 형상과 native 물리 접촉을 분리하며, fresh native 초기 audit의 전체 source 겹침·palm-up·기타 초기 p/q·81관절 검사로 동적 시험을 gate한다.
- 하나의81 PD 목표만 제출하고 시작 후 상태 쓰기·외력/effort 경로를 사용하지 않는다. native upper/lower·목표 slew 검사와 고정 root/하체·다른 목표 유지 검사가 있다.
- 정상 완료 경로는1200 physics step, 각 step 접촉 query, t0 포함151 native COLOR frame으로0~5초를 덮는다. raw lambda를 N으로 환산하지 않는다.
- preservation wrapper는 import 전에 소스·계획·자산·입력을 SHA로 기록하고 실행 후 대조한다. 이번 검수는 동적 성공·접촉 여부·보존 실제 결과를 보증하지 않는다.
- `--mode fret`은 아직 구현되지 않은 후속 모듈을 가리킨다. 이번 실행 범위는 search/settle이며 Fret 단계가 만들어지기 전 실행하지 않는다.
- search wrapper의 보수적 전체 소스 복사에는 이후 수정 전 runner도 들어 있다. search는 해당 runner를 실행/import하지 않으며, native가 실제 소비하는 runner 버전은 native의 `source_before`·입력 SHA를 기준으로 확인한다. search 단계 입력 불변성과 단계 사이의 작업본 수정은 구분한다.

실제 trial과 산출물이 준비된 후 최종 검수를 별도로 기록한다.
