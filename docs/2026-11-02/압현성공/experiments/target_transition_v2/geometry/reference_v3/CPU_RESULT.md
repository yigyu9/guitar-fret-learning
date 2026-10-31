# 정시 전환 참조 v3

최종 휴지 0.20초는 다음 press 목표각을 유지하는 settling 구간이다. 이륙·수평이동·하강은 gap-0.20초 안에 완료하며 이전 음 1.5초 유지를 침범하지 않는다. 각 endpoint의 finite-cell 기하와 다른 세 손가락 패드 6mm 간격은 v2와 같다.

Native 초기 상태는 최적화 hover로 바꾸지 않고 geometry/initial_catalog.json의 학습 초기 q/state/hold_target을 그대로 사용한다. 0.5초 초기 유지 → 1초 Apress 요청 전환 후 음 유지창을 시작한다. CPU initial_state는 endpoint 일관성 데이터일 뿐 native reset에 쓰지 않는다.

실제 제어기와 대조할 연속 quintic 이론최대속도와 60Hz 표본최대속도를 모두 기록했다. 0.5/0.75/1초 조건의 속도는 모두 팔 3rad/s·중지 4rad/s 이내다. 이 값은 물리 추종 성공의 증명이 아니다.

Native strict AB 판정은 첫두음의 전체1.5초 clean과 시작 후 최대1/240초 내 최초clean, 최초 상태 일치·오압현·손목/물리 안전·source 일치·중간reset없음·정상정리까지 요구한다. BA/ABA는 별도 보조 판정이다. 기존 native_verified는 90% 유지 판정으로서 정시·완전 유지와 구분한다.

이전 기준 소스는 before/reference_baseline_v2에 해시와 함께 보존했다. CPU 회귀검사5개 통과.
