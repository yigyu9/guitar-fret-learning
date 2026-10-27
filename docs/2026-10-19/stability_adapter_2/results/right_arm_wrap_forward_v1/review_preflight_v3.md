# 전완·손 전방 이동 V3 사전검수

요약 판정: 문제없음. cached 제어 지지점 재사용은 지지 강체와 기타 초기값 고정이라는 물리적 전제에 맞다. 아래 legacy 목표 metadata 해석을 구분한다. 원본 수정·CPU/native 재실행은 하지 않았다.

Critical: 0

Warning: 1

- [source:77](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v3.py:77): `requested_elbow_forward_mm`과 :79의 `elbow_forward_error_mm`는 여전히5/10/15mm를 elbow 목표처럼 표현하지만 V3 실제 목표는 elbow원점0/palm5·10·15mm다. **소비 V3를 보존하고 문서·후속 분석에서 이 legacy label을 palm 요청값으로 해석함을 명시하며, 새 metadata에서는 palm 요청과 elbow0을 분리한다.** 실제 fitting·수락 gate·제어에는 영향이 없고 native 진행 차단 사유는 아니다.

Suggestion: 0

확인 근거:

- [source:40](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v3.py:40): 실제54~56 R_Elbow3만 기준±0.12rad/모델교집합으로 바꾼다. 나머지78각과 Shoulder/Thorax/body/head/left/Wrist/finger42/G초기값은 유지한다. Elbow_y±5° 여유를 포함한 실제 bounds가 비어 있지 않다.
- Calibrated FK에서 각 Elbow축을 독립으로0.05rad 바꾸어 Thorax/Shoulder p/q exact와 elbow원점<10nm를 확인했다. [source:71](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v3.py:71)의 cached Thorax capsule 및 upper30/45/65는 baseline의 runtime `right_block_cradle`와 exact다. 이 고정 강체들의 물리적 초기 위치·기타값이 같으므로 기존 attached local reference를 재사용할 수 있다.
- [source:55](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v3.py:55), [source:64](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v3.py:64): 모든source 비겹침/mincaps, full상완/normal/최근접20%·forearm12/Chest30/trunk20mm/natural/모델한계는 fresh FK/query로 판정한다. 새계산은 `fresh_capsule_body`/`full_upper_arm_witness`, cached제어참조는 기존capsule T/30·45·65 aliases와출처필드로 구분한다. 새 Elbow형상 proposal은 갱신하고 baseline forearm 가상요청cap0을 확인했다.
- [source:67](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v3.py:67): elbow원점변화<10nm와 palm전방>0·목표오차≤2mm·직교변위≤12mm를 요구한다. elbow 전방target gate를 제거한 [계획:5](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_FORWARD_PLAN_V3.md:5)과 일치한다.
- [source:91](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v3.py:91): config는 후보경로/hash와 static elbow amplitude0만 바꾸며 기존 Thorax10N4mm·상완20N8mm/body9PD·cap/controller를 유지한다. cached참조의 실제 native 생성결과는 다음 분석기에서 다시 exact 검사한다.
- [analyzerV2:20](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_forward_v2.py:20): 소비 source의 elbow3/arm6 schema에 따라 실제frozen각 개수를 계산한다. :37~40에서 native Thorax/Shoulder 전체state와 elbow원점10nm, baseline `two_block_configuration.json` 전체exact를 요구한다. :44의 짧은 공통240Hz시계/고정초기Gfront 투영·실제종료시간·읽기전후SHA 방식은 유지된다. baseline과같은설정 및 원점 불변을 새native에서 실제확인한뒤 결과로보고한다.
- Source/계획과 analyzerV2 AST 통과. source/계획의981개 before-map SHA가 현재파일과 일치하며 active XML/mesh/config/helper 핀 구조는 V2 그대로다. 현재 source값과 cooked접촉/실제5초유지는 구분한다.

- Source SHA256: `fde6e7db95bbd60a458a13a51dd8ab0ce01787ab99d370fff894ee82b95b93fe`
- Plan SHA256: `8ca24aceb1448b8bf6097e578f36d8d1eb52acb4f5101b757dcaed2b579c35b8`
- AnalyzerV2 SHA256: `e786d61841390dfe82151aa42f9e8247d11e7bd6202c077ce2517ece6dbff624`
