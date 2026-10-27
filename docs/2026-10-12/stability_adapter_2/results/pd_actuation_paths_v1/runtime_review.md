# PD 구동 경로 정적 감사·산출물 독립 검수

2026-10-07. 새 감사 결과·경로도·문서·다음 제안을 검토했다. 기존 code_review/원자료를 수정하지 않았으며 native 초기화·step·source query를 수행하지 않았다.

## 요약

문제없음. Critical/미해결 Warning/Suggestion 없음. 105개 nominal 값과 이름의 정적 감사 및 그림 검수를 완료했다. API의 실제 적용 여부·actuator 동등성·기타 안정화 성공은 검증하지 않았다.

## 감사 결과와 재현

실제 audit_execution은 exit0/native0/step0이고 audit.json의6계약·101입력 SHA가 통과했다. 독립 순수 실행 출력과 실제 audit 전체 JSON이 exact였다. 사전 검수의 별도105 gain/cap 산식·Fret30 이름 literal·Strike30/Main66/Torso9 이름 대조 결과도 일치한다. 원본 환경이나 Gym을 수입하지 않는 AST 함수 실행 범위를 유지했다.

원본 POS/stiffness0/damping=kd 및 cap된 kp*(target−q)의 force-tensor 제출과 현재 POS/stiffness=kp의 position-target 제출을 구분했다. 설치 공식 tensors.html:384의 EFFORT 요구와 원본 코드의 정적 차이는 기록하되 실제 force 무시·원본 bug·PD 부족·포화로 판단하지 않는다. 원본 imported effort를 측정하지 않았고 nominal 숫자의 일치도 실제 actuator 동등성을 의미하지 않는다.

## 최종 미디어·문서

정적 경로도는 native renderer나 물리 측정 그림이 아니다. 105 nominal_rows의 다섯 그룹은30/30/6/9/30이며 kp/kd/cap 범위가 표·그림과 일치한다. Main66은 제어 이름 인터페이스이며 새 학습 action 차원의 결정이 아니다. 원본 기타 고정·하체 state 재주입을 현재 환경에 적용하지 않는다.

지원 CLI를 새 `/tmp/pd_paths_reviewer_plot_zuciwqyw`에서 실행해 exit0, canonical2610×1800 PNG의 byte/RGBA exact를 확인했다. 직접 이미지 QA에서 표·상자·화살표·범례·한계 문구가 읽히며 잘림/겹침이 없었다. Audit101 upstream·추가6 source/docs·audit/execution·현재 producer·PNG SHA가 모두 일치했다.

그림의 `(target,q)`를 PD 목표 구성 요소로 오해할 여지에 대한 Suggestion은 결과 README:23–24의 명시적 설명으로 해소했다. q는 실제 DOF 좌표이며 target과 별도의 입력이다. CHANGED_FILES:7의 누적 보고서 링크도 실제 VISUAL_REPORT:902로 수정됐다. 결과 표·한계·재현 경로와 PLAN:1010/adapter README:463의 정적 감사 범위가 일치한다.

## 승인 전 다음 제안과 동결

TENSOR_EFFORT_API_PROPOSAL.md는 사용자 확인 전·미구현/미실행이다. 별도1축 fixture의 POS/EFFORT ×0/±1Nm, 6fresh×24=144step 안으로 제한하고 main scene·gain·목표·LA를 바꾸지 않는다. EFFORT 양방향 응답을 positive control로 확인하고 다른 API/GPU로 자동 대체하지 않는 범위가 일관된다.

Descriptor 소유권 Warning은 제안:27–30에 `own_data=False`와 NumPy buffer/descriptor의 종료까지 유지 계약을 명시해 해소했다. 로컬 gymtorch.py:97–105의 구조와 일치한다. 기록 시점 Suggestion도 제안:36의 초기1개+완료24개 상태로 명확해졌다. 이 검수는 실행 승인이 아니며 새 구동·SO(3) torque 제어에는 별도 확인이 필요하다. 현재 runtime_review를 동결한다. 이후 완료 표시·보존 metadata는 root가 처리한다.
