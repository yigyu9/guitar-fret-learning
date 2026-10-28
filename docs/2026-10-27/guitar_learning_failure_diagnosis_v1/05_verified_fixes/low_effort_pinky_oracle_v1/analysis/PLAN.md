# 낮은 상한 소지 유한 탐색 분석 계획

소유 범위는 이 `analysis/`뿐이다. 부모 준비·소스·기존 결과·원자료를 바꾸거나 GPU/native를 실행하지 않는다. root의 실제 종료 통보 뒤에만 `analyze.py --root-completed`로 새 `results_v1/`을 만든다. 인자 없이 실행하면 원자료를 읽거나 결과를 만들지 않는다.

1. **출처·실행 확인**: 부모 준비/독립검수 SHA, 실제 launcher의 소지 child 1개 종료0, 입력 전후 불변, 장면 종료·72환경 readback·105 native 속성·16축 effort만0.25Nm·90 collision pairs를 확인한다. 현재 계약에서 cap 진단 선언을 제거한 값은 검수된 기존 소지 reference 계약과 같아야 한다. 이는 새20Nm 실행이 아니다.
2. **분모·순위 검산**: 원 helper로 225개 선언, 유효72·제외153개와 각 제외 사유를 재생성한다. 실패를 포함한72개 첫 시도·음원장·9보상을 보존하고 원 eligible 조건/최소 perturbation 순위 및 selection을 독립 재계산한다. 225행 표에서 제외 행을 지우지 않는다.
3. **관찰 범위 검산**: 전체72행의 저장60Hz 단계별 통계/6gate, actual/target4·세 마디 순힘·손목을 비교한다. 사전 상세 행은 `[22,109,112,113,115,130]` 6개이다. 기존 기하 분석 helper를 재사용해 해당 원자료의 candidate/wrong·잘못된 프렛/현/다른 손가락 higher 원인·각도·힘·손목과 통계를 재계산한다. 단일 trace 재생을 위한 helper의 임시 env0 표기와 실제 원장의 env_id를 구분한다.
4. **해석·검수**: 새 batch의 baseline112(env56)는 기존4환경 소지 reference와 별도 실제 시도이다. 이전 검수된 reference 수치를 출처 표시하여 비교하고 동일 실행이라고 보지 않는다. 성공 후보가 있으면 원 순위1개에 대한 새4시도 검증이 필요하며, 없으면 grid/cap 확장을 멈추고 손목/제약을 분리하는 다음 진단을 검토한다. 실제 결과는 독립 change-reviewer에게 검수한다.

## 보존할 한계

- 같은 seed7의72환경이며72seed가 아니다. no-NN finite scripted 명령이며 정책학습/자유 기타 성과가 아니다.
- 몸체 순힘은 특정 접촉쌍·실제 현 압력·모터 토크가 아니다. native0.25Nm readback은 몸체 순힘 상한을 인증하지 않는다.
- 저장60Hz 끝점 통계와 원래240Hz 음악 원장을 구분한다. 미저장 행의 자세/힘 시계열, nativeqd, native nearest sample index/normalcos를 복원했다고 주장하지 않는다. nearest와 any-candidate/wrong의 동일점 증명도 하지 않는다.
- 기존 nearest tie 한계와 CPU 재생의 거리/높이 잔차 및 gate 불일치는 그대로 남긴다. 원 판정·임계·순위를 바꾸거나 random env3 성공 명령을 고정 목표로 역산하지 않는다. MCP2축 native 자세를 팔3축 FK로 대체하지 않는다.

## 체크리스트

- [x] 분석 도구 AST·무인자 stdlib-only 실행 및 기존 원 helper import 확인. 순수 CPU 가상 원장으로 후보 없음/기준 경계 통과/물리·손목 실패 제외/clean·wrong 미달/첫 시도 누락 거부를 확인했다. 원 225/72 선언 재계산과 baseline112→env56 대응도 일치한다. 결과는 만들지 않았다.
- [ ] root 실제 종료 통보와 새 원자료 검산
- [ ] 225행/72시도 결과·한국어 보고서 생성
- [ ] 독립 actual 검수와 SHA 기록
