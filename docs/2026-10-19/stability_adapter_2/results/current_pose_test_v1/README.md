# 현재 자세 테스트 공간 점검

[실행과 키 안내](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md:1)를 따릅니다.

- 현재 실행: [open_v2.sh](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/open_v2.sh:1).
- V1: 원본 초기 상태/PD/질량 exact 확인 후 녹화 카메라 누락으로0step setup 실패. 입력·원본소스·초기 상태·로그 보존.
- V2: 0.2초/48physics/12controls 완료, native 초기 exact/입력 전후 동일/금지 호출0. 실제 물리 관측48행·목표12행·최종 제어48행이 기존 결과 prefix와 exact 동일.
- GUI 상태 로직: 시작 정지·한 단계·재생/정지·종료 후 진행 방지·R·Esc 요청 확인. 실제 DISPLAY 통합은 미검증.
- 기존 source/runtime/원본 자산 수정 없음. 별도 config/initial 복사. 기본 GUI 시험5초,2초 이후 기존 오른EW6 가상 피크 시험.

실제 점검 회차: [trial_000](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/sessions/20261014_215819_009632/trial_000/report.json:1). 세 영상은0.2초 점검용이며5초 시험 완료 영상으로 설명하지 않습니다.

독립검수 및 최종 보존 감사는 별도 파일에 실제 완료 여부를 남깁니다.
