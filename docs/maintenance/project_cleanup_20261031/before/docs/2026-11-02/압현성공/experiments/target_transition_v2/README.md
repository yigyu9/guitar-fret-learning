# 중지 목표 전환 개선 v2

같은 중지의6·7프렛 동시 성공 판정을 보정하고, 자유 기타에서 실제 참조 동작을 검증한 뒤 A→B 두 음 전환을 학습한다. 손목은 기존 허용 영역으로 안내하며 특정점으로 강제하지 않는다. 팔12축+중지4축 직접각 제어를 유지하고 단계별 행동 잠금은 넣지 않는다.

- [계획·체크리스트](PLAN.md): 승인 범위·예산·판정 기준
- [변경 전 원문](before/contact_fix_manifest.json): 기존 접촉 판정과 SHA
- [CPU 회귀 결과](validation/contact_fix_validation.json): 접촉 판정 관련59검사
- `geometry/reference_v3/`: 선택한 CPU 참조 후보와 휴지 마지막0.20초 정착 경로. 앞선v1/v2는 개발 과정으로 보존했다.
- `validation/reference_gap_*/`: 휴지별 실제 물리 추적·목표각·유지 결과
- `validation/preflight.json`: 참조·초기 자세·학습/재개/평가 검증 뒤 생성하는 실행 허가 근거
- `runs/comparison_v1/진행상황.md`: 본 비교 시작 뒤 현재 작업·완료 반복·예상 종료
- `runs/comparison_v1/RESULTS.md`, `summary.json`, `comparison.png`:100회마다 평균/확률 행동을 분리한 결과·분석·그림
- [공개 영상](../../video/target_transition_v2/): 실제 정책 손·전신 MP4만 저장

판정은 `wrong_press_sources.v3`이다. 같은 손가락의 높은 프렛 간섭도 낮은 목표 음을 차단한다. 낮은 프렛 접촉이 남았다는 이유만으로 높은 목표를 차단하지 않는다. 이전0.6초 연속 달성, 음 전체1.5초 유지, 시작 시각 준수는 각각 기록한다. 기하·몸체하중 후보와 실제 접촉점 힘·음향을 구분한다.

수정 후 source가 다른 구형 checkpoint를 암묵 재개하지 않는다. 기존 초기 FK 자세 데이터를 현재 소스 SHA로 새로 기록하되 과거 native 성공 플래그를 상속하지 않고 새 GPU 검증을 요구한다. 학습은 fresh E4·large64·H32·seed7/17 각300회이며, 참조가 성립하지 않으면 먼저 원인을 개선한다.

사전 검증을 통과해 휴지0.75초로 학습을 시작했다. 실제 참조 동작은0.75/1초에서6→7→6 각 음의 시작 준수와1.5초 전체 유지를 통과했다.0.5초는 이번 경로에서 실패했다. [검증 기록](validation/IMPLEMENTATION.md) · [참조 비교 그림](validation/reference_comparison.png). 참조 제어의 성공과 학습 정책의 성공은 별개다.
