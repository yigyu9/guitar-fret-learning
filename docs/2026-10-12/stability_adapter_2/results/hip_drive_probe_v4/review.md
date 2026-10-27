# 독립 hip fixture·추가 damping-zero 진단 검수

2026-10-06. 별도 change-reviewer 최종 판정: 남은 Critical/Warning/Suggestion 없음.

- 원본 L_Hip에서 추출한 4개 fixture XML bytes/SHA·관절 정의 대조.
- 24 native case 재실행의 모든 반환 field·trace exact 일치, v3/v4 trace/contacts exact 일치.
- 고정 root·초기 q/velocity·POS target·gain/drive readback·무접촉·zero-gravity 확인.
- velocity-target getter는 종료 시점, gravity는 초기화 후 getter로 구별. 초기 velocity-target 캐시가 검증됐다고 주장하지 않음.
- 실제 H0의 TGS/PGS damping-zero 두 조건 전체 trace/states/contacts exact 재현.
- 실제 lower damping0와 solver readback, 초기 전신 상태·root·기타 목표·L_A·kp/cap·하체 외 kd 보존 확인.
- comparison SHA와 최대 위치/회전·raw 하체 목표 편차·scalar limit 지표 대조.
- hip09·기존14조건·새2조건 PNG를 임시 경로에 재생성해 원본과 픽셀 일치; 원본 JSON·PNG 보존.
- 표시된 각도는 실제 DOF 측정값. EFFORT trace의 torque 필드만 제출명령이며 실제 torque 계측으로 해석하지 않음.
- fixture/실제 trial 모두 성공 또는 새로운 기본 설정으로 채택하지 않음. +5mm 실제 Z 변경은 확인 대기 중.

native 포함 15 tests 통과, 보호 파일87 size/mtime 및 과거49 SHA 불변 검증도 저장했다.
전체 목표(자유 기타 유지·오차 보정·작은 손/팔 움직임)는 아직 미완료다.
[변경 파일·실제 줄 번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/CHANGED_FILES.md:1).
