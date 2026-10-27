# StabilityAdapter 목표와 책임

현재 새 기본 환경·스트랩·초기화·3초 WAIT 검증을 완료했다. 접근·그립·학습은 아직 미구현이다.
새 환경과 학습의 세부 기준은
[StabilityAdapter 환경과 학습 기준](../docs/2026-10-12/plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md)
한 문서를 따른다. 이전 관측 차원·보상 버전·완료 기록은 현재 실행 계약이 아니다.

## 현재 과제

스트랩이 연결된 자유 기타를 왼손으로 붙잡아 초기 위치·회전으로 복원하고 유지한다.
이번 독립 학습에는 fret·strike 실행이나 Synchronizer 명령을 포함하지 않는다.
제어는 왼쪽 L_Thorax부터 손가락까지이며, 오른손은 기준 자세 유지와 접촉 감지만 수행한다.

## 전체 시스템의 책임

향후에는 Fret·Strike의 연주 결과를 훼손하지 않는 기타 자세·지지 안정화를 담당한다.
tablature 생성, score clock 수정, Fret·Strike event 의미 변경은 이 모듈의 책임이 아니다.
연주 기술 보존과 FullBodyPlayer 결합 검사는 독립 복원 과제 검증 뒤 별도로 설계한다.

## 구현 원칙

공용 humanoid·기타 자산과 기존 스트랩을 검증한 뒤 사용한다. 이전 checkpoint·실험용
제어기·상수는 자동 승계하지 않는다. 기본 환경, 접촉·행동, 관측·보상·종료,
학습·평가 연결 순서로 구현하고 각 단계에서 CPU 검사와 실제 물리 검증을 수행한다.
