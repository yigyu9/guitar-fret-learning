# 전환 학습 보상·탐색·성공자료 재사용 보완

사용자 승인: 앞서 제안한 네 가지 개선의 구현 진행. 새 장기 학습은 이 요청의 구현 완료와 구분한다.

## 원칙과 범위

- 기존 봉인 소스33개·실행·모델·실패·원자료를 수정하지 않는다. 신규 코드는 guitar_learning/transition_refinement/와 tests/에 둔다. 원본 보관은 기존 source_snapshot_v3와 새 구현 전 archive manifest로 명시한다.
- Root고정/하체유한제어/105·97·8/기타자유·중력ON·strapOFF/원gain·범위·rate·안전종료 유지.
- 단음 A부터 개선 효과를 검증한다. 범용 전곡·두음 전환 성공을 주장하지 않는다.
- BC 초기화는 새 보상·탐색 계약으로 명시적으로 Actor만 이전한다. 이전 모델 성공은 상속하지 않고 새 native 평가로 확인한다. strict resume 약화 금지.

## 계획·검증 체크리스트

- [x] 보상: 0~2초 준비 접근/실제접촉 보상, 평가와 같은90% 유지 보너스/해제. 겹친 준비는 higher-fret A clean + lower B positive 규칙 유지. 경계·한번만지급·실패tick양성억제 CPU 검증.
- [x] 탐색/학습: 명시된 작은 std 하한·초기값 적용, 성공자료 모방 보조손실과 PPO를 함께 최적화. 기존 PPO KL/transaction/critic/strict 저장·재개 유지. gradient/모델불변/소스/identity CPU 검증.
- [x] 연결: 새 초기화·환경·train/eval·탐색량 비교·기록·감사를 연결. 실제 BC 증거 검증과 보상 변경을 명시한 이전, 새4회 native gate와 과거 gate 거부. 보상/탐색별 설정과 실행법 제공.
- [x] 별도 change-reviewer 검수·CPU검사·소스 봉인 완료. 실제 native 연결 확인을 시도했고 SIGFPE로 미완료인 범위를 아래에 기록했다. 장기 성과와 구분해 문서화.

담당은 파일별로 분리한다. 다른 작업자의 수정은 되돌리지 않는다. 설정/모델/소스는 native 사용 전에 봉인하고 사용 후 수정하지 않는다.

## 구현 후 검증 진행

- 새 패키지·검사·설정 구현 완료. 기존33파일 SHA 불변 확인. 원본 포함53파일을 새 결과의 source_snapshot_v1/source_pins_v1로 보존했다.
- 보상12+학습9+연결7+공유PPO6=34검사 통과, 탐색 비교9검사 별도 통과. 최종 통합 재검사에서는 기존 유형의 CPython float formatter SIGFPE가 발생해 실패 로그를 보존했다. CPU 전용 격리 검사와 실제 native 검증으로 구분 중이다.
- 실제 새 보상 계약으로 초기 정책의 독립4회 native 실행을 시작했다. 새 성공 원자료의 감사와1업데이트 연결 확인은 아직 완료되지 않았다.

## 최종 검증 상태

- 동일43검사를 CPU전용(CUDA_VISIBLE_DEVICES 비움)으로 실행해15.800초에 모두 통과했다. 앞선 SIGFPE 실패 로그는 보존했고, 오류가 해결됐다는 뜻으로 확대하지 않는다. 별도 검수 미해결 지적0개.
- 새 native2회는 각각 task3.55초/1.633333초의 완전 기록 이후 Python float formatter SIGFPE로 중단됐다. 완료성공0개이며 새4gate·PPO1update·checkpoint 재로드는 미완료다. 새 PPO는 시작하지 않았다.
- 두 부분 trace의311행/1244개240Hz 표본에서 보상 조합 재계산은 일치했다. 전체 capture 감사나 성공 gate가 아니다.
-53개 활성/보관 SHA 불변, 이번 작업의 프로세스 잔류 없음. 코드 설명은 guitar_learning/transition_refinement/README.md, 실제 결과와 후속 순서는 docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/README.md다.

후속 검증:

- [ ] SIGFPE 근본 원인 규명.
- [ ] 새 독립4회 완주 및 native capture 감사.
- [ ] 실제4gate 경로를 포함하는 새 학습 설정 버전.
- [ ] PPO1update와 strict checkpoint 재로드.
- [ ] 탐색 비교·학습 개선 검증 후 장기/전환 학습.
