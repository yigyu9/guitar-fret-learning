# 중간 선택 모델·보존 체크포인트

생산 기본값을 변경하지 않는 검증된 연구 산출물 목록이다. 모든 경로·실제 SHA·평가 보고서·영상 검사는 [selected_models.json](selected_models.json)에 기록했다.

## A에서 선택한 모델

|손가락·목표|학습 갱신|A 지원 평가|자유 v9 평가|자유 평가 clean 평균(실패0점,초)|영상|
|---|--:|--:|--:|--:|---|
|검지·3줄4프렛|100|32/32|32/32|2.496484|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/index_A100_free_v9_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/index_A100_free_v9_fullbody.mp4)|
|중지·3줄6프렛|200|32/32|32/32|2.500000|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/middle_A200_free_v9_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/middle_A200_free_v9_fullbody.mp4)|
|약지·2줄7프렛|200|32/32|32/32|2.500000|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/ring_A200_free_v9_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/ring_A200_free_v9_fullbody.mp4)|
|소지·3줄9프렛|200|32/32|32/32|2.500000|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/pinky_A200_free_v9_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/pinky_A200_free_v9_fullbody.mp4)|

A 체크포인트는 정렬·지원 조건에서 학습했다. 검지는 fresh100회 모델이며, 나머지 세 모델은 fresh100회 뒤 같은 A로 엄격히 재개한200회 모델이다. 위 영상은 동일 가중치를 0업데이트로 자유 v9/J33에 내보낸 실제 native 재생이다. 영상은 환경0의 한 에피소드이며 표의32환경 평가와 구분한다.

[네 손가락 영상 모음](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/four_fingers_A_free_v9_comparison.mp4)은 독립 재생 네 개를 배치한 합성본이며 동시에 네 손가락을 제어한 정책 영상이 아니다. 공개 MP4 9개 모두 source/publication SHA와 ffprobe를 확인했다.

## B0는 별도로 보존

|손가락|B0 평가|실패|평균 safe clean(초)|체크포인트|
|---|--:|--:|--:|---|
|검지|32/32|0|2.433854|[initial](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/index_B_seed7_v1/100/train/J/initial.pt)|
|중지|32/32|0|2.500000|[initial](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/model_only/middle_B0/J/final.pt)|
|약지|32/32|0|2.500000|[initial](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/model_only/ring_B0/J/final.pt)|
|소지|27/32|0|2.109375|[initial](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/model_only/pinky_B0/J/final.pt)|

B0는 추가 B 학습이 없는 초기 모델이다. 원래 A 모델과 active mask 외 전체 모델 tensor가 정확히 같은지 CPU에서 대조했다. B0의 지원·초기 분포 평가이며 정식 B 승급이나 학습 개선을 뜻하지 않는다.

## 처음부터 full33으로 학습한 대조군

|구분|갱신|안전 달성|평균 safe clean(초)|체크포인트|영상|
|---|--:|--:|--:|---|---|
|기존 latent_mean 최고 모델|100|32/32|2.500000|[checkpoint](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/index_full33_seed7_v1/100/train/J/final.pt)|아래 참조|
|마지막·기존 latent_mean 실패 대조|200|0/32|0.000000|[checkpoint](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/index_full33_seed7_v1/200/train/J/final.pt)|아래 참조|

full33은 601열·33축·v9에서 처음부터 학습한 별도 절차이며 A→B 모델과 혼합하지 않는다. 200회는 100회 모델의 엄격한 재개 결과다. 최고100회와 마지막200회를 각각 보존하며, 아래에 실제 native 실행 규칙별 영상을 기록했다.

## 같은 full200 체크포인트의 실행 규칙 비교

200회 체크포인트의 실패 표기는 **기존 deterministic latent_mean 실행의 0/32**에 한정한다. 아래는 추가 학습 없이 같은 체크포인트·원래 Gaussian μ/σ·32개 초기 q105/hold를 유지하고 실행 규칙을 바꾼 진단이다.

