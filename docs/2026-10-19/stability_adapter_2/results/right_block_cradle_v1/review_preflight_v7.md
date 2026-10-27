# 사전 검수 — 몸통9과 양팔24 유한 EFFORT 제어

요약 판정: **코드 문제없음. Critical 0 / Warning 3 / Suggestion 0.** 지정 static_body9_effort 설정의 초기 필수 검증 후 bounded5초 진단을 막는 제어/계약 오류는 발견하지 않았다. 작성 시 실행은 시작됐으며 실제 결과는 아직 검수하지 않았다.

- factory는 left_near_arm_effort_v2의 원 factory를 호출하므로 process patch한 left_near3 factory와 재귀하지 않는다. guard class도 패치되지 않은 기존 class에서 상속한다. GraphicsGym/초기 setter/StrapForceGuard 계층을 유지하고 body9+right12+left12의33개 열만 human81 effort에 허용한다.48 POSITION getter exact와 전체 state 불변·단일 target 제출/4physics를 새 factory에서 검사한다.
- construction은 기존 arm mode 설정 뒤 body9만 EFFORT/0 stiffness/0 damping으로 바꾼다. 새 reference도 해당9행의 mode/두 gain만 변경됐으며 다른72행·기존 다른 필드는 exact, 모델 effort300도 유지한다. 같은 candidate/SHA/기타 초기값이다. runner5의 expected PD와 실제 property 기록은 선언된 변경과 맞는다. reference의 과거 native state는 현재 측정이 아니다.
- body controller는 기존 currentG 두점/왼 wrist 제어를 한 번 계산한 뒤 `gravity + 600*(target−q) − 60*qdot + 두점 Jᵀ(body9)`를 몸통9에 합산·native cap으로 clip한다. body9와 arm24는 다른 열이므로 같은 generalized torque를 중복 적용하지 않는다. 중력은 `−ΣJ_COMᵀ*m*g`이며 COM/origin 변환을 이전 actor Jacobian frame에 맞춘다. 기타 직접 힘·부착·pose setter는 추가하지 않는다.
- 최신 helper는 body9 gravity COM-J z열을 기록하여 mass×9.81 합을 후처리에서 재계산할 수 있다. native 전체 q/qdot finite와50rad/s 초과를 각 물리 제출 직전에 검사한다. 부모 controller 계산 뒤에도 실제 물리 적분은 아직 없으므로 위험 상태에서 다음 torque 제출/physics로 진행하지 않는다.
- body_effort_rows에 body9의 요청/중력/PD/task/제출 전후81을 저장하고 tracking actualfinal을 최종 body 합산값으로 갱신한다. controller가 반환한 한 벡터만 기존 actor effort API로 제출한다. helper/runner AST 통과 및 현재 실행 attempt의 helper/계획 SHA와 파일 일치도 확인했다.
- 분석기3의 새 body9 branch는33 owner/48 readback·BODY9 PD/중력/task/clip과 최종 vector를 처리한다. 이전 분석기2의 J*qdot 검증 범위·최대 요청 필드명·raw projection과 clamped endpoint 구분 보완도 코드에서 확인했다. 실제 분석기3 실행/결과는 미검토다.

Warning 1 — 부모 position_command_rows 헤더는 아직 POSITION57/bilateral24라는 legacy 문구를 저장한다. 실제 새 행은 position48_exact이고 현재 제어는33EFFORT/48POSITION이다. body_effort_rows 및 갱신 tracking이 실제 최종 명령이며 two_block_rows.final은 body9 추가 전이다. root가 새 scope 정정 기록/최종 문서에서 이 구분을 명시하기로 했다. 원본 로그를 덮어쓰지 않는다.

Warning 2 — body native POSITION을 explicit600/60+gravity/task로 바꾸는 비교는 중력만의 효과나 implicit PD와 동일 동역학의 인증이 아니다. 유한300Nm cap과 실제 q 오차/접촉·기타 변화로 판단해야 한다. 계획의 실행 전 정정대로 양팔24는 오른12+왼12다. 같은 초기값이나5초 완주만으로 두블록/무왼손 지지 성공을 선언하지 않는다.

Warning 3 — 저장된 Jacobian coefficients의 후처리 중력 산술 검증은 전체 native Jacobian/질량 모델을 독립 인증하는 것은 아니다. prior 오른 점 velocity guard와 current 두점/왼 wrist frame 검증의 범위를 유지한다. 각10N 가상 point 요청과 실제 접촉힘·힘 분담은 다른 양이며 왼thumb/허벅지 관여 및 제한된 scalar elbow 시험을 별도로 평가해야 한다.

검수 범위는 새 helper/runner/계획·config/reference 전체 비교·최신 guard/기록 보완·분석기3 diff·AST/attempt SHA다. reviewer의 추가 native/학습/추론·다른 담당 파일 수정은0이다.

검수 SHA256:

- 계획V5: `bac39b7b4806448eb407d16d0fcc52214c5c7ca648c4263605f07052afc121af`
- body helper1: `7934a42ec030983409e6126f10d779fa20746c85ddcd7fe277f8e1e6fe04d194`
- runner5: `2aa94ba5dba4e53f12823f55fd3697d98ad75ef02a87225eb840efcadd707fd5`
- config: `d491d81b9222a2fd33028078dab170571b7ef7cd233448181779335fcdb3cbab`
- reference: `df57032845257ff3adba10ce252bb36cabd499f2203bbbbeebeb7887b0485158`
- 분석기3: `3bdc63ffe9b1000830b3ae07c269ff0d4edf69233c868f1486867f795fe57e66`
