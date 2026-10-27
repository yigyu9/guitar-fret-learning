# 논문 작성 메모

논문 제목: **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**

이 문서는 본문 밖의 후속 실험, 자료 배치, 과거 아이디어를 보존한다. 논문 본문은 [전체 목차](/home/ajou/yigyu/3/paper/README.md)에서 읽을 수 있다. 이 항목들은 수행된 실험 결과와 구별한다.

## 기여 문장과 후속 검증

현재 본문은 제어 구성, 공동 평가, 전이·지지 실패 분석을 기여로 기술한다. 연주 성공률 향상, 기존 방법 대비 우월성, 입력 오디오부터의 완전 자동 수행은 추가 근거에 따라 문장을 확정한다.

- 입력 오디오의 자동 전사, annotation 사용, 사람이 수정한 부분을 분리하여 전체 입력 이력을 기록한다.
- 보정 없는 기준선, 학습된 잔차 제어, 적절한 직접 학습 기준선을 같은 초기 조건과 평가 계약에서 비교한다.
- 여러 초기 조건과 곡에서 음악 이벤트 성공과 기타 이탈을 함께 평가한다.
- 원본 Fret/Strike의 성능 보존과 자유 기타의 접촉 변화가 음악 수행에 미치는 영향을 분석한다.

## 그림과 영상 후보

| 후보 | 용도와 원자료 |
|---|---|
| 전체 모듈 흐름 |오디오·계획·기술 prior·공동 보정의 관계. [Methodology](/home/ajou/yigyu/3/paper/03_methodology.md)의 흐름도 |
| 실제 pilot 네트워크 |825D/81D와기준목표·보정·PD관계. [현재 구조 그림](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/image/08_learning/I2001__stability_adapter_2_current_network.png) |
| 독립 기술과 자유 기타의 실패 |같은시각의손목·피크·프렛·기타오차를비교. [Fret전이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md), [Strike전이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md) |
| 공동 정책의 음악·범위 지표 |reward 합계와joint성공·outside거리분리. [병렬수집 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/README.md) |
| 초기 지지와 왼손 철수 |전신장면·접촉부위·기타이동을함께표시. [철수비교 정정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README_V2.md) |
| 원본과 현실 비율 형상 |동일 cm축척의시각/충돌형상. [정정그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/README.md) |
| OM 바디와 기타·손 집중 화면 |도면형상·native초기장면·현재지지. [OM결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/README.md), [집중화면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/README.md) |
| 표시된6현과 실제 물리의 구분 |현재marker기하의가림처리영상. [6현표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/README.md) |

그림에서 source 형상 proxy와 실제 native 렌더를 구별한다. 동일 초기 상태 이미지,
시간이 다른 frame, 서로 다른 카메라와 자산을 같은 물리 비교처럼 배치하지 않는다.
영상의 보기 좋은 부분만으로 음악이나 초기 지지 성공을 대신하지 않는다.


## 과거 설계와 보류 아이디어

연구 초기의 기타 초기점 복귀와 단계별 접근·그립·운반 계획은, 현재의 허용 범위 안 연주 문제로
바뀌기 전의 설계다. 이 자료는 과제 정의와 제어 구성이 바뀐 이유를 설명하는 데 사용할 수 있지만,
이전 수치·행동 차원·단계를 현재 방법에 합치지 않는다. 비교 대상이 되는 실패나 대안은 해당
실험의 원래 조건을 그대로 유지한다.

| 재료 | 원문과 활용 후보 |
|---|---|
| 초기 복귀 중심 논문 계획 |[과거 PAPER_PLAN](/home/ajou/yigyu/3/docs/PAPER_PLAN.md). 초기 pose 복귀와 연주 가능한 범위 유지의 차이를 설명 |
| WAIT·REACH·GRIP·TRANSPORT 경로 |[이전 lean 계획](/home/ajou/yigyu/3/docs/2026-10-12/plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md), [이전 실험 계획](/home/ajou/yigyu/3/docs/2026-09-21/stability_adapter/plans/TRANSPORT_LEARNING_DESIGN.md). 현재 연주의 필수 상태 전이로 사용하지 않음 |
| 초기 Full 모델 결합 후보 |[모델 비교](/home/ajou/yigyu/3/full/archive/02_architecture/MODEL_FUSION_STUDY.md), [과거 Action Residual 코드](/home/ajou/yigyu/3/full/action_residual/model.py). 설계 선택의 참고이며 현재81D pilot과 다른 prototype |
| 전사기의 onset·frame·HCQT 확장 |[transcribe_v2 설계](/home/ajou/yigyu/3/tab2fingermapping/transcribe_v2/DESIGN.md). 기본 Stage1과 분리된 실험 경로, 상류 오류 개선의 후속 후보 |
| 바레·압현 안전과 자세 확장 |[Fret 보류 항목](/home/ajou/yigyu/3/fret/04_deferred/README.md). 원래 규칙과 재검토 조건을 보존 |
| 실제 pick·줄 탄성·추가 주법 |[Strike 보류 항목](/home/ajou/yigyu/3/strike/04_deferred/README.md). 실제 물리·음향 및 라벨 확장이 필요한 후속 연구 |

