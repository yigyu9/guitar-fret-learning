# 原본 대비 strap −4mm 실행 단위

기존 BODY9_STRAP_MINUS4MM_PLAN.md의 한 시험을 수행한다. 원본 LA에서0.004m만
줄인1.0978469719600776m를 사용한다. 이전 −2mm/원본 humanoid81/G 초기값,
몸통9 PD×2, 다른72 PD, 손목 목표 파형, 물리·self-collision 조건은 유지한다.

- [ ] frozen 준비 코드·native runner SHA 대조 후 새 준비 코드/입력 생성.
- [ ] 새 source admission과 실제 한5초/1200step·스트랩 포함 두 영상.
- [ ] original/−2/−4의 초기/후기 G 오차·실제 손목 진폭·장력/접촉 비교.
- [ ] 원자료·producer·로그 보존, 그림 확인, 변경 줄과 누적 결과 기록.

새 코드는 prepare_body9_strap_minus4mm_trial.py와 analyze_body9_strap_minus4mm.py다.
기존 frozen prepare/analyzer/runner는 수정하지 않는다. 무학습 작은 손목 파형 비교이며
fret·strike actor나 residual 학습을 실행하지 않는다. 전체66권한과 이후 초기p/q 복원
목적을 유지한다. 초기pose/LA 수정과 이후 실제 관절 목표 보정 역할을 혼동하지 않는다.

원본/−2mm를 같이 비교하고 최대 장력 증가 및 지지 contact 소실도 기록한다.
Source proxy admission은 PhysX cooked penetration 인증이 아니다. 원래 source grip
조건 미충족도 그대로 남긴다. 실측 이전 성공 임계값이나 다음 길이를 확정하지 않는다.
