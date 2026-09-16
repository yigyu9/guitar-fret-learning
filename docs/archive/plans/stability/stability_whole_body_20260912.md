> **HISTORICAL — 통합 이전 기록.** 본문의 수치·명령·검증 결과는 작성 당시 기준이다. [현재 StabilityAdapter 안내](../../../../stability_adapter/README.md)를 먼저 읽는다. 보관은 미완료 검증의 완료를 뜻하지 않는다.

# 독립 StabilityAdapter 전신 제어 확장

사용자가 97축(손가락·손목·목·머리 포함)을 선택했다. 골반/root 고정과 수동 스트랩,
낙하→정착→목표 복원 lifecycle은 유지한다. 이 선택을 구현 범위 승인으로 적용한다.

- [x] 105개 named 축 중 zero-range 8개를 제외한 97개 제어 범위 확인
- [x] 독립 action 97D / observation 317D 계약·물리 task·checkpoint v2 반영
- [x] 관절별 cap 적용 및 Full bridge의 기존 43축 권한 유지
- [x] CPU 계약·실제 GPU 전신 target·PPO 업데이트 검증
- [x] 변경 검수 및 현재 문서·검증 이력 갱신

성공 기준: RECOVER에서 하체·손목·손가락·목·머리까지 유효한 제한 내 PD target을
정책이 변경한다. WAIT는 전체 초기 hold를 유지한다. root와 zero-range 8축은 고정된다.
Full bridge는 같은 97축 proposal을 받되 canonical Full43과 외부 authority의 교집합만
허용해 Fret/Strike의 손목·손가락 및 시선 관절을 보존한다. 정책 수렴은 별도 평가한다.

이전 27D/107D checkpoint를 자동 확장하지 않는다. 현재 97D/317D 독립 actor 역시
source 관측이 없으므로 연주 결합에는 별도 관측·정책 학습과 검증이 필요하다.

검증 결과: CPU adapter14·bridge10·evaluation3 및 Full/checkpoint/dispatch 회귀 통과.
GPU 두 환경에서 90 frame 정착, 97개 목표 및 전신 그룹 움직임, root/8축 고정 확인.
48 rollout에서 12,288 transition, 6,155 정책 표본, 46회 업데이트와 v2 checkpoint 저장.
평가 1 episode는 6.528 cm / 8.769도로 recovery timeout. 제어 구조 구현 완료,
복원 수렴 미검증. 별도 change-reviewer 검수 통과. 자세한 근거는
[NEW-003](../../../../stability_adapter/archive/VALIDATION_20260912_14.md)을 따른다.
