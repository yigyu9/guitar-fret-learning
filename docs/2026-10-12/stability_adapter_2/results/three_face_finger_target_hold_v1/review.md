# 독립 검수 — three_face_finger_target_hold_v1

2026-10-08. 신규 준비·분석·그림 producer와 이번 두 실행의 저장 원자료·PNG·문서를 검수했다. 기존 frozen runner는 읽기 전용으로 확인했다. 검수자는 native/Gym 초기화·physics·source replay를 실행하지 않았으며 이 파일만 작성했다.

## 요약 판정

문제없음. Critical 없음 / Warning 없음 / Suggestion 없음. README:10의 최대오차 일반화는 위치 악화·회전 최대오차 소폭 감소로 정정됐고, README:22–25 및 VISUAL §79의 R_Hip/빈 step 집합 표현도 정정됐다. 현재 미해소 finding은 없다. Root 최종 보존 감사와 source/inventory 봉인은 후속 작업이다.

## 직접 검증한 코드·원자료

- 입력·기존 예상 SHA 검증 및 시작/종료 봉인은 계산용 helper import 앞에 있다. 새 proposal을 전달하는 방식으로 기존 runner를 수정하지 않았다. 초기/제어 33/21/12/48/66 분담, native bounds·상대 offset±.3과 실패 부분기록 경계를 확인했다.
- 저장 half 초기값으로 목표 합성 함수를 AST 추출해 NumPy만으로 독립 계산했다. 실제 두 실행은 초기 full state·81q·속도·PD·기타 초기/목표·LA·route·solver가 동일했다. 손가락21 목표만 달랐고 팔12 및 다른48 목표는 유지됐다. Float64 상대 offset 합성 후 float32 제출81축 목표가 기대값과 exact였으며 숨은 clipping은 없었다.
- Native 실행은 새 2회·2400 steps다. 각 상태/trace/task1201개와 제어/접촉1200개, 60Hz 갱신300회·4-step 유지 및 root/하체9 body 구조 불변을 독립 대조했다. Fresh source/FK admission은 두 조건 모두 통과했고 저장된 최대 FK 위치오차는 0mm였다. Source 거리는 cooked clearance 인증이 아니다.
- 원시 기타 pose에서 world 위치오차와 SO(3) 회전오차를 재계산하고 첫0.1초·전체5초·마지막1초 구간 집계를 대조했다. 이전 trace의 경로 위치·속도로 수동 cable 법칙2400구간을 독립 재계산한 오차는0N이었다. 이는 법칙 scalar이며 native force 센서 인증이 아니다.
- Contact row를 다시 집계했다. Index 양λ 고유step23→33·마지막81→106, palm30→50·마지막123→123이었다. Palm 마지막 전체 contact step은132→130이다. R_Hip 양λ는 양쪽1200개 고유step, RH hand 접촉은0이었다. 마지막 관측과 연속 접촉·면별 지지·힘 단위를 구분했다.
- Saved-finger 반복의 states/trace/tasks/contacts/controls 다섯 파일과 hands/whole-body 영상 두 파일은 이전 half와 SHA byte-exact다. 재현 equality는 관측이며 성능 gate가 아니다. 현재 분석7계약과 입력10351개 SHA를 독립 확인했다.

## 미디어·문서

- 그림 producer는14개 명시 입력을 읽기 전에 봉인하고 종료 SHA를 대조한다. 현재 입력14개·출력2개, 성공 producer 사본·manifest·실행/log SHA 및 exit0/native_calls0를 직접 확인했다. 이번 그림 생성에는 실패 시도가 없다.
- 두 PNG를 직접 보았다. 0–5초 위치(mm)/회전(도) 곡선과 양 raw-lambda 고유 step/240초 표식·범례가 저장 자료와 맞다. 접촉이 없는 body는 빈 집합을 허용하며 관측값을 통과 gate로 요구하지 않는다. 2×2 hands의 실제 step0/1200 네 cell은 원 native PNG의 축소 crop과 pixel exact였다.
- Phase README·CHANGED_FILES와 main PLAN:1489·README:832, dated README:502·VISUAL §79:1458을 대조했다. 영상151frames/30fps/5.033333초와 실제 physics5초를 구분한다. 다음 THREE_FACE_SUPPORT_LOSS_DIAGNOSTIC_PLAN은 저장 자세·물성 읽기 진단의 미실행 계획이며 초기값/PD/LA·목표 변경이나 원인·성공 단정을 포함하지 않는다.

## 확인한 SHA

- `prepare_three_face_finger_hold.py`: `1e0b7303a5409915cc8861b47686e9350af4c0e1ac174ef320345d233df076e0`
- `analyze_three_face_finger_hold.py`: `e89a67874fdce129b5e1db0ebf3325afff40ca6fa35ba3c08118e899bbe2db3f`
- 재사용 runner: `4f8a99ac84e99079d9c720123a5a3bc77e465794fb48fcd23af97615d9eeabae`
- `analysis.json`: `f7b4559f08e9d578003744a6ec393628d44b46ad5ec37f9433dcac041ef9cd58`
- 그림 producer: `ec303f6be9c8b41c6c6dfde1f83091d9e8c3936b379c865e40c8d224d7380233`
- 그림 manifest: `8f10be3a3583867a6c11624fc8087eb6dca1489b956d62ce64dd62ccf3756d92`

## 최종 판정과 동결

Initial-finger 목표는 첫0.1초 p/q를 줄였지만 5초 최대 위치오차25.229274→26.111870mm와 종료 p/q21.912505mm/7.091529°→26.047250mm/7.714785°는 악화했다. 최대 회전오차는7.770624→7.724794°로 소폭 줄었다. 손가락 목표 변경은 채택 근거가 부족하며 손바닥·검지 지속 지지 소실이 남는다. 엄지 후면·손가락 전면·손바닥 옆면의 초기 source 접근과 named-body 접촉은 별개이며 실제 면별 지지·초기 기타 복원·연주 안정성은 인증되지 않았다. 검수 완료로 이 파일을 동결한다.
