# 독립 검수 — three_face_initial_same_target_v1

2026-10-08. 이번 신규 준비·목표 합성·실행·분석 코드와 저장 원자료, PNG 두 장 및 최종 문서를 읽기 전용으로 검수했다. 검수자는 native 초기화·physics·source replay를 실행하지 않았고 이 검수 파일만 작성했다.

## 요약 판정

문제없음. Critical 없음 / Warning 없음 / Suggestion 없음. 아래 보완사항은 해소됐으며 현재 미해소 actionable finding은 없다. 원본 전체 보존 및 최종 snapshot/inventory 감사는 root의 후속 작업으로 구분한다.

## 직접 확인한 구현·원자료

- 준비 입력 closure와 예상 SHA를 검증한 뒤 계산하고 종료 시 다시 봉인한다. refinement closure의 종료 검증 누락, 분석의 metadata/raw 선읽기 및 원래 입력 SHA 검증 누락은 보완됐다. 카메라 두 view 구분과 실제 PNG SHA 대조도 추가됐다.
- 새 native 실행은 3회·3600 physics steps다. 각 상태/trace/task 1201개, 제어/접촉 1200개, 60Hz 갱신 300회와 4-step 유지, 초기 DOF 속도 0을 독립 대조했다. 왼쪽 33개 초기 좌표만 바뀌고 다른 48개 초기값은 그대로다.
- 저장 constant_0p016에서 절대 float32 81축 목표를 독립 재구성했다. float64 상대 offset 합성 후 float32 제출이 세 조건 모두 exact였고 native/C02 팔 범위·offset ±.3, 다른 48개 목표 유지·최종 66축 인터페이스를 확인했다. 상태/몸체 pose 덮어쓰기 없이 초기 관절좌표만 설정한다.
- 초기 기타 full state·PD·목표 p/q·절대 LA와 물리 설정을 대조하고 root/하체 구조가 모든 상태에서 그대로임을 확인했다. 절대 LA는 같지만 초기 자세 때문에 strap 경로와 장력은 같다고 요구하지 않는다. previous-state 경로 위치·속도로 수동 cable 법칙 3600구간을 독립 재계산한 오차는 0N이었다.
- 실제 기타 위치·SO(3) 회전 오차, palm-up proxy와 body별 접촉 집계를 재계산했다. 세 조건 모두 R_Hip 양 raw-lambda 고유 step 1200, RH 접촉 0이다. Half palm 마지막 양λ/전체 row step은 123/132, index는 81/83이며 thumb/middle 양λ는 step1200에도 있었다. 이 기록은 면별·연속 지지나 뉴턴 힘의 인증이 아니다.
- baseline states/trace/tasks/contacts 네 배열과 두 영상은 이전 기준과 exact다. controls는 새 81축 목표 기록·진단 필드 schema 때문에 false이며 물리 재현 관측과 구분했다. exact/성능 결과를 통과 gate로 강요하지 않는다. 분석 7계약과 현재 입력 9707개 SHA 일치를 확인했다.

## 미디어·문서 및 실패 보존

- 그림 producer의 19개 명시 입력은 읽기·렌더 전 봉인되고 종료 SHA가 같다. 현재 19개 입력과 두 출력 SHA, producer 사본·성공 실행 exit0 및 로그 SHA를 직접 대조했다. 그림은 저장 자료만 사용한다.
- PNG 두 장을 직접 보았다. 세 조건의 0–5초 p/q 곡선·단위·범례와 여섯 초기 source gap이 맞고, hands montage의 step0/1200 여섯 cell은 실제 native PNG의 축소 crop과 pixel exact였다. 영상 기록은 151 frames·30fps·5.033333초이며 실제 physics 구간 5초와 구분한다.
- Phase README:3–15, CHANGED_FILES의 실제 절대 경로/함수 줄, main PLAN:1466·README:821, dated README:497·VISUAL §78:1432를 대조했다. thumb/middle의 종료 관측을 연속 접촉으로 표현하지 않고 초기 source 거리·named-body 접촉·cooked/면별 지원을 구분한다.
- 직접 보간 및 투영 후보는 source-only 거절/native0이다. 최초 준비의 missing-key 실패 producer 사본 SHA와 로그를 확인했다. 첫 그림 시도도 Python3.8 `str.removeprefix` 오류/exit1/PNG 없음/native0이며 당시 exact producer·로그를 보존했다. 문자열 slicing 수정 후 성공한 현재 producer와 구분한다.
- 다음 THREE_FACE_FINGER_TARGET_HOLD_PLAN은 손가락21 목표만 분리하는 미실행 계획이다. 팔12 및 다른48 목표·물리조건 유지, 원인 단정·상태 덮어쓰기·성공 보장 없이 비교하도록 명시돼 있다.

## 확인한 최종 SHA

- `warmstart_targets.py`: `203b6d30e511a5e3df70301ba43118fda34eb5a9912c08e815dab31bb0be4356`
- `prepare_three_face_same_target_trials.py`: `6d390a76c51c317916c4250d61cf48d11a4fcc4d6bb6787117bfa1740e151255`
- `run_seed2_support_warmstart.py`: `4f8a99ac84e99079d9c720123a5a3bc77e465794fb48fcd23af97615d9eeabae`
- `analyze_seed2_support_warmstart.py`: `ad96ffc2254160d753fc7a97e7dcd7d98ceda0527a1c75203e62d73b3c0976f9`
- `analysis.json`: `2e33683bd86694bcaad30a2961f7707aa859ccb5085f2397ae3ba782307845dc`
- 그림 producer: `8f244d6c33cb4e8a296125fd9eb918e5f1210453562f500205e61e4f15e8fd83`
- 그림 manifest: `18f0dd309c43dcfdde4d97851c8b29a9e95174888b93ef7ad2f28b5c7733d50f`

## 최종 한계와 동결

Half의 초기 여섯 source gap≤3mm는 통과했지만 5초 최대 p/q는 25.229274mm/7.770624°로 baseline 25.280921mm/7.753357° 대비 위치만 아주 작게 줄고 회전은 늘었다. Quarter는 두 최대오차가 모두 커졌다. 손바닥·검지 지속 지지, 초기 기타 p/q 복원, 연주 안정성은 검증되지 않았으며 후보 채택 근거가 없다. Source 형상 거리와 palm-up proxy는 cooked clearance/해부학적 법선 인증이 아니다. 현재 검수 완료로 이 파일을 동결하며 root 최종 보존 감사 후 추가 append하지 않는다.
