# 학습 중단·음악 목표 발견 개선

사용자 요청: 확인된 문제를 수정하고 실제 검증한다. 기존실행과실패/자산/제어/성공판정은보존한다. Root고정/하체유한/105·97·8/자유기타/중력ON/스트랩OFF/준비2초유지. 분석상hostOOM확정이나단독누수/worker직접OOMkill미확정이므로timeout연장으로덮지않는다.

- [x] 현행코드/검사/문서/설정을archive에SHA일치보존한다.
- [x] runner에저메모리중단/자원시계열/터미널heartbeat/정확한실패원인/예외·중단시마지막유효체크포인트를추가한다.
- [x] pool대기를짧은poll로감시하고worker죽음/응답없음/수집·reset진행을구분한다. callback오류시부분rollout폐기·정리검사를추가한다.
- [x] 기존성공판정유지하에별도dense환경으로왼손접근보상시간확대와오른손시각조건trajectory접근신호를추가하고read-only계산/실패처리를검사한다.
- [x] 명시한지원단음pool을episode마다선택할수있는wrapper를구현한다. 정책공통계약과episode목표기록을분리하고기존고정목표/legacy계약을보존한다.
- [x] CPU검사와독립검수후실제기존checkpoint연결/중단저장/8환경단기수집·PPO를확인한다. OOM을실제로유발하지않는다.
- [x] 8환경/전체batch2048/저메모리4GiB/주기5저장설정과새보상별새시작규칙,실제결과/남은범위/실행법을한국어로정리하고최종봉인한다.

구현소유권:root통합·config·실행·문서·봉인;worker_runner train_parallel.py/monitoring.py와해당검사;worker_pool parallel.py와해당검사;worker_music 새dense_environment.py/task_sampling.py와새검사. worker들은서로파일을덮지않고원자산/기존실험을수정하지않는다. 상호인터페이스는Pool.wait_callback(대기context dict),Collector.collect(horizon,progress_callback=None),spec.music={reward_mode:legacy|dense_v2,goal_event_indices:null|list}다. 새보상은기존checkpoint resume계약을무시하지않으며새정책으로검증한다.

실험은bounded smoke/pilot로실행하며8시간장기실행/연주수렴을자동선언하지않는다. 결과:docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1.

실제검증중추가발견: 첫pool실행은개별task길이별관측scale차이로initialreset실패했다. 계약만덮어쓰지않고sampled wrapper의실제builder와반환관측을pool공통시간기준으로고친후realRecordedSession회귀검사와새native재시도로확인한다. 실패입력/실행/소스는별도보존한다.

완료: CPU127개,기존모델중단저장/재개와fakeguard,native N8두실행각4096전이,N2수정pool1024전이통과. 첫pool계약실패도보존했다. 실제음악성공/거리감소미확인과새8h미시작을결과에명시한다. 최종검수·입력버전/소스/결과봉인을함께확인한다.