자료를 보관한다는 판단과 논문에서 내용을 제외한다는 판단은 분리한다. 현재 초안은 배경·대안·실패
분석·후속 연구에 활용할 재료를 남기고, 최종 본문에서는 연구 질문과 검증에 직접 연결되는 내용을
선택한다.

## 관련 연구와 주장 범위

기타를 고정한 Luo 등의 연구 및 Xu와 Wang의 연구와, 움직이는 기타를 추적한 Canales와 Jörg의 연구를 구별한다. 전신·오디오 기반 악기 동작과 모션 캡처 없이 학습하는 기타 제어는 선행 연구에서 이미 다루어졌으므로, 본 연구의 차이는 비고정 기타의 물리적 지지와 연주 제어의 결합에서 설명한다.

Stage1 운지 배정은 탭에 지정된 줄·프렛을 유지하고 손가락·손 위치·유지 조건을 결정한다. 모든 동음의 줄·프렛 조합을 다시 탐색하거나 물리적 도달 가능성을 검증한 것으로 기술하지 않는다. 대표 곡 입력의 자동 전사 이력은 추가로 확인해야 한다.

## 방법의 후속 검증과 구현 범위

- 입력 오디오의 추정 오류부터 자유 기타 연주 결과까지 연결한 단일 종단 간 평가는 아직 없다. 본문은 파이프라인과 등록 목표를 이용한 물리 제어 평가 범위를 명시한다.
- G0 공통 이벤트 compiler와 CPU Synchronizer 계약은 구현되어 있으나, G0 물리 backend 전체 완료나 자유 기타 지속 양손 연주 성공으로 해석하면 안 된다. 본문에서는 역사적 구현 명칭을 최소화하고 공통 이벤트의 의미만 설명한다.
- 비교 실험에서는 원본 source, 자유 기타에 옮긴 source, nominal guard가 적용된 기준선, 학습 잔차의 효과를 분리해야 한다.
- 관측에는 별도의 일반 접촉력 센서 또는 손바닥 접촉 mask 블록이 없다. press cell과 sounding fret는 음악 판정 관측이다.
- 상세 reward v4에 제안된 이벤트 정규화, sustain/dropout/release ledger, 시선, 실제 접촉력 항 전체가 실행한 pilot에 적용된 것은 아니다.
- 피크 접근점의 phase별 선택과 원본 phase 의도의 정합성은 후속 검증 대상이다.
- 바레·특수 주법의 계획 표현 범위와 개별 Fret S0의 단음 중심 지원 범위를 혼동하면 안 된다.
- 피크 marker와 현 표시를 실제 pick grasp/slip 또는 줄 변형·진동·반력·음향 합성으로 설명하면 안 된다.
- 자산 변경 뒤 기존 음악 checkpoint의 성능은 별도 재평가해야 한다. OM 지지 실험을 이전 형상의 공동 정책 결과와 합치지 않는다.
- 몸통의 native 한계, 초기 기준±5도, residual±0.03 rad를 서로 다른 제약으로 기술한다. 팔 nominal guard±0.15 rad와 residual±0.30 rad도 별개다.
- 위치 허용 범위는 world actor-root 기준이며 후속 body-center/Pelvis-relative 제안은 실행 방법에 포함하지 않는다.
- 지속 자유 기타 연주 성공이 확인되지 않은 상태다. 방법 서술은 구성 및 실행 절차를 기술하며 성능 입증으로 간주하지 않는다.

## 후속 실험의 우선순위

현재 결과를 바탕으로 한 후속 실험 계획이다. 아래 항목은 수행 결과가 아니다.

