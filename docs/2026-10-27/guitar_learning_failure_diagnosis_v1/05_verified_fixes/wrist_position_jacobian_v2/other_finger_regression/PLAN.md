# 손목 qpos-J v2 중지·약지·소지 회귀 준비

승인된 상위 PLAN 6단계의 실행 준비다. 검지 실행/분석은 root가 별도로 담당한다. 이 폴더만 작성하며 활성 소스·기존 teacher/reference·봉인·결과는 수정하지 않는다.

1. [x] 기존 jobs/validate/run_child와 원래 `-m` CLI로 12단계를 구성한다. 중지 row8, 약지 row16, 소지 row23을 유지한다. 각 fresh bootstrap 1update 뒤 **initial.pt만** reference/zero/random 각 4환경 첫 시도에 사용한다.
2. [x] CPU에서 현재 teacher/reference·전체 settings·v2 계약·새 입력핀·출력/symlink 거부·dry plan을 검사한다. 기존 38개 소스 회귀 검사를 다시 돌리지 않는다.
3. [x] 독립 준비 검수 PASS 후 preparation seal을 완성했다. root의 실행 인계 전에는 GPU를 실행하지 않고 대기한다.
4. [ ] root 실행 후 원래 판정/실패 포함 분모, 12 scene 종료·입력·설정·실제 fresh initial을 검증하고 별도 결과 검수를 받는다.

.5° cap, damping, 2초 ramp, 3초 onset, PD, native 범위, codec, 보상과 원곡 음 길이를 유지한다. 이전 checkpoint는 실행하지 않으며 새 동일 계약 strict loader를 그대로 사용한다. 고정 중지 또는 소지 zero의 압현 성공을 손가락 학습 성과로 해석하지 않는다. 전곡·자유 기타·일반적인 도달을 주장하지 않는다.

실행: root 인계 후 `python run_regression.py --execute`. 인자 없는 실행은 dry plan만 출력한다. 중지 입력은 원 support의 TEACHER/REFERENCE이며 약지·소지는 기존 other_finger_precheck_v3 JSON을 직접 참조한다. 새 teacher·checkpoint 변환·child wrapper·학습 설정 패치는 없다.

원 runner가 각 장면에서 source/config/model/optimizer/RNG strict 검증을 수행한다. orchestration seal은 매 child 전후 검사하며 child 자체 inputs_before/after 및 원 run_child의 실행 중 검사를 함께 사용한다. 12단계가 실제 종료하기 전에는 결과 완료를 주장하지 않는다.
