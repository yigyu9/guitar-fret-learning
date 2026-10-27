# Root 실제 실행·검증 기록

Preparation63314·minus00842830·plus00855888·analysis13391은 모두exit0다. 두 native는 각각1초기화/1200step/151frame, 총2초기화/2400step이며 새 물리 재실행은 없다. 분석29검사/38입력 SHA, wrapper 분석 사전39입력의 차이는 wrapper 자체 포함 여부다. 초기13공통 필드와1200step의 나머지80목표/시계/손목파형을 exact 대조했다. LA1.1018469719600776m는 세 조건 동일하다. Source fresh14검사와1188 source self쌍 검사도 각 통과했다. Source 형상 검사는 cooked 동적 관통 인증이 아니다.

Root는 실제 minus t0/5초와 plus5초 hands PNG를 열어 native 렌더·스트랩 주황 실선/가려진 점선·LA 표시를 확인했다. 그림 실제 QA는 생성 후 추가한다. 저장 영상은 각각151frame/30fps로 t0와5초 끝을 포함해5.033333초다.

+방향의 위치 개선과 회전 악화, −방향의 반대 tradeoff·후기 악화를 함께 기록했다. 4~5초 empirical one-column secant와 양방향50.75% 차이는 정적 즉시 Jacobian으로 해석하지 않는다. LS+.02768rad를 적용하지 않고 원기준 유지/다른 축 응답을 다음 단계로 결정했다. 기존66 제어권은 진단 단일축과 구분한다. 기타 고정·손부착·상태 지속 덮어쓰기·목표외력은 추가하지 않았다. 이전 CUDA 없음/CPU PhysX·visualgeom 메시지는 각 원로그에 보존했다. 실제 완료·렌더 확인과 로그 메시지를 구분한다.

Collection은4개 새 영상을 SHA exact로 복사해134개/new indexv7로 정리했다. 원본/기존 indexv6는 보존한다. Collector 실행 전에 두 report·네 source SHA·목적지 부재를 먼저 확인하도록 독립검수 지적을 반영했다. Artifact producer 미소비 사전 검토에서 baseline label과 self input SHA 누락도 실행 전에 보완했다. 이번 실패한 native/분석/그림 실행은 없으며 actor/학습0이다.

## Root 실제 그림 QA 완료

Root가 실제 chart PNG SHA d19d03ba92e80f3a13d3e0405686746421090e250ed84c2cf8aba2f1e93bb234를 열어 세 trace의 최대값/색상/0~5초와 원자료를 대조했다. 그래프는 초기 world오차, 표는2초 기준 vector/quaternion 후기변화로 구분한다. 범례는 데이터 밖에 있고 축은 모든 표본을 포함한다. Plus t0 PNG도 직접 열어 초기 배치와 주황 스트랩 경로/LA 표시를 확인했다. Producer exit0,69입력전후SHA/원문복사11개, native/actor/train0을 확인했다. 그림 재생성은 하지 않았다.

## 그림 실행 보존 범위

그림 실행의 exact shell command·환경·exit·로그 SHA와producer/입력전후SHA는 producer_execution.json에 있다. 실제producer·phase wrapper·직접helper·leaf계획11개는 plot 전에 복사·SHA 대조했다. 외부 shell 호출을 별도 파일로 만들어 실행 전에 archive한 기록은 없으므로 그 별도 사전 wrapper 원문을 보존했다고 주장하지 않는다. 이미 소비된 실행/원자료/그림/metadata는 수정·재실행하지 않고 이 좁은 기록 한계를 남긴다.

## 다음 축 사전 수치 확인 — 물리 미실행

보존된 current18 initial_values에서 L_Wrist_y 초기 PD각0.176372841rad/유지목표0.036752470rad/기존offset−0.139620371rad를 읽었다. 후보 ±.008을 합성한 float32 목표0.028752470389/0.044752471149rad는 해당 native 범위±.785398185rad와 기준 목표 offset±.3rad 안이다. 이는 해당 축의 읽기 전용 사전검산이며 전체목표/freshgate/실제 지지나 효과 검증을 대체하지 않는다. Wrist_y 실제 두 시험과 신규 feedback은 아직 미실행이다.
