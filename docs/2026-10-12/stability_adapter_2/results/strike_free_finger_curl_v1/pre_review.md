# Free finger curl 사전 독립 검수

요약 판정: **문제없음 / 사전 PASS**. 남은 Critical·Warning·Suggestion 없음. Native 초기화·물리 실행은0회다.

- `run_strike_free_finger_curl.py:70,148`은 PLAY마다 source의 finger21 목표를 새로 복사한 뒤 RH:middle2/3·ring2/3(index71/72/75/76)에만0.2rad를 더한다. 이전 actuator 목표에 누적하는 보정이 아니다. 실제 grip reference의 pinch9와 네 보정축은 분리돼 있으며 남은 finger17의 요청은 코드상 그대로다. 저장 기준 target을 사용한 순수 float32 대조에서4개 residual 허용오차2e−7rad 이내·다른17개 exact를 확인했다.
- 기존 timed-wait-rebase와 diff상 초기 q/G·PREPARE·팔R9 policy+PI·closed wait actual IK·RECOVER 이전 목표+2δ·왼팔·PD schedule·source clock/detector/성공 조건은 변경하지 않았다. Curl은 `advance`의 PLAY 목표에만 추가하며 source finger21와 요청4목표를 기록한다. 몸체 상태·기타 pose 쓰기·기타 힘·EFFORT 명령·부착·충돌 설정 변경은 없다.
- `:106–118`은 기존 native bounds 및 PLAY source30에 적용하는 right-rate 경계, 제출 후 state 보존, 실제 전달 target 기반 source history 갱신을 유지한다. Source action/history 갱신 메커니즘이 유지되는 것이며 curl 이후 history 값과 물리 궤적이 기준과 같다는 뜻은 아니다. Source의 free-action0.22rad envelope를 넘을 수 있다는 문서 한계와 맞는다.
- `:221–225`의 pinch requested exact 및 nominal residual float32 허용오차 검사를 확인했다. Requested curl과 최종 native/rate clipping 후 전달 목표를 구분한다. 최초 actor 입력/출력 및 PREPARE prefix 동일성은 실행 후 실제 기록으로 확인해야 한다.
- 두 파일 Python3.8 AST와 dict literal의 중복 문자열 key 부재를 확인했다. Wrapper는 실제 실행 모듈만 바꾸고 기존 입력 사전/종료 SHA·source 보존·argv 복구를 유지하며 GRIP 입력은 기존 closure에 포함된다. 정적 FK의 간격 개선은 동적 충돌·타현·그립 성공 인증으로 확대하지 않는 계획 범위가 맞는다.

확인 SHA256: runner `3b3b44add9393cbd58fa7c8333edf3de78f7cd11daaea9d1f807abd09a8dde8b`, wrapper `6adbb9c5c3f7d4ec793ab4427ee8e9dd38368ab7b0fa9da5d500e49461d5eb35`, 계획 `210b0cacf95d6c08ae631bcb2d21d794364368f0eea7ff8dc9c546cecf9cbd4f`.

이 판정은 변경 구현·순수 목표 수학·문서 범위다. 실제5초 반응·초기/PREPARE prefix·contact·회복·지속 타현·전체 actor30 행동 또는 source/native CPU/GPU 동등성은 실행 후 별도 검수한다.
