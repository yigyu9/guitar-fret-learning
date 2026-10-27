# StabilityAdapter 구현 상태

2026-10-05 사용자 요청으로 이전 세대의 전용 코드·설정·테스트와 기존 학습·진단·영상
산출물을 프로젝트에서 제거했다. 이후 현재 `stability_adapter/`에 새 기본 환경·원본
스트랩·reset·초기 노이즈·3초 WAIT를 구현했다. 이 lean 경로의 접근·그립·학습 코드는 아직 없다.

별도 `stability_adapter_2/` 연구 경로에는 자유 기타·root/하체 고정·양팔 66관절 제어의
짧은 물리 진단, 소규모 기타 오차 feedback 비교와 물리 없는 정적 배치 도구가 있다.
2026-10-08에 물리 실험·학습을 일시 중단했으며, 아래 검토 문서와
[StabilityAdapter 2 세션 요약](stability_adapter_2/SESSION_WRAP_UP_2026-10-08.md)을
확인한다. 두 경로는 과제 정의·초기 자세·행동 차원이 달라 결과와 상수를 바로 승계할 수 없다.

단일 환경 16개 검사와 노이즈를 넣은 8개 환경 21개 검사, 스트랩 단위 테스트 7개를
통과했다. [실행 방법과 검증 범위](../../stability_adapter/README.md)를 확인한다.
무자막 영상은 [3초 WAIT](results/base_environment_v1/final/wait_full.mp4),
검증 기록은 [단일 환경](results/base_environment_v1/final/report.json)과
[8개 환경 및 부분 reset](results/base_environment_v1/noisy8_validation/report.json)에 있다.

## 현재 기준

- [환경과 학습 기준](plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md): 사용자와 합의한 새 설계
- [목표와 책임](../../master_plan/06_stability_adapter.md): 전체 시스템에서의 모듈 역할
- [접점 시각화](visualizations/grip_proposal/grip_proposal_multiview.png): 공용 모델의 정지 장면
- [기타 연구 전체 흐름 검토](guitar_research_review/README.md): 시작부터 전체 연주까지의 상태, 미흡점과 대안 비교

이전 실행 계획서는 폐기하고 같은 경로의 새 기준으로 교체했다. 기존 코드 정리·
세그폴트 수정 계획도 현재 계획에서 제거했다. 원문 3개는 복구용 백업의
`retired_plans/`에만 남겼으며 실행·구현 기준으로 사용하지 않는다.

`archive/plans/`, 이전 날짜의 StabilityAdapter 계획과 `docs/plans/stability_*`는
과거 이력으로만 남아 있다. 새 기준을 보충하거나 덮어쓰는 현재 계획이 아니다.
세그폴트 관련 버퍼 수명·인덱스·장기 안정성 검사는 새 기준의 검증 항목에 반영했다.

## 이전 구현 제거와 복구

- 2026-10-05 이전 세대의 `stability_adapter/` 전용 환경·학습 구현과 관련 산출물을 제거했다.
- 현재 `stability_adapter/`는 새 계획에 맞춘 별도 기본 환경이다. 이전 세대 코드를 복원해 사용하지 않는다.
- 2026-10-06 이후의 `stability_adapter_2/`와 `docs/2026-10-12/stability_adapter_2/` 결과는 별도 실험 경로로 남아 있으며 위 제거 범위에 포함되지 않는다.
- 공용 기타·humanoid·스트랩 자산과 다른 모듈·무관한 곡 영상은 유지했다.

제거한 파일은 `/home/ajou/yigyu/stability_adapter_reset_backup_20261005/`에 원래 상대
경로를 유지해 옮겼다. 영구 삭제하지 않았으며 이 백업에서 복구할 수 있다.