| 우선순위 | 후속 실험 | 성공·보고 기준 |
|---|---|---|
| 1 | 최종 기타 형상에서 초기 지지 배치 확정 | 같은 초기값·물성에서 초기 낙하를 줄이고 위치/회전 허용범위·관통·접촉을 함께 기록 |
| 1 | 한 음 압현과 한 번 타현 | 실제 압현·dwell·correct string/timing을 공동 판정; 접근 거리만으로 통과하지 않음 |
| 1 | 단일 동작→이벤트 전환→짧은 구절→곡 | 성공 분모, 반복 수, 중도 종료 이유를 단계마다 보존 |
| 2 | 같은 초기분포·입력·학습 예산의 baseline 비교 | 동결쌍/nominal guard만/residual 학습을 같은 조건에서 비교 |
| 2 | 몸통 사용과 접촉 부위 ablation | 몸통 9 보정 OFF/ON, 신체 접촉 배치·스트랩 ON/OFF를 한 변수씩 비교 |
| 2 | 보상 ablation | pilot과 검증된 음악 ledger·안정성 비용의 효과를 같은 reward/환경 계약에서 비교 |
| 2 | 학습 seed·평가 자세 반복 | 평균·분산 또는 신뢰구간, seed별 성공률과 실패 유형 제시 |
| 3 | 곡·템포·구절 난이도 확대 | 다양한 string/fret 전환·down/up/다중현 조건을 구분해 일반화 평가 |
| 3 | 오디오 예측 입력과 검수 입력 비교 | 전사·운지 오류가 물리 연주에 미치는 영향과 수동 검수 범위 제시 |
| 3 | 바디 형상 전이와 물성 민감도 | 원본/OM의 같은 조건 비교, 질량·COM·관성·마찰의 영향과 checkpoint 호환성 검증 |

가장 최근 OM 초기 가슴·오른상완 지지 작업은 계획·초기 후보 검사 단계로 기록되어 있다. 이 초안에서 새 계획을 완료된 5초 유지나 연주 성공으로 쓰지 않는다. [최신 실행 계획](/home/ajou/yigyu/3/stability_adapter_2/OM_AXILLA_INITIAL_POSE_PLAN_V4.md)

최종 표와 그림은 음악 성공, 기타 허용범위, 신체 제어 및 실패 사례를 함께 보여주도록 구성한다. 신체 접촉의 효과를 주장하려면 접촉 발생뿐 아니라 그 조건이 기타 유지와 연주 결과를 개선했는지 확인해야 한다.


## 본문과 부록의 후속 편집

본문 후보는①고정 정책의 자유 기타 전이 실패와 제어 분리의 공통 시각 비교,②preload와 동결 양손의 차이,③동일 조건의 공동 학습 baseline 및 최종 음악·경계 결과,④신체 지지 ablation이다. 현재 표는 그 주장을 만들기 위한 기초자료이며 최종 논문에서는 새 성공 결과와 함께 축약한다.

source 표현·history 오차, PD 구동 검증, 그래픽 crash·실행 복구, 초기 bank 구축 및 거절, 좌표계·회전 집합 검사, OM 자산·시각 현 표시와 긴 영상은 추가 결과 또는 부록에 둔다. 이들 실행 검증을 성능의 주요 기여와 같은 수준으로 나열하지 않되, 재현과 실패 해석에 필요한 근거는 보존한다.


## 결과를 갱신할 때 확인할 조건

- 제목 From Audio의 종단간 성능은 Jazz1 provenance={} 상태의 등록 목표 물리 평가만으로 입증하지 못한다. 자동 예측 입력/annotation 기반 입력/수동 검수를 구분한 실험이 필요하다.
- 현재 Full-Body의 실제 구현은 root·하체를 고정한 전신 모델과 상체81 정책이다. 하체까지 모두 움직이는 정책으로 표현하지 않는다.
- 정확한 음악 성공과 기타 허용범위 유지를 반복 평가한 결과가 추가되면 Result의 최종 기여 서술을 갱신한다. 현재 공동 음악 0/42를 감추지 않는다.
- 실측과 설계 제안을 구분하고, 성능 지표는 해당 scene·평가계약·분모·시간창과 함께 유지한다.

## 제공된 과거 원고

2026-10-13에 전달된 DIGIT 원고의 절·그림·인용별 활용 판단은 [과거 원고 대조](/home/ajou/yigyu/3/paper/legacy_draft_review.md)에 모았다. 확산 모델·영상 추출·AMP 경로와 당시 데이터 규모는 역사 자료로 보존하며, 현재 결과의 실측 근거는 기존 근거 색인을 따른다. 과거의 CQT→전사 그림 구성은 현재 입력과 예측·정답의 대응을 확인한 새 그림의 후보로 활용할 수 있다.
