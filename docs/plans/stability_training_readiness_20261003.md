# Stability Adapter 학습 준비 점검

## 목표

- `rl38`에서 pytest를 실행할 수 있게 한다.
- 현재 코드의 회귀 테스트를 실행한다.
- 최소 학습 smoke를 시도하고, 실행 환경 오류와 학습 구조 문제를 분리한다.
- 본 학습 전에 필요한 개선사항을 정리한다.

## 점검 결과

- [x] `rl38`에 pytest 설치: `pytest 8.3.5`
- [x] `stability_adapter/tests`: 166 passed
- [x] gymtorch 빌드 의존성 확인: `ninja 1.13.0`
- [x] 8환경·2 update 학습 smoke 시도
- [x] 최초 smoke 중단 원인 확인: `torch.cuda.is_available() == False`, NVIDIA 장치 미노출
- [x] 기존 학습 로그의 단계별 샘플 분포 확인
- [x] NVIDIA 장치 파일 복구 후 PyTorch CUDA 인식 확인: RTX 4070 Ti, driver 580.178.04
- [x] 복구 후 8환경·10 update smoke 완료 및 독립 평가/영상 생성

## 현재 판단

테스트와 코드 연결은 통과했고, NVIDIA 장치 파일을 복구한 권한 세션에서는 학습 루프가 정상 실행되었다. 복구 후 smoke는 10 update/5,120 sample을 처리했으며 segmentation fault 없이 checkpoint·평가·영상을 남겼다. 그러나 유효 샘플이 REACH에만 있고 GRIP/TRANSPORT 샘플은 여전히 없다. 512환경 장기 실행 이력에는 native segmentation fault도 남아 있으므로 본 학습 안정성이 확정된 것은 아니다.

복구 후 smoke 결과: `docs/2026-10-12/runs/cuda_recovery_smoke_20261003/`. 평가 성공률 0, REACH 진입률 1, GRIP/TRANSPORT 진입률 0, REACH 평균 최소 거리 0.2205m.

추가 16환경·50 update 결과: `docs/2026-10-12/runs/main_16x50_20261003/`. 51,200 sample을 segmentation fault 없이 처리했지만 평가 성공률 0, GRIP/TRANSPORT 진입률 0, REACH 평균 최소 거리 0.2837m였다. 모든 rollout sample이 REACH에만 있었고, 평균 기타 이동량은 약 0.296m로 증가했다.

## 결과에 따른 개선 우선순위

- [ ] 학습 update를 늘리기 전에 기타 이동 억제와 REACH 방향 오차를 분리 진단한다.
- [ ] REACH에서 33개 관절을 동시에 탐색하지 않도록 기준 제어 또는 curriculum을 검증한다.
- [ ] 기타 중심 이동량·손바닥 법선/heading 오차·관절 포화율을 학습 중 지표로 노출한다.
- [ ] REACH ready가 실제로 발생한 뒤에만 GRIP/TRANSPORT 장기 학습으로 확장한다.

## 다음 개선 우선순위

1. NVIDIA 드라이버와 CUDA 장치가 보이는 실행 환경을 복구한다.
2. 8~32환경에서 100 update 이상 native crash 없이 실행되는지 확인한다.
3. REACH 전용 기준 제어 또는 curriculum으로 실제 최소 거리와 ready streak가 개선되는지 검증한다.
4. REACH→GRIP 전환 및 실제 접촉 force reader를 소규모 환경에서 확인한다.
5. 위 조건을 통과한 뒤에만 환경 수와 update를 단계적으로 늘린다.
