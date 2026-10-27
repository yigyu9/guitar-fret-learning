# source 제안 v1 보존과 v2 보완

읽기 전용 독립 검수에서 t0의 PD base 선택 오류를 발견했다. v1은
initial_PD_target_rad를 읽었지만 이 값은 초기 실제각이며, 실행에 제출된 유지 목표는
controls[0].final_target_rad=preserved_absolute_targets_rad다. v1 source·로그·JSON과
모델 검증 결과는 보존하고 새 search_coupled_support_source_v2.py/search_v2.json을 사용한다.

v2는 모든 시점의 원본 제출목표를 base로 읽고, t0 원본 유지목표 일치와 비선택63개
목표 불변을 assert한다. Base+delta의 model/손한계와초기±.3rad 경계도 재계산한다.
18개만 선택했으므로 native81의 나머지63개는 목표가 바뀌지 않는다.

v1의5초 quarter는 대표점오차가 줄었지만wholepalm–patch upper가8.913→9.183mm로
늘었다. v2에서는 후보 upper가 baseline lower보다 작아야 실제 source hull 접근으로
표시한다. 이는 source 방향 선별 조건이며 최종 성공/PhysX 허용 오차가 아니다.
Whole-hand source 교차증가, +Z반구, 원본PDbase 보존 조건도 그대로 유지한다.
정책 가중치/상태/기타/스트랩 수정이나 새 physics 실행은 없다.
