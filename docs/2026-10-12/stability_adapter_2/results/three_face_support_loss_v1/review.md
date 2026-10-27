# 독립 검수 — three_face_support_loss_v1

2026-10-08. 신규 shape readback runner·저장 자세 분석기, 이번 원자료와 최종 v3 그림·문서를 검수했다. 검수자는 native/Gym 초기화·physics·source replay를 실행하지 않았으며 저장 배열의 NumPy/SciPy 수학만 독립 대조했다. 이 검수 파일 외 변경은 없다.

## 요약 판정

문제없음. Critical 없음 / Warning 없음 / Suggestion 없음. 미해소 actionable finding은 없다. 원본 전체 보존·최종 source/inventory 봉인 감사는 root의 후속 작업이다.

## 코드·원자료 검증 범위

- 원본 runner, 직전 frozen snapshot 및 새 source_reference 사본 SHA가 exact였다. 새 runner는 t0 capture 직후 human/guitar의 body shape IndexRange와 SDK RigidShapeProperties 9개 필드를 읽는다. 각 shape가 1회 매핑되고 human55/guitar28 shape·필드값 finite를 확인했다. 조회 전후 native state·PD·Python 제출목표 불변을 기록하며 native target getter roundtrip으로 확대하지 않는다. Shape setter·새 상태 덮어쓰기는 없다.
- 새 native 실행은 1회·1200 steps다. 초기 full state·81q·절대81목표·PD·기타·LA·route·solver가 이전 saved-target와 같다. 각 상태/trace/task1201개·제어/접촉1200개, 300갱신·4-step 유지와 제출목표를 대조했다. 다섯 원자료 파일과 두 영상 SHA는 이전과 byte-exact였으며 성능 gate가 아닌 재현 관측이다.
- 이전 trace의 route 위치·속도로 수동 cable 법칙1200구간을 독립 재계산한 오차는0N이었다. 영상은 실제 Gym151frames/30fps/1280×720/5.033333초이며 물리 구간5초와 구분한다. 초기 및 런타임 state/PD/목표 검사의 범위와 root/하체 고정 조건은 기존 실행에서 유지된다.
- 분석7계약·입력10675개 SHA current를 확인했다. 두 이전 조건의 실제 저장 body/G pose12개×손 부위6개의 G-local geometry를 rigid transform으로 독립 대조한 최대 vertex 오차는2.36e−16m였다. Facet point와 normal dot 오차0, witness distance 오차9.15e−18m였으며 hull/유한 patch feasibility와 convex QP stationarity를 수치 확인했다. 새 geometry/source 실행 없이 저장 결과와 좌표 수학을 검증했다.
- Coordinate error는 각 sample의 실제 native scalar q에서 t0의 계획된 첫 목표 또는 이후 직전 제출된 control 목표를 뺀 값이다. Left Shoulder_x .2884451598rad는 첫 setter 전 의도한 목표 불일치를 포함하고, 종료 .3789434731/.3792854100rad는 실제 로그 목표 대비다. 전체 관절 SO(3), drive 포화 또는 접촉 소실 원인으로 해석할 수 없다.
- SDK shape friction은 양 actor 모두1.0이다. Raw contact friction 필드와 재료 계수를 혼동하지 않는다. Contact/rest offset·filter 및 Flex-only thickness를 raw readback으로 보존하며 cooked 형상·면별 접촉을 증명하지 않는다.

## 최종 미디어·문서와 보존 이력

- v3 producer의10679개 입력 pre/post/current SHA와 출력2개·실행/log/manifest·정확한 실행 source 사본을 직접 확인했다. 성공 실행은 exit0/11.23134584305808초/native_calls0이다. 분석 결과 True를 강요하는 성능 관측 gate는 없다.
- PNG 두 장을 직접 보았다. 여섯 범주형 표본0/.1/.25/.5/1/5초의 mm·degree·무차원 dot 표기와 G-local mm의 step0/120/1200 source geometry2×3가 맞다. 공통 축 범위·비율·시점을 사용하고 legend/라벨 겹침은 해소됐다. Source 도식은 실제 Gym 카메라 영상과 구분한다.
- v1은 font-family lookup 실패/exit1/PNG0/native0이며 exact producer·로그·실행 metadata를 보존했다. v2는 성공/exit0/11.918461초 후 geometry layout QA에서 제외됐고 exact producer·manifest·PNG2개·로그를 보존했다. v3의 변경은 brief 경로와 geometry layout이며 metrics PNG는 v2/v3 byte-exact였다.
- Phase README·CHANGED_FILES 및 main PLAN:1502·README:839, dated README:507·VISUAL §80:1500의 수치·실제 파일/함수 링크와 원시/기하/영상 구분을 확인했다. 다음 THREE_FACE_ARM_INITIAL_TARGET_PLAN은 초기q/gain/material/LA를 유지하며 팔12 목표만 초기각에 맞추는 두 finger 조건의 미실행 진단이다. 그 결과나 접촉 원인을 미리 확정하지 않는다.

## 확인한 최종 SHA

- Readback runner: `ca467248e9dbbce8d8967cfa5d8cf3893d58b8b9a0821c4d4840aac61febba60`
- Analyzer: `2a7e2fa9d5b7ba0a99c35bb237abb72a9fb660f445ea1f04a6c7baab7b9c77e1`
- `analysis.json`: `c7d14a89d7eb420eb5b4a0d7d64c47b35fffb42617c457144ce032b43dda9daf`
- v3 producer: `539308ba005250e8d12a1e9732e80b11df11ea7d7871bf2441f480cfda268603`
- v3 manifest: `8ac37ad5770f11691af998d4b4a1e6d9e4be157e37a6a34a14d268a180e3ee5c`

## 최종 한계와 동결

Palm source gap2.129621→9.894188/5.392989mm와 선택 facet alignment .994174→.979404/.978361은 근평행만으로 위치 근접이 유지되지 않는 관측이다. Thumb 지정 facet dot 초기−.816388도 해부학적 pad 정체성을 증명하지 않는다. Source hull–유한 면 거리와 named-body/raw-lambda 접촉은 별개이며 엄지 후면·다른 손가락 전면·손바닥 옆면의 실제 지속 지지, cooked clearance, 기타 초기 p/q 복원 및 연주 안정성은 인증되지 않았다. 현재 검수 완료로 이 파일을 동결한다.
