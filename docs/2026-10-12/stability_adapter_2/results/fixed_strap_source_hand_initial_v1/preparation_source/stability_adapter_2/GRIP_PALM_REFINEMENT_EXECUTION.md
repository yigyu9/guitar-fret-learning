# seed2 국소 source 탐색의 실행 단위

MULTI_FACE_GRIP_PALM_REFINEMENT_PLAN을 유지하며 다음 세부 계산을 먼저 기록한다.
기존 multi_face_grip_v3 코드·원자료는 변경하지 않는다.

1. seed2 실제 t0의 전체 hull–유한 면 QP witness를 손 body local로 변환한다.
   같은 점을 작은 FK 변경에 따라 이동시키고 면 바깥0.3mm를 선호하는 least-squares를 계산한다.
   witness는 최적화 동안 고정된 국소 근사이며 해부학적 pad나 실제 접촉점 인증이 아니다.
   palm 위치 가중1/2, palm 법선 평행성 약한 선호, 위쪽 반구와 작은 각도 보정을 함께 둔다.
2. 각 fit에서 alpha1/.5/.25/.125로 보정해 8개의 고유 source 후보를 기록한다.
   팔±.03/손가락±.10와 baseline팔±.3/native한계를 함께 적용한다.
   후보마다 전체 hull–유한 면 QP와 사람–기타/양손/비인접왼손 LP 교차 검사를 다시 한다.
3. source 교차가 없고 palm-up>0이며 seed2보다 전체면 최대 gap과 palm gap이 모두
   작아진 후보 중 최대2개만 실제Gym t0 검사 후 각각5초 실행한다.
   후보 선택 전에 raw 수치와 선택 근거를 기록한다. 접촉면 인증·안정화 성공과 구별한다.

새 source 결과는 docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1,
trial은 stability_adapter_2/trials/grip_palm_refinement_v1에 저장한다.
실제Gym에서는 기존 held-target/LA/PD/기타 초기p,q/root하체고정/양쪽66 연결을 유지한다.
기타 p/q feedback·학습은 이 초기 자세 탐색이 끝난 뒤 별도로 설계·검증한다.
