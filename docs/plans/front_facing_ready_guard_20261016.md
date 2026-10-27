# 실제 baseline 입력 연결에 맞춘 진입 검사 보완

native_baseline_v1은 실제28초/6720step을 완료하고 core28개·발 전행 검사·영상 검사를 모두 통과했다. 준비 후 삼중 지지와 양발 접촉은100%다. native_repeat_v1 시도는 scene 생성 전 run_v2의 baseline guard에서 멈췄고 물리 적분0회, native 출력 폴더도 생성되지 않았다. 실패 로그와 외부 입력 map/returncode는 보존한다.

실제 baseline의 세 map은 같은 config SHA를 모두 포함한다. analysis1601개와 wrapper1394개 map은 새 ready_spec도 직접 포함하지만, 원 runner가 생성한 attempt1061개 map에는 ready_spec 직접 항목이 없다. 기존 CPU의 합성 attempt map은 이 항목을 포함해서 실제 계약 차이를 놓쳤다. 기존 run_v2의 모든 map에 spec 직접 항목이 있어야 한다는 조건이 과도했다.

- [ ] 새 run_v3에서 모든 세 map의 config SHA와 전체 verify, 정확28개 gate, 원RAW/기간/실행경로/물리조건을 유지한다. spec 직접 SHA는 실제 완전 closure를 가진 analysis+wrapper 두 map에 각각 요구한다. attempt는 검증된 동일 config SHA와 그 config의 spec 경로/SHA를 통해 연결한다.
- [ ] 실제 baseline 파일로 원V2 거부/새V3 통과를 재현하고, analysis 또는 wrapper의 spec 누락, attempt의 config SHA 변조는 여전히 거부하는 CPU 검사를 수행한다.
- [ ] 원코드·source·계획·입출력은 보존한다. 제어기/형상/관절/목표/gain/cap/판정 수치는 바꾸지 않는다. 새 native는 run_v3, 외부 실행/선행단계 guard는 execute_v2를 사용한다.
- [ ] 새 prospective 입력 map/source 사본과 독립 검수·완료 ACK 후 native_repeat_v2로 재시도한다. 이후 release/free_strike/regrasp/continuous도_v2 출력으로 진행하되 config/spec은 기존 동결 V1을 그대로 사용한다. baseline은 통과한_v1 원자료를 재사용한다.
- [ ] 각 선행 단계의 core+발 전행 통과/원RAW SHA 연결이 확인돼야 다음 native로 진행한다. 본 진입 오류는 동적 불안정성으로 집계하지 않는다. 별도 source 후보/경로/물리 조건 변화가 없으므로 기존 source13개 gate를 재사용하며 새 entry와 helper·계획의 SHA를 추가 사전 봉인한다.
