# 상완 축30/40% 목표 V4 변경 사전 검수

요약 판정: **수정 권장**. Critical: 0 / Warning: 1 / Suggestion: 0. V4 새 diff만 검수했고 source/native를 실행하지 않았다. 정상 비겹침 후보의 목표·gate·설정은 계획과 일치하며 아래 Warning은 거절 후보 저장의 수치 처리 문제다.

## Critical

없음.

## Warning

- [search_right_arm_wrap_upright_v4.py:124](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v4.py:124): `contact_normal`을 길이 검사 없이 정규화한다. 사용한 capsule–convex query는 axis가 mesh 안에 있는 경우 distance0/negative gap도 반환할 수 있어 이 거절 후보에서0÷0으로NaN이 생길 수 있다.127행의 row를 `allow_nan=False`인 save로 저장하면 전체 CPU batch가 중단된다. 길이>epsilon일 때만 정규화하고 undefined면 null/valid flag로 기록·normal gate를 거절하도록 처리한다. 기존 source clear/min-gap gate를 통과한 정상 후보의 normal 정의는 맞다.

## 나머지 변경 확인

- [search_right_arm_wrap_upright_v4.py:82](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v4.py:82): axis_local은 XML capsule의a→b축 .30/.40 분율이고 body pose로 world에 변환해4000 잔차를 준다. 새로운4개 label은 relief12/20×fraction30/40으로 서로 다르다. 기존 body 목표·G inset10/25mm·Hip 높이·bounds는 유지한다.
- [search_right_arm_wrap_upright_v4.py:83](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v4.py:83): Gy−.52의 profile t는0.743923544로0..1 범위이며 기존body profile 좌표식과 같다. 반폭0.189622377m/radius0.0521m에서 목표G_X는−0.242522377m이다. G_Z는 실제 collision body vertex bbox 중간값이고 목표W는 현재 이동한gp/gr를 사용한다. 원래 기타 위치를 쓴 목표가 아니다.
- [search_right_arm_wrap_upright_v4.py:126](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v4.py:126): 요청fraction과 별개로 실제 closest fraction .20..45, source separation normal의−G_X≥.7, actual axis goal error≤15mm를 수락에 사용한다. source 근접/clear·trunk/forearm/waist/natural/model/finger 등 기존 gate와45% metadata도 유지된다. source normal을 native cooked contact normal로 설명하지 않는다.
- [search_right_arm_wrap_upright_v4.py:131](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v4.py:131): Thorax10N/4mm·상완20N/8mm 설정은 계획 및 기존 지원 쌍과 같다. wrapperV2/분석기V3는 SHA 불변이다. 이후 cap 표기는 기존 `Thorax_cap_N=max(reference)` 오표기 caveat를 피하고 실제 body별값으로 기록한다.

V4 source AST 통과. 신규 leaf/self 및all A Python before/after pin 방식은 그대로이며 이미 소비한 원본을 수정한 변경은 아니다. 전체 fitting·closest fraction·실제 접촉/유지 결과는 후속 검증한다.

검수 SHA256:

- Plan V4: `ea4fcdb93473f90da5a4f5c8d6dfffd006bbc0b3c843ade21785116ff07d5292`
- Source V4: `c939b5a0debee7f1549f60aa5b3f0ea4958fbc1cd35cd78659c371c597f22e5a`
- unchanged wrapperV2: `773f7f982c5f8dc5075839bfe373b75ae184210ddfa9cd45fec920696a504ee1`
- unchanged 분석기V3: `5d800036446619eb8459aad2ee99b9e88cf1fe7895a8d72b67d807f8fe8ab07b`

지정된 이 검수 기록만 생성했고 다른 담당자 파일을 수정하거나 되돌리지 않았다.