|실행 규칙|안전 달성|평균 safe clean(초)|실패 에피소드|
|---|--:|--:|--:|
|기존 latent_mean|0/32|0.000000|0|
|원래 Gaussian 확률 표본, 고정 가중치|31/32|2.491927|0|
|normalized_action_mean|0/32|0.000000|0|
|requested_angle_mean|32/32|2.500000|0|

새 latent_mean 기준 재현은 기존 성과·9항·할인 reward/cost와 같고, trace의8개 배열도 bitwise 동일함을 독립 확인했다. 모든 행은 첫 에피소드32개 전체를 분모로 삼으며, 모델 SHA·실제 초기 q/hold 행·native provenance·입출력/helper 핀·39축 codec을 대조했다. reward γ=0.99와 cost γ=1.0을 구분했다. full100 requested_angle_mean도 같은 초기 q/hold에서32/32·clean2.5초를 유지했다.

requested_angle_mean은 비대칭 관절 범위를 반영한 **평활화·속도 제한 전 요청각의 기댓값**을 실행하는 검증 후보이다. 실제 물리 응답의 기댓값을 뜻하지 않는다. 핵심7조건과 추가 A200 세 손가락의 새 baseline/요청각 pair 검수는 완료했다. 중지·약지·소지는 두 규칙 모두32/32·clean2.5초이며 실패0이었다. 기존 저장 모델에 대한 제한된 회귀이며 일반적인 무손상 보장이나 생산 기본값 변경으로 해석하지 않는다. full33의 새 실행 규칙별 native 영상8개는 source/publication/공개 MP4 SHA와 ffprobe를 검증했다. 실제 증거 경로·SHA·시점은 JSON의 execution_rule_comparison과 expected_angle_review_snapshot에 기록했다.

## 독립 seed17의 full33 모델

|모델|latent_mean|requested_angle_mean|원래 Gaussian 표본|각 실행의 평균 safe clean(초)|
|---|--:|--:|--:|---|
|최고100회|32/32|32/32|28/32|2.500000 / 2.500000 / 2.474740|
|마지막200회|0/32|0/32|27/32|0.000000 / 0.000000 / 2.130990|

각 실행은 실패 포함32개 최초 에피소드이며 물리·손목 실패는 모두0이었다. 모델과 평가 CP SHA, 실제 초기 q/hold 대응, seed만 바뀐 설정 및100→200 strict 모델·두 Adam·전체 RNG 복원을 검증했다. 최고100회와 마지막200회를 별도로 보존한다. seed17의200회에서는 요청각 기댓값도 실패하므로 Eθ는 보편적 해결책이 아니다. 기존 A/B0를 교체하지 않으며 seed17 영상은 대기다.

## B 지원을 유지하거나 제거한 별도 진단

|조건|기존 latent 안전달성/clean초|지원 유지 requested-angle 안전달성/clean초|clamp 제거 latent 안전달성/clean초|
|---|---|---|---|
|검지 B0|32/32 · 2.433854|32/32 · 2.438542|32/32 · 2.436198|
|검지 B100|32/32 · 1.888672|32/32 · 1.887630|32/32 · 1.897005|
|소지 B0|30/32 · 2.343750|30/32 · 2.343750|30/32 · 2.343750|
|소지 B100|21/32 · 1.640625|21/32 · 1.640625|21/32 · 1.640625|

두 진단은 독립 비교다. 요청각 평균 진단은 B16·초기후보·팔 press clamp를 유지한다. clamp 제거 진단은 같은 저장 B에서 팔 press clamp만 제거한다. 각 pair의 같은 CP·실제 초기 q/hold·32개 분모를 확인했으며 소지 B100의 새 latent baseline도 기존 성과와 정확히 재현했다. 실패는 모두0이었다. 위 지표는 비할인 episode 합이며 per-step 할인 수익을 계산한 자료가 아니다. 소지 B0의 이 고정4242 후보 평가는 위 보존 목록의 과거27/32 영상 평가와 다른 기록이므로 바꾸어 쓰지 않는다. 어느 진단도 B 정식 승급이나 새 학습 성공으로 간주하지 않는다.

