# 마스터 플랜 파트별 정합성 갱신

승인된 brief에 따라 마스터 플랜의 역할·현재 상태·검증 순서를 자유 기타 연구 방향에 맞췄다. 이번 작업은 문서 정합성 갱신이며 성능 완료나 새로운 물리 검증을 뜻하지 않는다. 원본 성능 확인 → 필요한 접촉 점검 → 자유 기타 단일 동작 → 제한 보정 학습 → 양손·곡 통합의 순서를 명시했다.

Source 420D/303D의 기존 관측 계약과 각 30D action, 105D named G0 계약을 보존했다. 66개 관절의 제어 권한과 학습 action 차원도 별개로 기술했다. 허용 범위 안의 기타 움직임을 인정하고, 초기 p/q 복귀·완전 정지·지속 손바닥 접촉을 연주 조건으로 두지 않는다. 기타 고정, 강제 부착, 지속 pose 덮어쓰기와 pose servo는 도입하지 않는다.

기존 `06_stability_adapter.md`와 `10_open_decisions.md`는 보존 대상이다. 현재 역할을 담은 `06_stability_adapter_2.md`와 현행 결정을 담은 `11_current_decisions.md`를 별도 문서로 추가하고 목차에서 연결했다. 세부 근거와 실제 경로·줄은 [변경 파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/master_parts_sync_v1/CHANGED_FILES.md:1)을 참조한다.

- [x] 각 파트의 계약·최신 연구 방향·현재 결과를 대조하고 입력 상태를 기록했다.
- [x] 00~05, 07~09의 역할·상태·검증 순서를 보완하고 기존 계약을 유지했다.
- [x] 06/10 원문 보존 경로와 현행 06/11 문서를 구분해 목차에 연결했다.
- [x] 기록된 문서 검증 107건 PASS를 확인했다. 이 검사는 문서 구조·링크·원문 보존을 대상으로 하며 물리 성능 검증이 아니다.
- [x] 별도 change-reviewer 검수와 root 최종 보존 감사 반영 — Critical/Warning 없음.

입력 기록상 기존 문서 10개를 갱신하고 신규 문서 2개를 추가했으며 보호 파일 31개를 보존 대상으로 추적했다. 이번 작업에서 물리 실행 0회, 학습 0회, 이미지·영상 생성 0회다. 원래 코드·자산·과거 실험 결과는 변경 범위가 아니다.

[검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/master_parts_sync_v1/review.md:1)과 [최종 문서 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/master_parts_sync_v1/final_verification.json:1)를 연결한다. 이전06/10과 실행 코드·자산은 보존했고 현행 문서 갱신만 완료했다. 다음 물리 소단계와 보정 학습은 아직 실행하지 않았다.
