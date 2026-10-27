# 독립 검수

요약 판정: 문제없음. 소비 코드 차이·native 원자료·분석·영상·최종 문서를 읽기 전용으로 대조했다. 물리, actor, solver, 분석 producer 및 렌더 재실행은 없다.

- recovery-priority 대비 변경은 phase2 증분 gain0.5→1.0과 해당 기록값뿐이다. 원본 READY/APPROACH의 policy+PI, 회복 중 I동결, RHfinger21 policy, source waypoint/clearance/latch/detector/음표 시간/weights 및 normal PD 제출을 유지한다. local fit delta±0.15와 누적 actuator goal의 native limits·최종 float32 rate3.2 cap을 구별한다. AST3.8 통과.
- 초기 native state/81각도/PD/bounds/rate/gain이 비교 실행과 exact이고 첫150개 목표·step≤600 native 표본이 exact다. 모든300개 최종 목표·held36·source30 history 역변환,180개 다음 observation history를 독립 재계산했다. phase0/1의 float32 PI preview/conditional antiwindup,52개 phase2의 previous goal+delta·I동결·entry selector/event key가 저장 값과 exact다. 저장 native와 맞는90개 actor 표본의 실제81각도/pick/ChestDelta/currentG target도 직접 대조했다.
- 실제1200 physics steps·151 camera frames·16개 계약 검사 통과,PREPARE49/PLAY180/HOLD71이다. source terminal3.816667초(step916) 추가 trace가 있어152개이고 카메라151개와 구별한다. HOLD의 목표/history/source clock은 동결되며 물리는5초까지 이어진다.
- raw pulse 합산은 hit/physical hit/accepted release1/1/1, release/miss/wrong5/7/4, 마지막 partial F1 0.153846이다. 첫 hit2.483333초/string2와 기존 timing45.179844ms를 확인했다. RECOVER physical release0, lifted2.783333초, reached 및 scheduled recovery-complete3.15초1회이며 이전0.5조건보다 각각0.1/0.116667초 이르다. 그러나 source2→1 전이는 동일3.35초이고 곡 목표 완료는 false다. scheduled pulse를 별도 full recovery 또는 전체 연주 성공으로 바꾸지 않는다.
- wrong4회는 정확히 초기READY1.033333초1회와 후기APPROACH3.516667/3.733333/3.8초3회다. README:17의 ‘이후4회’는 검수 요청 후 원문 보존·정정돼 전체/후기 범위를 구별한다.
- 독립 p/quaternion·controls 계산은 최소 PREPARE/PLAY/HOLD25.211255/1.907328/14.148093mm,기타 최대/종료 위치46.353646/38.303635mm·회전9.019638/5.132309°,전체/policy 범위 참238/300·132/180이며 분석표와 일치한다.
- native 사전 입력1035개·소스 사본291개 SHA와 종료 변경0을 확인했다. 현재1033개 exact와 승인된 mainREADME/PLAN 두 문서의 원본 prefix를 대조했다. 분석 직접7개 입력 전후/current exact,151capture/302PNG SHA·readonly 및 두 실제MP4 SHA/ffprobe151frames·30fps·5.033333초가 일치했다. 실제5초 손 프레임과 최종 문서의 모든 절대 링크를 확인했다.

소비 runner SHA:39357cbf06f661f766ce19079db594269ceb0898f0b82ed09c5e912941d1366e. wrapper SHA:89e09c76c9c5203596e52550a0389a64b3df2f15e6a66a3e1701ab880d2f8cb4. 최종 README SHA:1cac75e0493b84601fa4d7853897655040df5a3bca0bb7763df02848359b45f9. CHANGED_FILES SHA:b0f59411dc4da137b39c83344ab4cddd2cbd54ced9f5c2582b7f1e2b03383e5e.

미해결 Critical/Warning 없음. PASS는 관측·계약·보존·문서의 정합성 판정이다. 회복 한 성공 관측은 후속 타현이나 곡 전체 성공·반복 재현성·정식 actor 자격·cooked clearance 인증을 뜻하지 않는다. 후속 gain2의 실제 응답은 이 검수 범위 밖이다.

최종 판정: PASS
