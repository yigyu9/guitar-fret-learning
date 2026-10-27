# 목표별 도달성과 두 음 전환 구현

사용자가 앞서 제안한 방향의 구현을 승인했다. 기존 봉인된 song/song_reward_v2와 과거 모델·실험·공용 자산은 변경하지 않는다. 신규 구현은 guitar_learning/transition/, 검사는 guitar_learning/tests/test_transition_*.py, 실행 결과는 새 결과 디렉토리에 둔다.

- [x] 첫 두 음 및 고유 30목표를 추출하고 단음/겹친 준비/느린 두 음 task와 240Hz 판정 구현.
- [x] 현재39행동의 실제 endpoint 교집합 안에서 기하 후보 생성, 같은 codec를 통한 접근·유지·해제 교사 구현.
- [x] native replay·관측 직전 capture·실패/불변입력/안전 감사와 자료 채택 gate 연결.
- [x] 목표 조건부500입력 손별 정책의 성공자료 BC, 보조 없는 평가, fresh PPO·엄격 resume 연결.
- [x] 경계/반례 CPU 검사 및 별도 코드 검수, 신규 소스 봉인. 53개 PASS/94.485s, 검수 Critical/Warning 없음, 24개 소스 snapshot 일치.
- [x] 짧은 실제 native 실행으로 경로/측정 검증. A/B 각각4초 안전완주했으나 clean0%, B최초SIGFPE는별도보존하고동일입력재실행완주. 성공교사0이므로 BC/PPO 미시작. 실제 실패case3개 모두 capture 채택거부 확인.
- [x] 코드 위치·명령·실제 검증·남은 실험 문서화. guitar_learning/transition/README.md와 docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_v1/README.md 참조. 후속은 원제어범위 내 실제접촉 피드백 접근 보정→단음성공→겹친준비/느린전환→BC/정책평가/PPO 순서.

불변 조건: Root고정, 하체 유한제어,105/97/8, 기타자유·중력ON·스트랩OFF, 원gain/원제한·smoothing·rate·안전종료 유지. solver는 후보생성만 하고 실제상태/기타힘/매step상태 덮어쓰기를 하지 않는다. 손끝원점거리나정적IK로실제clean성공을대체하지 않는다. 단음A/B성공과reset없는A→B전환을구분한다. 다음5프렛의positive사전접촉과clean은별도이며7프렛을유지하는동안5프렛clean을요구하지 않는다.

역할분담: task/metrics/environment; solver/teacher; policy/transfer/BC/PPO; root probe/통합/실행/문서. 독립 worker는 다른 담당 파일을 수정하거나 기존 편집을 되돌리지 않는다. 새코드의최초봉인후수정은snapshot/archive와새실행버전으로진행한다.
