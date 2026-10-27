# 프로젝트 현재 상태 — 2026-10-05

오디오→탭·운지→Fret·Strike→동기화→기타 안정화→전신 연주가 전체 흐름이다.
전체 설계는 [Master Plan](master_plan/README.md), 실행 환경은 [README](README.md)를 따른다.

## 현재 작업: StabilityAdapter 재구성

- 기존 StabilityAdapter 환경·학습 코드·설정·실험 산출물은 제거했다.
- 기존 checkpoint와 과거 관측·action·reward·curriculum 수치는 새 구현에 승계하지 않는다.
  다른 모듈의 공용 기타·humanoid·스트랩 자산은 유지했다.
- 새 `stability_adapter/`의 기본 환경·원본 스트랩·reset·약한 기타 노이즈·3초 WAIT를 구현했다.
  단일 환경 및 노이즈를 넣은 8개 환경 검증을 통과했다. 접근·그립·학습은 아직 미구현이다.
- 이전 실행 계획서는 폐기하고 사용자 합의에 기반한 새 환경·학습 기준으로 교체했다.
- 과거 계획·완료 기록은 현재 구현 기준이 아니다. 미정 수치는 검증 후 정한다.
- 다음 단계는 접점·왼쪽 제어 관절·접촉·오른손 감지의 구현과 검증이다.
- 제거한 전용 구현·산출물은 `/home/ajou/yigyu/stability_adapter_reset_backup_20261005/`에
  복구 가능한 형태로 옮겼다. 이 백업은 현재 프로젝트 실행에 사용하지 않는다.

핵심 문서:

- [StabilityAdapter 상태](docs/2026-10-12/README.md)
- [목표와 책임](master_plan/06_stability_adapter.md)
- [새 실행 계획](docs/2026-10-12/plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md)

## 다른 모듈

| 영역 | 문서 |
|---|---|
| 오디오·운지 | [Stage1](tab2fingermapping/README.md) |
| 왼손 압현 | [Fret](fret/README.md) |
| 오른손 타현 | [Strike](strike/README.md) |
| G0 계약·결합 | [Full 구현 상태](full/03_implementation/STATUS.md) |
