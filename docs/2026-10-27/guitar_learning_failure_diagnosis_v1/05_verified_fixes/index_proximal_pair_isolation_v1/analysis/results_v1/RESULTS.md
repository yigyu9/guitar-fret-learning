# 검지 첫마디 단일 충돌쌍 분리: 실제 A/B

단일 pair 제외 개입은 큰 순힘의 분포를 바꿨지만 압현 미달을 해결하지 못했다. baseline의 검지 첫마디 약73.4N은 refilter에서 0N이 됐고, 검지 둘째마디와 중지 첫마디에는 약52.7N이 남았다. **양쪽 달성0/4라는 사실만으로 이 한 쌍이 고하중과 무관하다고 결론낼 수 없다.** 동시에 이 순힘 기록은 원래 또는 새 접촉쌍의 압력 인증도 아니다.

## 실제 실행과 통제 항목

root가 두 fresh scene을 직렬 실행했고 launcher는 각각 exit0, 31.2613/29.7112초, 전체60.9730초다. 각4환경 첫 시도 총8개를 모두 포함했다. 두 report completed/closed, wrapper 1회/복원, 입력 before/after 불변·unpinned0이 통과했다. 준비677핀과 두 실행의 현재 입력 SHA도 확인했다. 각 장면은221 control/884 physics이며 고정 기타·GPU PhysX·240/60Hz다. GPU 재실행은 하지 않았다.

실제 collision condition은 CPU 사전 선언과 exact 같다. 55shape/1485쌍의 두 matrix/hash를 검산했고 **index1/middle1 한 쌍만 enabled→disabled**, 나머지1484쌍·external filter 관계·비filter 속성은 보존됐다. 원90 contract와 refilter89 contract를 혼용하지 않았다. refilter가 원 준비 mask와 비교해 보존한1396쌍과 baseline 대비 보존1484쌍은 서로 다른 기준이다. 두 scene readback 및 training contract의 차이는 hand_collision뿐이다. 원 native setter/getter의 filter/friction/contact-offset exact assert와 4환경 readback을 재사용했다. 별도의 전체 native shape-property dump를 새로 수집한 것은 아니다.

PD/범위/codec·원 음악 판정/보상, seed7/index row1/2초 ramp/3초 onset/원 음길이와 tail, 엄지035·비선택 B·wrist v3는 같다. NN·trainer·checkpoint는 없다. 원 evaluator의 reference branch와 compact episode를 그대로 썼다. 두 조건 **선택4 target과 executed action 전체221끝점이 exact 동일**했다. 실제 상태가 달라 원 wrist feedback의 팔 target은 최대0.0521°, 요청은0.0526° 달랐다. 따라서 이것은 같은 손목 제어 아래의 총 반응 대조이며, 팔 명령 tape까지 고정한 직접 접촉쌍 압력 실험은 아니다.

새 baseline은 기존 v3 `index_reference`와 실제 비교했다. settings·trace metadata·전체4 evaluation이 같고, 저장된 공통20개 trace field가 모두 exact였다. 이는 이번에 확인된 별도 실행의 일치이며 사전에 보장하거나 과거 checkpoint를 현 소스로 다시 로드한 것이 아니다.

## 성과와 음원장: 전체8 시도

| 조건 | 달성 | clean | audible wrong | 물리/손목 실패 | contact_progress / best_clean_streak |
|---|---:|---:|---:|---:|---:|
| baseline | 0/4 | 0 | 0 | 0/4 | 모든 시도0 / 0 |
| refilter | 0/4 | 0 | 0 | 0/4 | 모든 시도0 / 0 |

각 원장의 missing은0.1703초, performance_paid는 원래값0.1000000015이며 settled=true다. 실패를 제외해 분모를 줄이지 않았다. 이번에는 native 실패가 없어 아래 env0 통계에서 censor된 끝점도0개다. 분석 코드는 실패가 있을 경우 해당 실패 끝점을 무실패 force/성공 해석에서 제외하지만 원 episode 분모를 보존한다.

## env0 audible 하중: 60Hz 끝점11개

단위N. 다른3환경의 세마디 힘이나240Hz 극값은 저장되지 않았으므로 주장하지 않는다.

| body | baseline p50 / p95 / max | refilter p50 / p95 / max |
|---|---:|---:|
| index1 | 73.402 / 73.405 / 73.406 | 0 / 0 / 0 |
| index2 | 0 / 0 / 0 | 52.688 / 52.692 / 52.693 |
| index3 | 0 / 0 / 0 | 0 / 0 / 0 |
| middle1 | 73.402 / 73.405 / 73.406 | 52.688 / 52.692 / 52.693 |

baseline index1의 ramp(0<t<2초,119끝점) p50/max는45.564/91.005N, 2≤t<3초(60끝점)는73.398/85.822N이다. refilter index2는 같은 두 구간에서26.802/62.377N, 52.681/52.692N이다. 음후31끝점에도 baseline index1 p50 73.403N, refilter index2 p50 52.688N이 남는다. 원래 ramp는 첫 tick부터 시작하므로 별도 pre-ramp 정지 표본은 없다. 전체 표는 `forces.csv`다.

