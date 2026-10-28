# wrist candidate v3와 직전 v2의 실제 비교 준비

root가 실제8stage 종료0/199.807275179초를 통보한 뒤 CPU 분석을 실행했다. native_precheck와 활성 소스는 수정하지 않는다.

1. [x] 범위와 시각 정합을 고정했다. v2 검지는 직전 wrist_position_jacobian_v2/native_precheck, v2 중지는 같은 fix의 other_finger_regression, v3는 현재 native_precheck다. 각 버전·손가락의 reference/zero/random 4환경 첫 시도, 총12조건48시도를 실패 포함 분모로 사용한다. 과거 중지128은 비교하지 않는다.
2. [x] launcher/stage/scene/입력·설정·모델을 검증했다. v2 index4stage와 원 v2 middle12stage, v3 8stage의24scene 종료를 확인했다. 같은 손가락 settings 차이는 wrist_control뿐이며 training contract의 두 wrist_control 참조도 함께 대조했다. 실제 initial73 tensor가 모두 같고 이전 checkpoint는 현 runner로 로드하지 않았다.
3. [x] 과거 pin이 현재 경로와 다르면 archive/20261027_before_wrist_position_candidate_v3/manifest.json의 원경로·SHA·보관 byte를 명시 매핑했다. manifest521개 전체를 확인하고 실제 verified_at을 기록했다. 현재700핀과 동일 predicate SHA, 바뀌지 않은 ShortEnvironment class AST를 확인했다.
4. [x] v3에서만 recurrence를 재구성했다. endpoint k의 feedback은 precontrol 상태이며 k>=1 actual q는 직전 trace q다. base[k]는 원 reference→arm teacher2초 ramp, correction[k-1]=request[k-1]−base[k-1], proposal=base[k]+correction[k-1]다. 기록 candidate로 delta=clip(candidate−proposal,±.5°), 원 previous-request rate/action bounds, executed_action decode→native alpha.2/rate/bounds를 검산했다. k0 reset의 reference target/zero correction과 candidate=proposal·delta0을 따로 확인했다. 최대잔차2.23e-7rad였다. 후보는 unclipped 가상 기하이며 native 도달 증거가 아니다. v2 delta에는 새 recurrence를 적용하지 않았다.
5. [x] 전체48의 원래240Hz 음악 원장과 env0 저장60Hz 2,634끝점의 손목/선택4 추종·패드·loaded/any-sample geometry/facing/positive/candidate/wrong·몸체 합력을 분리해 집계했다. 현재 helper로 모든 저장 candidate/wrong/거리/높이를 재현했다. nearest와 any-sample witness, joint qd 미저장/0기하재생·body velocity 보존을 명시했다.
6. [x] 한국어 표/작은 그림·JSON/검증 pin을 저장하고 결과 고정 후 별도 actual 독립 검수를 요청한다. 힘은 env0의60Hz 몸체 합력 표본이며 전체4/240Hz 최대·현별힘·압력·접촉쌍·음향·정책학습 성과로 확대하지 않는다. 소지 또는 다른 손가락 성공은 이번 비교 범위가 아니다.

새 J 캡처나 native 추가 실행은 없다. 결과 검수 판정은 별도 review.json/REVIEW.md에 남긴다.
