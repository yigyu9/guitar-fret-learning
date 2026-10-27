# Source3 수락·거절 및 native 입력 검수

요약 판정: **문제없음**. **Critical: 0 / Warning: 0 / Suggestion: 0**. Source3의12°/20° 수락 candidate는 native 초기 검증에 사용할 수 있고24°는 거절 유지한다. 이 판정은 Source 계약 검증 결과로 실제 native 완료/부분 종료와 구분한다. 검수자는 native를 실행/재실행하지 않았다.

## 결과와 입력

Source3의760개 input SHA가 모두 현재와 같다. Source1/2/3은 각각3행이며 수락0/0/2개, 전체9행 중2수락·7거절이다. Source3 `native_runs=0`은 CPU producer의 집계이며 별도로 시작한 native 진행을0회라고 소급하는 값이 아니다. 원본 source/계획/거절·기존 버전은 보존했다.

저장된 Source3 원자료로 모든 gate를 재계산하고 body FK 목표 회전 오차도 독립 계산해 수락/거절과 일치했다.

| 후보 | 실제 Chest proxy° | body 목표 최대오차° | Thorax gap mm | 근위45% 상완 gap mm | Chest gap mm | 전완 gap mm | 판정 |
|---|---:|---:|---:|---:|---:|---:|---|
|12°/inset10mm|41.412322|0.00000150|20.002366|0.802901|50.581994|22.171490|수락|
|20°/inset25mm|33.412323|0.00000168|26.267663|0.811453|59.362039|20.718942|수락|
|24°/inset35mm|29.412323|0.68384844|27.160994|0.811072|60.014840|20.258754|거절|

24°는 Chest 목표만 맞았어도 Torso/Spine/Chest 전체 목표 최대오차0.683848°가0.4° 한계를 넘는다. 다른 gate는 통과했지만 이 후보는 사용할 수 없다.12°/20°의 Torso/Spine20mm·Chest30mm·upper45 negative G_X/0.05~4mm·전완12mm·waist/full source clear·natural/head/left wrist/finger42·모델 한계는 모두 통과한다. Thorax 최대간격/필수 접촉 조건은 없다.

## 후보 schema·강체 이동·제어 설정

- [search_right_arm_wrap_upright_v3.py:119](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v3.py:119):12°/20°의 `proximal_upper_arm45_witness`와 호환30/65 키가 exact하며 fraction=.45·legacy note가 있다. 기존 controller의30 키 명칭을 실제30% 측정으로 설명하지 않고 새 분석기의45%를 사용한다.
- 초기 기타 actual world delta는12°에서`[+0.386536,-9.992525,-0.540018]mm`,20°에서`[+0.966340,-24.981320,+1.030087]mm`다. 같은 회전의 G39는 baseline+이delta와 최대 residual2.24e−16m/회전0rad 차이다. 새 초기 위치를 이전과 동일하다고 쓰지 않는다. waist gap은두 수락 후보 모두약0.299986mm다.
- 기준 actual 초기에서 독립 재구성한 FK와 수락 candidate 예측의 최대차이는 위치 <3.39e−16m/회전 <7.22e−16rad다. candidate joint각/audit row/contract float32 q와 config 연결이 exact하고 body±.25·양팔±.6·head±.5 모델 범위 및 finger42 exact가 유지된다. R_Elbow_y 모델 한계 여유는12°47.0877°/20°50.5330°로±5°보다 크다.
- [search_right_arm_wrap_upright_v3.py:123](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v3.py:123): config 전체는 baseline에서 candidate 경로/SHA, amplitude0, Thorax10N/4mm·상완10N/4mm만 바꾼 값과 exact하다. body9 PD/gravity·left 추종·model effort cap·48POSITION·free guitar/strap OFF를 추가 변경하지 않았다.10N은 virtual human request cap이며 측정 접촉힘이 아니다.

## 후보 SHA256

| 후보 | candidate | config |
|---|---|---|
|12°|`4eed818be22e0e402a5653a7c18b94a1ea1c5fd74a087f479e8ef819e172f065`|`4d0800e1cc7aa6aedd807254ec1e67f4790a100be3de1b1c301948578043e642`|
|20°|`af58ca64fad31f03f0e631b934fdcf81b892257dff4b655c320cfb8084c1c681`|`d124f695ae741a72b34d5448726085301682f3fb9b2534d6e6a08ca048288455`|

Source 결과 수락은 cooked 접촉·상완의 지속 감싸기·trunk 접촉0·정지/파동 유지 성공 인증이 아니다. 실제 초기 상태와 readonly Chest/trunk endpoint·명령/자세/기타/waist·45% 접촉은 native 결과에서 확인한다. 지정된 이 검수 기록만 생성했고 source/root/다른 출력은 수정하지 않았다.
