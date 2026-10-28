# Goal 초기화 모델 env0 실제 영상 준비

소유권은 이 native_video_v1/뿐이다. 원2023/회복2067/source/checkpoint/실제평가·타 작업자 분석은 변경하지 않는다. root만 native/GPU를 실행하며 env0 첫시도 한 번·손/전신 두 뷰를 고정한다. 실패여도 환경선택·재렌더하지 않는다.

- [x] 원3note render_native/capture/save_raw/upright camera/encoder 재사용, 실제 GoalPolicy fresh=False·layered contract·원metadata/PPO0/supervised1000을 검증하는 얇은 adapter.
- [x] 원 GoalPool.step의 rawgoal→decode→physical request는 전tick 한 번만 적용. 원 current-goal guard·원128cap/native105/90쌍/범위·4rad/s/PD/손목/판정 불변. NN firsttick/referenceN0. evaluator callback은 renderer에서 호출되지 않으므로 사용했다고 주장하지 않음.
- [x] metadata/header/alias·1회변환/오류·출력보호와 실제73모델 CPU identity 검사. 원CUDA topology 거부 및 임시projection 범위를 구분. 새파일의 좁은symtable 검사도 적용.
- [x] 회복NN actual 독립PASS SHA9070c12f... 연결. CPU준비·독립준비review·최종봉인 판정은 해당 JSON에 별도 기록. 실제 음악통과와 A release 미달/stage_readyFalse를 별도 유지.
- [ ] root만 1회렌더한 뒤 qa/에서 두MP4 전체decode/원128평가 수치차이 보존·대표8PNG/최소comparison sheet·직접upright/headfeet/가림 확인·통합 독립검수.

원checkpoint SHA70e40d1cb80a90a2636fd7d1babb4870bd82333d900c667fa136bac233ef9327, PPO0/supervised1000. 원fit exit1/누락보고서2개는 회복수용 이력으로 보존하며 정상완료로 재분류하지 않는다. 이전250/300/warmstart영상은 비교 재사용만 하고 재촬영하지 않는다. 고정기타/F4/finite stagedwrist/조건부 NN 초기화 범위이며 RL-only·자유기타J33·자연스러움/압력/해제 성공을 인증하지 않는다.
