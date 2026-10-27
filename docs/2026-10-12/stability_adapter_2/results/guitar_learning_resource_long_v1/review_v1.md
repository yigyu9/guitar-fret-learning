# 자원 활용 장기 학습 독립 검수

- 요약 판정: **현재 확인한 범위 문제없음**.
- 상태: pilot·실행기 사전 검수 완료. 최종 장기 설정·선택 보고서·시작 상태는 생성 후 추가 확인한다.
- 범위: 새 실험 orchestration과 기존 strict 재개 계약. 생산 코드·원자료를 변경하지 않았고 검수자가 native 실험이나 학습을 추가 실행하지 않았다.

## Critical

발견 없음. 현 시점 장기 시작을 막는 결함은 확인되지 않았다.

## Warning

- `pilot_dual16_left_settings_v1.json:3` 및 대응 pilot 설정의 horizon은 120tick이다. 첫 준비구간만 수집하므로 완료 episode는 0개이며 접촉·해제·반복 reset을 포함한 장기 처리량이나 음악 품질의 근거가 아니다. 자원 선택은 짧은 실측으로 한정하고 첫 전체 episode 길이의 장기 update에서 다시 확인한다. 이 범위 제한을 root에 전달했다.

## Suggestion

추가 구현 권고 없음.

## 확인 근거

- [run_pair_v1.py](run_pair_v1.py)의 stdout/stderr는 전용 파일로 기록되고 각 trainer는 새 session에서 시작한다. supervisor는 자신이 생성한 Popen 자식만 SIGINT로 중단 요청한 뒤 종료를 기다린다. 기존 trainer가 worker 종료·실패 checkpoint 보존을 담당하며, 임의의 다른 프로세스를 종료하는 코드는 없다.
- supervisor CPU는 `/proc/stat`의 host busy 비율이고 메모리는 host `MemAvailable`이다. GPU 표본도 host 진단이며 학습 전용 점유율로 확대하지 않는다. supervisor의 completed만으로 학습 성공을 판단하지 않고 개별 returncode와 trainer report를 확인했다.
- N8/N16 단독 pilot와 dual8/dual16 네 개 손별 pilot가 모두 completed=True, failure=None으로 종료했다. dual8·dual16 supervisor의 양손 returncode는 모두 0이다.
- 동시 실행의 합산 처리량은 양손 전이 합계를 supervisor 경과시간으로 나누었다. dual8은 1920 / 65.759918초 = 약 **29.20전이/s**, dual16은 3840 / 104.267517초 = 약 **36.83전이/s**다. 단독 N8/N16의 trainer 내부 wall 분모와 같은 계측 범위라고 해석하지 않는다.
- dual16의 최소 여유 메모리는 host 표본 **14.4567GiB**, trainer 표본 **13.9350GiB**다. 계측 시점 차이가 있으며 같은 수치를 강제하지 않는다. 현재 6GiB 보호선은 유지한다. 이는 순간적인 부족을 절대 방지한다는 보장은 아니다.
- pilot 설정은 `cuda:0`, `medium`, 상태563·행동39 및 기존 품질/타이밍/물리 계약을 유지한다. 메모리 guard는 기존 Monitor가 IPC 대기·수집 진행 시 검사하며, wall budget은 update 경계의 soft 제한이다.
- 초기 모델 SHA가 [initial_models_v1.json](initial_models_v1.json)과 일치한다. 원 LH update3 / RH update1을 CPU로 확인했다. dual8·dual16 양손 `initial.pt`와 원 checkpoint를 재귀 비교한 결과 metadata만 다르고 모델·Adam·RNG·identity·counter는 정확히 같다. Actor만 초기화한 실험이 아니다.
- [source_pins_v1.json](source_pins_v1.json)의 현행 169파일을 재해시한 결과 변경 0개였다. 이 작업에서 생산 소스 수정을 검수 전제로 삼지 않았다.

최종 장기 계획·설정과 실제 첫 update 검수는 아직 이 보고서의 완료 범위에 포함하지 않는다.
