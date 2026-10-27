# POSITION geometry PI 사전 검수

요약 판정: 문제없음 — 사전 검수 PASS. Critical 없음 / Warning 없음 / Suggestion 없음. 신규 native 실행·연주 반응 및 PREPARE prefix 동일성은 아직 이 판정에 포함하지 않는다.

- `run_strike_position_geometry_pi.py:197,205`: 원 POSITION rebase 대비 PI preview와 최종 제출 두 기준이 모두 actual R9 좌표+P/I 보정으로 변경됐다. Phase0/열린 phase1에서 policy R9는 기록만 하며 학습 finger21 목표는 유지한다. Native bounds/rate clipping·I rollback에 동일한 base를 적용한다.
- Diff상 그 외 변경은 제어권 metadata다. 기존 POSITION stiffness, source phase1 damping1/4·phase0/2 baseline, PREPARE/L12 hold, 닫힌 창 actual IK와 RECOVER previous goal+2δ, source clock/detector/history/성공 기준은 그대로다. 명시적 인간 EFFORT tensor나 body force 호출은 추가하지 않았다. 자유 기타·스트랩 OFF·root/하체 고정·other targets 범위를 유지한다.
- 수정된 EFFORT geometry PI의 해당 PI else-block과 AST가 exact임을 확인했다. Native/helper import 없이 추출된 현재 block을 세 사례에서 실행해 policy만 +0.8↔−0.8로 변경할 때 desired/I/blocked/raw_goal이 모두 불변임을 독립 확인했다. 두 새 Python 파일 AST Python3.8 문법도 통과했다.
- Wrapper는 실제 runner module 선택만 변경했고 기존 사전 입력 SHA·source_before·종료 재검사·argv 복구를 유지한다. 기존 소비된 runner·결과를 수정하지 않았다. 목표 논리를 EFFORT와 같게 만든 비교이지 서로 다른 물리 궤적에서 같은 목표가 나온다고 보장하지 않는다.

확인 SHA256: runner `8460d1eb19cb40f9310637f1e45760e25df16ac53035b118207ce0f7cd197349`, wrapper `addc98f53cea33329be953f89a7264464109f7a3f386dcbf65c0213c0b25bf22`, 계획 `301406a27d92259011481ac5c5d8222f9a21cc502229a23ae20bff37639091f3`.

검수는 변경 소스·AST·순수 NumPy 회귀·SHA 범위이며 Gym import/native 초기화/physics 실행은 0회다. Actor 전체30 actuation 동등성·원 source hybrid/GPU 동등성·지속 지지·기타 안정성·완성 연주는 인증하지 않는다. 실제 제출/상태·초기 prefix·영상·입력 보존 및 실패 자료는 실행 후 별도 검수한다. 이 사전 검수는 동결한다.
