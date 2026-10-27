# 오압현·누락·미달성 개선 v15

사용자가 세 개선의 구현을 승인했다. GPU 왼손만 변경하고 물리·제어·초기035/v14·달성 문턱·준비 구간 무감점·B 권고와 손가락 움직임 비용0을 유지한다.

1. [x] 변경 전 원문 보관, 음 길이·손가락 정규화와 최장 clean 기반 미달성 감점 구현 → 서로 다른 길이/손가락, 연속시간 경계 검사.
2. [x] 오압현 원인별 audible 기록과 원장 추가 → 실제 full-surface witness의 몸체/목표줄/프렛 범위/경계 모호성/다음 음 준비 여부 검사, 기존 판정 불변 확인.
3. [x] 관련 CPU 회귀·독립검수·계약/문서 갱신 → H32 유지/선택 reset/동일v15복원·v14거부와 과거 결과 보존 확인.

수식: b=M/(등장손가락수×그손가락음수), D=end−onset. 원시 wrong=−Σb·wrong_dt/D, missing=−0.5Σb·missing_dt/D, missed=−0.5Σ이번미달성·b·(1−min(best_clean_streak/required,1)). 기존 음수 단계 계수는 유지한다. best_clean_streak는 audible 연속 clean의 최고값이며 끊겨도 유지한다. 달성 기준·한 번 지급·left_missed 음 수 자체는 바꾸지 않는다.

오압현 판정은 기존 full thumb/finger2/3의 higher OR (!pad_positive AND (lower OR assignment))를 보존한다. 원인 몸체별 higher/lower/assignment가 실제 wrong에 기여한 audible 시간을 기록하고 source 프렛 범위와 경계 모호성·다음 음 준비 일치를 분리한다. '기하상 근거가 있는 방해'도 접촉 상대/실제 현 압력 인증은 아니다. 모호한 경우를 임의로 새 감점하거나 다음 음 준비를 무조건 면제하지 않는다. 진단은 겹칠 수 있지만 wrong/missing 감점은 원래 target 단위 한 번이다. bounded GPU 누적만 추가하고 매tick CPU복사/무한접촉로그를 만들지 않는다.

전체 보상v15, surface_frettingv7, ledger v6, 신규 wrong 진단v1. 관측544/event24/8/3331·기존표면관측v4 유지. 이전v14이하 strict resume거부, 동일v15전체계약만 복원한다. 이번 실제GPU/native물리·학습은 실행하지 않는다.

완료: 최종27모듈265검사·독립61검사PASS. source진단810bool/270프렛범위/27조합 독립대조,원판정AST/입력불변 확인. 450Python문법검사·보관464원문·이전v14봉인60·기존시각화68파일보존. 결과 docs/2026-10-23/guitar_learning_press_penalties_v1. 실제GPU/native물리/학습은미실행으로성능향상을주장하지않는다.
