# PC2 코드·보상·포화 현상 추가 검토

검토 범위는 공유본의 읽기용 코드와 원시 JSON/JSONL이다. 공유상태 ready=true와 검토 프롬프트를 확인했다. 원본 코드를 import하거나 모델을 로드하지 않았고, GPU·평가·학습을 실행하지 않았다. 새 파일은 이번 PC1 추가 검토 폴더에만 작성했다. 현재 PC1 실행 버전과 같은 구현이라고 가정하지 않았다.

## 판정

REPORT의 핵심 구분은 타당하다. **중지의 정밀 위치 실패, 지원 축 요청 포화, 평가 반복 민감도는 관찰 사실이고, 특정 축 포화나 potential 설계가 실패의 원인이라는 주장은 아직 가설이다.** 실제 지급 보상과 원장 사이의 유의미한 누락·중복은 독립 검산에서 발견하지 못했다. 기존 성공 기준을 낮추거나 공유 코드를 변경할 근거로 확대하지 않는다.

## 1. 실제 보상 지급 독립 검산

이번 검산 코드는 `tools/audit_reward.py`이며 공유 분석 도구를 import하지 않고 표준 라이브러리로 직접 원시 행을 읽는다. 완료 원장의 첫 episode ID를 각 환경에 연결해 후속 episode를 제외했다. 상세 수치는 `code_reward_audit.json`이다.

신규 N32/N128 × 반복1/2/3의 여섯 보상 원문을 모두 검산했다.

- 모든 환경의 첫 episode는 60Hz 지급 435개다.
- 9항 합과 실제 반환 보상 차이 최대는 **9.2242772e-8**이다.
- 각 항의 첫 episode 합과 완료 원장 counter 차이 최대는 **4.3511391e-6**이다.
- gamma0.99를 지급 순서대로 적용한 접근 항 할인 합은 전체 범위 **−0.958014625..−0.958013795**다.
- N128 repeat1의 env0에서 첫 전이로 추정한 초기 Phi는0.9580151641이다. 후속434전이의 실제 endpoint Phi 대 보상 차이 최대는 **7.6293945e-8**, 종료 정산을 포함한 telescoping 잔차는 **1.0110664e-6**다. 초기 Phi는 직접 기록된 t0 상태가 아니므로 초기화 동일성의 독립 증거로 사용하지 않는다.

코드 근거: 읽기용 `guitar_learning/gpu/environment.py:1253`에서 실제 실패/시간 종료의 nextPhi를0으로 만들고 다음 행에서 gamma*nextPhi−beforePhi를 지급한다. `finger_skill_environment.py:500`의 실제 `_reward_components`는 legacy 가중치 묶음을 다시 쓰지 않고 정확히9항을 반환한다. 접촉·유지·달성은 원시항에0.5, 오압현은0.15를 곱하며 수행 부족과 접근·대기·엄지·행동항은 해당 실제 값을 읽는다. `로그분석/tools/observe_evaluate.py:16`은 이 함수의 반환 텐서를 clone하여 저장하므로 보상 counter 차이만으로 지급을 재구성한 자료가 아니다.

따라서 접근 항의 비할인 음수 합이 큰 것만으로 “음수 보상이 성공을 압도했다”거나 정책 경사를 지배했다고 주장할 수 없다. 종료를 포함한 완전한 할인 potential 합은 고정 초기 Phi에서 상쇄된다. 이것이 유한 H32·근사 critic의 중간 학습 신호까지 영향이 없다는 뜻도 아니다. 실제 rollout의 관측·latent·value·미니배치가 없어 항별 gradient norm/cosine은 복원하지 못한다. 새6평가 보상 시간 분해는 기존12/128 평가의 보상 시점 자료를 대체하지 않는다.

## 2. 준비·압현 중 대기 보상

읽기용 `finger_skill_environment.py:337`의 `_finger_preparation`은 natural target valid인 각 손가락의 실제 `standby_reward_gate`를0으로 만들고 그 gate로 `per_finger_rate`를 재계산한다. 관측에 쓰는 legacy gate는 별도 보존된다. 따라서 관측 gate가1이거나 B구간 전체 대기 보상이 양수라는 사실은 중지에게 대기 보상을 지급했다는 뜻이 아니다.

N128 repeat1 env0의 첫 episode에서 준비 유효 손가락 **1919개 끝점**을 독립 확인했고, 실제 standby weight 또는 standby rate 비영 사례는 **0**이다. 이 검산 범위는 env0에 기록된 손가락별240Hz 진단이다. 모든 환경 손가락별 gate까지 저장·검증했다는 주장은 하지 않는다. 실제 지급은60Hz이며240Hz gate 표본을240Hz 보상으로 해석하지 않는다.

## 3. L_Thorax_y 요청 포화

읽기용 `tool/experiments/natural_press.py:65`는 reference를 중심으로 양·음 범위를 나누어 정규화한다. `:135–143`은 catalog hold를 정규화하고 float32 clamp±0.999999 후 atanh로 정책 bias를 초기화한다.

