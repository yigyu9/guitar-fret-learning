# upright·오른 근위팔 접근 V2 사전 변경 검수

요약 판정: **문제없음**. 현재 수정본 기준 **Critical: 0 / Warning: 0 / Suggestion: 0**. Source V2 CPU 탐색으로 진행 가능하다. V1 전체 검증은 반복하지 않고 초기 기타 이동·높이 보정·상대 목표·새 분석기 변경만 검수했다.

검수 중 지적한 source elbow 거리의 이전 bbox 중심 사용과 계획 첫문단의 “기타초기p/q 유지” 충돌은 root가 미실행 V2에서 수정했다. 현재 미해결 항목은 없다.

## 확인 근거

- [search_right_arm_wrap_upright_v2.py:60](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v2.py:60): `-front_axis*inset_m`은 휴머노이드 수평 앞축 반대15/40/55mm의 초기 기타 이동이다. `down`은 world Z 하강량이며 fixed Hip 원형상에 대한 양쪽 최소 gap0.3mm를 brentq로 맞춘다. 새 함수의 bracket−25/+120mm에서 세 입력 모두 부호가 바뀜을 확인했다. float32 기타 root 위치로 변환한 뒤 actual delta를 다시 계산해 기록한다.
- [search_right_arm_wrap_upright_v2.py:80](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v2.py:80): 오른 elbow 목표는 baseline origin+실제 G delta이고 RH palm·왼 wrist는 동일 초기 G translation의 상대 위치를 재맞춘다. 기타 회전이 같으므로 방향 목표는 유지된다. body12/20/24°·bounds·Chest30mm/두 근위 블록/전완/waist/full source clear/모델 수락 gate는 V1과 같다. 이것은 초기 배치 변경이며 runtime 기타 힘/고정/pose 덮어쓰기 변경이 아니다.
- [search_right_arm_wrap_upright_v2.py:114](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v2.py:114): 수정된 after elbow→bbox 거리는 현재 `gp+gr.apply(centre)`를 쓰고 before는 baseline 중심이다. 기존 world 접근축 투영과 goal error는 별도 field로 기록한다. 초기 이동량은 `toward_body_m` 요청값과 실제 `guitar_delta_W_m`으로 구분한다.
- [analyze_right_arm_wrap_upright_v2.py:72](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_upright_v2.py:72): 실제 초기 root translation을 두 기준별로 기록하고 G39의 같은 translation residual<3µm 및 회전 오차<1e−5rad를 검사한다. 이전처럼 전체 위치 변화 자체를<3µm로 거절하지 않는다. 위치 변화 magnitude·translation residual·rotation 차이를 각각 저장하므로 새 초기 이동과 강체/회전 보존을 구분한다.
- 입력 before/after pin·실제 XML mesh69/union70/human37 수집 로직은 그대로다. 새 V2 source/분석기 Python은 `A.glob('*.py')` 목록에 포함된다. native 초기값은 새 source 예측 G39와 대조하는 기존 runner 계약을 유지한다. Chest raw wrapper V1은 변경되지 않았다.

## 검증과 제한

새 source/분석기 AST 통과. 높이 함수는 brentq bracket 양끝6개 값만 읽기 전용 검사했고 전체 root solve·pose fitting·source audit/native/producer를 실행하지 않았다. 검수 시 `search_v2` 폴더는 없었다. 실제 높이 수렴·float32 후 waist gap·전체 수락과 actual 접촉/유지는 후속 결과에서 검증한다.

## 검수 SHA256

- Plan V2: `d3cb22903d40b1d085d75b0c1638082264589aedaabe97223c5eedb62ce15f81`
- Source V2: `bb9c3976d72728bfda2d5acc655b6e4fc6357beb48872da85c1cb96ba7957097`
- 분석기 V2: `f5a639c327db4c1b9484d4629bccb81bb97d1cceba377f01eb742a3e01b8dade`
- 보존 Source V1: `164945ef095c695e099e54d9713aa4b5c95e6653033360343de46e018751a9e0`
- 변경 없는 Chest wrapper V1: `0cd511087ba0db3bb64fea9c9a5be605474dda2cce57753a7afcb5cb2358fc0a`

지정된 이 검수 파일만 생성했으며 다른 담당자 파일을 수정하거나 되돌리지 않았다.
