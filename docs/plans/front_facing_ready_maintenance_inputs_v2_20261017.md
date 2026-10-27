# 후속 유지제어 입력 경로 보완

- 기존 실행 계획의 `inputs_maintenance_v1`은 첫 생성 시 역사 SHA map에 미사용 release/free_strike/regrasp 설정이 없어서 baseline/repeat 두 개만 생성하고 중단했다. 원 코드·실패 기록·부분 설정은 보존한다.
- 정규 새 후보의 입력은 `paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_maintenance_v2`의 다섯 설정이다. 원본71 key를 소비된 baseline과 대조해 case/schedule/seconds 외 공통값이 동일함을 확인하고, 미사용3 원본은 이번 prospective SHA로 처음 닫았다. 과거 봉인에 포함됐다고 설명하지 않는다.
- 이번 변경은 원본 대비 설정당10 key(몸통4, 손5, baseline 결과경로1)이며 변경 근거와 원본·신규 SHA는 `maintenance_execution_v1/config_generation_v2.json`에 기록했다. 물리 실행0.
- 새 runtime/analyzer/진입점 및 형상 감사의 독립 검수가 끝난 뒤 baseline28초만 우선 실행한다. 이후17..22초 정지5초와 모든 필수 gate를 확인하고 다음 동작으로 진행한다.