원시 initial_catalog에서 해당 native 관절은40번이며 action index목록의 두 번째다. reference≈9°, hold≈10°, upper≈10°다. 같은 실행의 `native_reference_v2/reference_trace60.json`에서 B 발음 요청은 **8.235896518°**로 일정하다. 실제 float32 clamp는0.9999989867210388, atanh bias는 **7.247732639312744**이다. float64 atanh(0.999999)=7.2543286과 혼동하면 안 된다.

float32 bias에서 연속 tanh 함수의 국소 Jacobian을 다시 계산하면 span1° 기준 **2.0265577e-6°/latent**, latent std0.05의 선형 근사 요청 std는 **1.0132788e-7°**다. REPORT의2e-6/1e-7 근사는 약1.3% 차이로 핵심 결론을 바꾸지 않는다. 10° 부근 rad float32 한 ULP는약 **8.5377365e-7°**다. 이는 연속 선형 근사와 출력 양자화의 규모 비교이고, float32 tanh·요청각의 정확한 이산 분포를 측정한 값은 아니다.

원시12개 trace(두 seed ×100/200/300회 ×mean/sampled)의 B 발음 env0 끝점을 별도로 재집계했다. 각360개 표본에서 |action|≥0.98 비율은100%였고 적용각은9.999999709°로 일정했다. 요청각도11개 실행에서는 같은 상수였으며 seed7/u200/sampled만9.999998855..9.999999709°의 한 ULP 폭을 보였다. 따라서 모든 탐색 요청이 문자 그대로 완전히 일정하다는 표현보다 “float32에서 사실상 압축됨”이 정확하다. 상세한 실제각 평균은 JSON의 `raw_saturation.rows`에 보존했다. 이는 기록된 대표 환경의 결과이며 전체 환경 축별 행동을 측정했다는 뜻은 아니다.

대표 env0 B의 실제 q가 seed7≈9.188°, seed17≈8.385°인 사실은 해당 축 정책 요청 탐색이 회복됐다는 증거가 아니다. 실제 q는 동역학·접촉·다른 축의 상태에 따라 바뀔 수 있다. 또한 교사가8.236°를 썼다는 사실만으로 이 축 하나가 정책 실패의 원인이라고 결론 낼 수 없다. fresh 초기 bias 한 축만 내부로 이동하는 단독 실험이 적절하며 기존 모델 metadata나 bias를 수정한 재개는 동일 비교가 아니다.

## 4. 접촉 표본과 wrong source의 해석

읽기용 `gpu/contact.py:622–642`의 최근접 접근 표본은 하중·법선과 무관하게 거리로 선택된다. 반면 positive는 **동일 표본에** lateral≤3mm, 프렛 셀 내부, signed height−1..3mm, cosine≥0.1이 모두 맞는 표본이 전체 유효 패드 중 하나라도 있는지 검사한 뒤 담당 몸체 loaded를 결합한다. 따라서 접근 표본의 높이만 좋아지거나 normal이0.1보다 높다는 이유로 접촉 성공을 주장할 수 없다. `facing_geometry`에는 위치 조건도 포함되어 있어 facing0은 독립적인 방향 실패 증거가 아니다. loaded는 몸체 합력 기반 bool이며 올바른 줄 압력이나 현에 가한 N값이 아니다.

읽기용 `gpu/contact.py:935–981`에서 원인 flags는[환경,목표,몸체,cause]지만 fret min/max는[환경,목표,몸체]다. `environment.py:1175–1192`는 실제 발음 overlap에 맞춰 cause 시간을 적분하고 cause축을 합친 몸체별 min/max를 보존한다. REPORT의 “중지 own_wrong_fret와 own_wrong_string 각각1.5초, 중복 가능; 몸체 범위5..6” 표현은 타당하다. 이를 같은 시점·같은 줄·같은 cause의 witness로 결합하거나 두 원인 시간을 더해3초로 만들면 틀린다.

원시 candidate/effective, audible overlap clean 적분,0.6초 연속 달성,1.5초 전체 유지는 구분해야 한다. 발음이 끝난 raw 접촉 중복 자체는 오류가 아니며 이 사례에서 분석기의 기존 assert가 실제 평가를 탈락시켰다고 확인된 것도 아니다.

## 5. 검토 한계와 다음 우선순위

원시 지급 보존, gate, 포화 초기화, 참조 요청각, 표본/출처 계약의 보고서 해석은 지지한다. 전체 checkpoint identity를 이 읽기용 사본에서 재로드 검증하지 않았고 원래 strict-loader 실행 증거와 파일 보존 자료를 provenance로 취급했다. 검증을 우회하거나 읽기용 사본을 실행 패키지로 만들지 않았다.

단독 실험은 평가 반복 최초 차이 분리 → 한 축 bias 초기화 → 같은 표본의 근접 기하 potential 비교 순서가 적절하다. 두 번째·세 번째를 동시에 바꾸면 포화 해소와 reward 정밀도 중 어느 개입이 작동했는지 알 수 없다. 평가 범위가 큰 상태에서는 작은 성공률 차이보다 witness 기하·요청 범위·초기 상태의 직접 기전 수치를 먼저 확인해야 한다. 최종 채택은 기존90% 수행 및1% 이하 실패 기준을 유지한다.
