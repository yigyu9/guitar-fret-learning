# GPU 물리 배치 학습 전환

사용자 요청: 현행 학습을 GPU 기반으로 변경한다. 이전 CPU 정책·물리 실행과 원자료는 보존하고, 합의한035/v14 초기 자세·105/97/8·자유 기타·중력ON·스트랩OFF·유연한 왼손·현재 보상 단계를 유지한다.

## 진행 및 확인 기준

- [x] 기존 코드 및 local Isaac 문서 감사, CPU 원본410개와 README/AGENTS 보관
- [x] 한 GPU PhysX+GPU tensor pipeline 시뮬레이터의2환경 실제CUDA상태·접촉힘·Jacobian·물리2step 확인
- [x] 독립 경계reset·실제PPO·환경수확대 검증
- [x] 기본 손별 학습 연결: 환경마다 프로세스를 만들지 않고 공용 GPU 물리를 한 번씩 진행
- [x] 현재 제어·관측·240Hz 접촉/안전·곡 원장·curriculum·PPO·저장/재개 연결
- [x] 소수 환경 native GPU 실행·PPO·선택reset·horizon연속성 검증, 이후 큰 환경 수 자원 시험
- [x] CPU 회귀 검사·독립 change-reviewer·문서/실행 명령 갱신

## 확인한 제약과 결정

Isaac Gym Preview4의 GPU pipeline은 기존 접촉쌍/local witness API와 native 질량행렬을 그대로 제공하지 않는다. GPU PhysX와 CPU tensor pipeline 조합은 지원한다. 사용자가 접촉 판정까지 새 GPU 방식으로 재설계하는 경로를 명시적으로 선택했다. GPU PhysX+GPU tensor pipeline으로 물리·유한 제어·관측·접촉 후보·보상을 배치 처리하고, 기존 witness 기반 clean 성공과 다른 새 surface/load 기반 후보 계약을 구분한다. 하체 IK는 배치 tensor solver로 재설계하고 차이를 기록한다. 어떤 경로도 정책만 CUDA로 옮기고 GPU 물리라고 보고하지 않는다.

이전CPU strict checkpoint를 GPU 물리와 같은 계약으로 취급하지 않는다. 과거 결과/원문/CAS를 수정하거나 입력 검증·물리 안전을 완화하지 않는다. 1024 실행 가능성과 처리율은 실제 시험 후 보고한다.

## 최종 결과와 한계

- 기본128·오른손·large1024 GPU PhysX/CUDA tensor/PPO 저장 및 strict 재개 확인. large1024 PPO2/65536전이, 재개추가PPO1/32768전이.
- 실제2환경 행동0 전곡1969tick/67음 안전 완주2/2, 수집 경계62회와음별원장/curriculum 처리 확인. 선택reset의다른행불변·제어캐시·실제시계검사 통과.
- 1024초기정책의979완료에피소드는모두물리실패다. 대규모 안정전곡·100업데이트·연주수렴을인증하지않았다. 겹친/compact배치는용량경고/물리실패로채택하지않았다.
- 최종GPU관련30CPU검사통과. 전체고유785중784통과, 변경하지않은teacher-proof preflight1개단독SIGFPE는보존·보고했다. 전체검사성공이라고표현하지않는다.
- 별도change-reviewer가코드·실제checkpoint경계·입력pin을검수했고발견한로그문서2곳을수정했다. 최종자료는`docs/2026-10-20/guitar_learning_gpu_batch_v1/README.md`에연결했다.
