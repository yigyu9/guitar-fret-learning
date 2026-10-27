# 현재 지지 자세의 가슴 접촉 확인

사용자 질문: 현재 오른쪽 겨드랑이 주변 지지에서 가슴도 기타에 접촉하는가?
기존 left_grip_release_cycle_v1/native_v2의3840 endpoint 기록에는 Chest/몸통 접촉 배열이 없다. R_Thorax 접촉0을 Chest 접촉0으로 대체해서 해석하지 않는다.

- [ ] 기존 config·초기 상태·자산·제어·16초 궤적을 그대로 재현한다. 자유 기타/스트랩OFF/Root·하체 고정/오른팔 유한 지지/오른손 타현OFF 조건을 유지한다.
- [ ] 읽기 전용 after_physics에 Torso·Spine·Chest·R_Thorax·R_Shoulder·R_Hip의 모든 기타 body 접촉을240Hz 기록한다. raw lambda 양수 여부를 분리하며 N 단위 힘이라고 설명하지 않는다.
- [ ] 신규 코드 문법과 독립 검수를 확인하고, 초기 값 및 실제 전체16초 영상은 새 경로에 보존한다.
- [ ] 이전 실제 trace와 새 trace를 비교하고 가슴/몸통 접촉 유무·시각을 보고한다. 이전 실행에 없던 접촉 로그를 소급 생성한 것으로 설명하지 않는다.

기존 결과/소스/봉인/계획은 수정하지 않는다. 구현은 새 run_chest_contact_cycle_v1.py, 결과는 /home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/에 남긴다. 완료 체크리스트는 결과 문서에 기록한다. 이번 작업은 자세/제어 변경이 아닌 접촉 관측을 보완하는 재현 실행이다.
