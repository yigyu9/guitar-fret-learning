# 남겨 둔 최종 근거

| 자료 | 용도 |
|---|---|
| [손바닥 아래접근 런타임 검사](palm_underhand_runtime.json) | 손바닥 중심·방향 기준과 0.15초 단계 전환의 2환경 실제 GPU 확인 |
| [이전 팔꿈치 기준 종료 trace](underhand_termination_probe.json) | 손바닥 기준 전 1환경·10초 기록. 현재 판정 근거로 사용하지 않는 비교 자료 |
| [종료 원인 수명주기 검사](stability_termination_runtime.json) | GPU 환경의 `failure_palm_down` 종료·에피소드 기록 확인 |
| [이전 아래그립 미팅 검증](underhand_meeting_validation.json) | 구 팔꿈치 기준 8.13초와 스트랩 보정의 과거 비교 자료 |
| [스트랩 조기 종료 제거 검증](strap_no_stop_validation.json) | CPU67·GPU3, 힘 보존·지속 한계 초과·정상 시간 제한·낙하/수치 종료 |
| [검증 요약](pinch_curriculum/validation_summary.json) | 진단 제어와 PPO 결과, 학습·재개·전환 검증 |
| [최종1024환경 집기 진단](pinch_curriculum/pinch_grasp_final_contact_1024.json) | 진단 제어기1024성공·물리 실패0의 환경별 원본 |
| [개선 전1024환경 대조](pinch_curriculum/pinch_scale_chairfix_1024.json) | 의자 mask 수정만으로는 실패108건이 남은 대조 |
| [PPO 정책 평가](pinch_curriculum/pinch_curriculum_grasp_eval.json) | 24iteration 정책은8회 평가에서 집기 성공0 |
| [CPU 검사](pinch_curriculum/pinch_curriculum_final_cpu.log) | 67개 회귀 통과 |
| [현재 통합 구현 지문](pinch_curriculum/implementation_manifest.json) | 단일 환경 코드·설정·검증 산출물의 현재 해시 |
| [기준 자세 fixture](support_hold_reference_s0_smoke_clamped.json) | 기존 테스트에서 직접 읽으므로 유지 |
| [파라미터 근거](calibration_reference_v4.json) | parameter_provenance.json이 가리키는 출처 |

중간 후보·대용량 trace·중복 로그·이전 영상·소스 스냅샷은 [압축 보관](../archive/README.md)으로 통합했다.
원래 training/runs의 학습 로그·checkpoint와 실행 코드는 변경하지 않았다.
