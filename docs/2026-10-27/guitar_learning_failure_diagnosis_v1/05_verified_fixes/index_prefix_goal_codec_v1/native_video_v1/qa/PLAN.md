# Goal 모델 영상 CPU QA

소유권은 qa/만이다. root 실제 종료 통보 전 새영상/NPZ/raw 읽기0, 추가 native/GPU/재촬영0. 원2109봉인/source/model/기존평가/타작업자자료 불변.

- [x] 검수된 warmstart QA의 ffprobe/decode/원장·raw·guard 비교와 old250/300 PNG 비교 구성을 최소 재사용. stdlib 완료guard/self-check 뒤에만 실제 결과를 읽는다.
- [x] root 종료 후 실제 원본 strictload/모델불변·128readback/90쌍·clock/scene/encoder/alias·변환1회/reference0 검사.
- [x] 두MP4 전체decode·대표8PNG/2sheet·원128평가 env0 9보상/raw·whole128guard·typedgoal 차이 보존.
- [x] 직접upright/headfeet/가림 시각검사. 독립 source+수치+픽셀 통합검수 판정은 results_v1/review.json에 별도 기록하고 이 계획은 동결한다.

PPO0/지도1000·실제GoalPolicy·원70e40d 모델·F4고정기타/finite wrist 범위. 원musicTrue/releaseFalse/ANDfalse를 구분하며 성공환경 사후선별0. NN rawgoal과physical request는 구분한다. evaluator callback 미사용, 60Hz합력은240Hz최대나접촉쌍압력이 아니다.
