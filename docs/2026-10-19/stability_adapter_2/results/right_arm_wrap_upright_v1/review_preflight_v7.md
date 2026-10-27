# V6 변경 사전검수

요약 판정: 문제없음. V5→V6 변경만 검수했으며 CPU/native 재실행 및 원본 변경은 하지 않았다.

Critical: 0

Warning: 0

Suggestion: 0

확인 근거:

- [source:59](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v6.py:59): 추가20°·몸쪽25mm·축40%/55% 두 후보로 제한한다. [계획:5](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_UPRIGHT_PLAN_V6.md:5)과 일치한다.
- [source:75](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v6.py:75): 실제 baseline의 오른팔 12 DOF 이름으로 계산해 Shoulder/Elbow 각각3 DOF만 ±0.9rad, Thorax/Wrist 6 DOF는 ±0.6rad임을 확인했다. 모델한계 교집합과 Elbow_y ±5° 여유를 유지한다. 확대는 초기 CPU fitting bounds에만 적용된다.
- [source:129](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v6.py:129): V5 수락 gate가 그대로이며 Torso/Spine20mm·Chest30mm·forearm>12mm와 full witness/normal/axiserror/natural/waist/left/head/finger42/모델한계를 약화하지 않았다. root/lower와 몸통 fitting 범위도 변경 없다.
- [source:130](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v6.py:130): 실제 초기 탐색 범위를 `right_initial_range_rad`에 남긴다. [source:134](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v6.py:134)의 상완20N/8mm·Thorax10N/4mm, 정적 elbow amplitude0 및 runtime 연결은 변경 없다.
- [source:24](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v6.py:24): 새 source/계획/출력 경로로 분리하고 기존 입력 사전 핀 및 종료 SHA 검사를 유지한다.

문법 AST 통과. zero-normal 거절/JSON 저장도 유지된다. 소비된 `search_v6/inputs_before.json`의 source/계획 SHA와 현재 파일이 일치한다. 실제 후보 수락 및 cooked 물리 유지 성공은 별도 결과 검수 대상이다. V5 검수의 `upper45_*` 해석 범위도 그대로 적용한다.

- Source SHA256: `d1c4f7c031de60c4174cb1c0195075940777015a5c7b3c831cb4eb4fe08c28a1`
- Plan SHA256: `60beb807f873b7216fdc8cf5f753cb5a8a3fca9d49a665271048e269b8555748`