seed17 fresh 목표4축 분산0.1 실험은 **완료**했다. 원본과 분산0.1 모두100회는32/32·clean2.5초,200회는0/32·clean0초이며 평가 실패는0이었다. 실제 초기 전체 모델·CPU/CUDA/Python/NumPy RNG,100→200 모델·두 Adam·전체 RNG 복원 및 분산 외 설정 동등성과 native 감사를 확인했다. 기존 최고100회보다 개선되지 않아 대체 모델로 선택하지 않는다. Variant 공식 평가는 q/hold32를 별도로 캡처하지 않아 실제 전체 초기 상태 exact 대응이라고 표현하지 않는다. 공통 비교는 비할인 episode 합이다. 첫 물리전 경로 준비 실패 출력·로그는 보존하고 정책 실패로 집계하지 않는다. 새 full33 native 영상은 다음 네 조건에서 완료했다.

## full33 실행 규칙별 native 영상

|조건|영상 env0 달성|clean 비율|영상|
|---|--:|--:|---|
|full100_latent_mean|1|1.000000|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full100_latent_mean_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full100_latent_mean_fullbody.mp4)|
|full200_latent_mean|0|0.000000|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full200_latent_mean_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full200_latent_mean_fullbody.mp4)|
|full200_stochastic|1|0.996667|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full200_stochastic_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full200_stochastic_fullbody.mp4)|
|full200_requested_angle_mean|1|1.000000|[손](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full200_requested_angle_mean_hand.mp4) · [전신](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/seven_hour_v1/full200_requested_angle_mean_fullbody.mp4)|

각 영상은4환경 native renderer의 환경0 한 에피소드·6초·180프레임이다. 고정4242의32환경 평가와 초기화/분모가 다르므로 영상 성공을32/32로 표현하지 않는다. 확률 영상도 한 표본이다. CP·가중치·물리·source pin이 보존되고0학습임을 확인했다. 요청각 평균 영상은 배포 실행 규칙을 바꾼 진단이며 원래 latent_mean 실행과 구분한다. 기존 A/합성9개와 새8개를 합쳐 공개 MP417개의 source/publication SHA·인코딩 정보를 확인했다.

## 고정 full200 탐색 그룹 진단

|확률 실행 그룹|seed7 안전 달성|seed17 안전 달성|
|---|--:|--:|
|원래 전체33축|31/32|27/32|
|목표 손가락4축만|32/32|16/32|
|왼팔12축만|24/32|10/32|
|나머지 손가락17축만|0/32|0/32|

각 seed는 같은200회 CP·실제 초기 q/hold와 원래33축 Gaussian 난수 소비를 유지했다. 전체33축 baseline의 trace8개 열·initial 배열은 기존 frozen 기록과 정확히 재현됐다. 최초32개·실패 포함·9항·rewardγ.99/costγ1을 확인했고 두 seed gate가 모두 통과했다. 전체33축만 원래 확률 정책이며 나머지는 선택 그룹 외 활성축을 latent mean으로 둔 hybrid 진단이다. 기록 logp는 원래 Gaussian에서 선택 latent의 값으로 hybrid 분포 밀도나 학습에 사용하지 않는다. 목표/팔 탐색에 의해 성공하는 경로를 확인했으나 효과를 합산하거나 독립 기여율·보편 해법·새 학습 개선으로 해석하지 않는다. 기존 선택 모델과 생산 기본값은 유지한다.

## 해석 범위

실패도32개 평가 분모에 포함한다. 각 손가락의 줄·프렛이 달라 난이도를 직접 비교하지 않는다. 같은 명목 초기 자세의 반복이며 새 초기 자세·곡·목표 일반화나 실제 음향 압현을 인증하지 않는다. 현재 보상·기하·하중 기반 판정에 따른 중간 연구 결과이며 생산 코드·기본 체크포인트를 변경하지 않았다.

기준 runtime 3,148개 파일의 봉인 SHA를 재검증했다. 다른 학습·분석·봉인 파일은 수정하지 않았다.