audible에서 baseline index1+middle1 벡터합의 norm 최대는0N, refilter index2+middle1 합의 norm 최대도0N이다. 예를 들어 component별 중앙값은 baseline index1=[−13.069,−68.045,+24.229]N, refilter index2=[−4.783,−46.863,+23.600]N이며 middle1은 각각 반대다. 이는 **몸체별 순힘과 그 합**이다. 여러 접촉·다른 물체·제어 반응을 분리한 contact-pair sensor로 해석하지 않는다. 큰 힘이 나타나는 마디가 달라졌다는 관찰과 특정 새 쌍의 직접 접촉 확정은 구분한다.

## 실제 관절 추종과 남은 contact gate

audible 중앙값, 단위°. 축 순서는 MCP x/z, PIP, DIP다.

| 값 | MCP x | MCP z | PIP | DIP |
|---|---:|---:|---:|---:|
| 동일 target | 39.307 | 27.756 | 54.485 | 24.068 |
| baseline actual | 36.741 | 17.461 | 54.485 | 24.068 |
| refilter actual | 36.907 | 18.931 | 54.016 | 24.068 |
| baseline target−actual | 2.565 | 10.295 | −0.0005 | −0.0004 |
| refilter target−actual | 2.400 | 8.825 | 0.469 | −0.0004 |

MCP z gap은 약1.47° 줄었지만 큰 잔여가 있고 PIP gap은 약0.469° 생겼다. 실제 세마디 하중·각 추종이 함께 달라졌으므로 단일 목표각만으로 자세를 설명할 수 없다. 이것을 PD 부족·자산 충돌·특정 끼임의 단독 원인으로 확정하지 않는다.

| audible metric | baseline | refilter |
|---|---:|---:|
| nearest pad 거리 p50 / max | 1.353 / 1.393mm | 2.357 / 2.437mm |
| nearest signed height p50 | +1.323mm | +2.311mm |
| nearest normal cosine p50 | 0.985685 | 0.997801 |
| 원 position / position+facing | 11/11 / 11/11 | 11/11 / 11/11 |
| 원 assigned-distal loaded / positive / candidate | 0/11 / 0/11 / 0/11 | 0/11 / 0/11 / 0/11 |
| 원 wrong | 0/11 | 0/11 |
| wrist 위치오차 p50 / max | 0.205 / 0.221mm | 0.194 / 0.214mm |
| wrist 회전오차 p50 / max | 0.0409 / 0.0434° | 0.0368 / 0.0402° |

저장 snapshot을 원 CPU ShortEnvironment에 넣어 모든221×2끝점의 candidate/wrong와 nearest geometry가 저장값과 맞는지 확인했다. 여기의 원 geometry/facing gate는 기존 any-sample 조건이고 nearest 수치는 별도다. 서로 다른 sample을 가짜 same-point witness로 합치지 않았다. 두 조건 모두 기하 범위 안이지만 **실제 할당 distal3 load가0**여서 positive/candidate가 없다. 큰 proximal/middle body force를 distal load로 바꾸어 성공 처리하지 않았다. ramp의 wrong은13→25끝점이나 이것은 실제 음창의 wrong0과 다른 시간 구간이며 `gates.csv`에 분리했다.

## 기존9보상 지급 확인

조건별4시도 평균이다. 새 계수·힘 cap·보상항을 추가하지 않았다.

| 원 보상항 | baseline | refilter |
|---|---:|---:|
| song_left_approach | −0.378906 | −0.383905 |
| song_left_contact | 0 | 0 |
| song_clean_hold | 0 | 0 |
| song_left_success | 0 | 0 |
| song_wrong_press | 0 | 0 |
| song_performance_deficit | −0.100000 | −0.100000 |
| song_finger_standby | +0.055478 | +0.055539 |
| song_thumb_support | +0.033826 | +0.033898 |
| action_change | 0 | 0 |
| 실제 총 reward 평균 | −0.389602 | −0.394468 |

8개 원 episode에서9항 합과 실제 total reward의 차이는 최대 약2.16e−7로 float32 누적 오차 범위였다. 지급 총합을 힘이나 성공으로 재분류하지 않았다. 고하중 패턴이 달라져도 clean/contact/success 지급은 양쪽0이고 물리·손목 실패도 양쪽0이라는 관찰만 남는다.

![env0 actual comparison](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_proximal_pair_isolation_v1/analysis/results_v1/comparison.png)

이 finite-control 개입은 proximal1 순힘 패턴을 크게 바꾸는 데 관여했으며, 다른 마디의 큰 하중과 distal 접촉 미확보는 남았다. **단일 pair 제외를 압현 개선으로 채택할 근거는 없다.** 고정 기타·고정 엄지·비선택 B·손목 teacher 조건에서 얻은 결과를 자유손 mainJ33·전곡 원인으로 확대하지 않고, 허용 손가락 충돌을 영구 제거하지 않는다. proximal 자산·접근 경로·비선택 B와 실제 자세의 관계는 별도 원인 분리 대상이다.

원자료는 보존했다. CPU 분석만 수행했고 기존 producer/준비봉인/활성 source 및 GPU를 변경하지 않았다. 상세 원장·gate·벡터·통계는 `comparison.json`, 입력 SHA·실제 launcher·보상 검산은 `verification.json`, 전체8 시도는 `episodes.csv`에 있다.
