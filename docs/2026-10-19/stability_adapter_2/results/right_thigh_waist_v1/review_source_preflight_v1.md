# 오른 허벅지 waist source1 검수 기록

판정: **거절 원본 보존은 문제없음. source1의 완전한 형상 입력 봉인은 미달.** 발견 Critical 1건, Warning 1건, Suggestion 0건. 기록 작성 전에 CPU 탐색이 완료됐으며 세 후보 모두 거절, 선택/native 후보0이다.

## Critical — source1의 감사 범위

[source1:38](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v1.py:38)은 전체 source 감사에서 실제 읽는 humanoid XML의 손/손가락 mesh를 pin하지 않는다. 실제 XML mesh37개 중 이전 B 봉인의 expected SHA에도 없는 손 STL35개가 있어 이전 봉인으로 before 근거를 소급할 수 없다. 원본 코드·로그·거절 결과를 보존하고 source1을 완전한 입력 봉인 실행으로 설명하지 않는다. 후속 source2에서 compiler.meshdir 기준37개를 명시 pin하도록 보완했다. config.json/원 기타 XML 누락은 source1 실행 전에 추가됐다.

BASE/CFG의 전체81q·joint 이름 exact, profile 길이/y 변환과 waist 구간 약[−.347115,−.302838]m, full 양 Hip 최소거리 brent 부호 전환(85/95/105mm), 모델 범위/Elbow_y ±5° 여유 및 최종6caps·LP·frozen42 gate를 확인했다. AST는 통과했다. source1 최종 결과는 waist gate와 전체 source_clear가 모두 false이며, 95/105mm는 Chest/Shoulder analytic 겹침도 있었다. 잘못된 후보를 native에 투입하지 않은 수락 로직은 적절하다.

## Warning

[source1:79](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v1.py:79): min(L/RHip)0.3mm는 오른 허벅지0.3mm나 waist 걸침을 보장하지 않는다. source 간격과 전체 LP 수락은 cooked 접촉·지지력/형상 맞춤 인증이 아니며, 실제 접촉 위치와 유지 상태를 후속 native에서 확인해야 한다. 이번 결과에는 그 대상 후보가 없다.

검수 SHA-256: source1 `4eccfb1db46bc343fa4133f5a12124b13541e253a6f9706d1c69e93d669395b7`, PLAN_V1 `c365caa8147d4ed1a7d40135b13b0a175031877cc8e387943a85572d687868e9`, search_v1/search.json `b4d9a45235fa24c46a4fee0379f4c4cdee60bf1cf8bfcc9d4a3ef13a36f988c5`.

소스·원자료를 수정하거나 새 탐색/native를 실행하지 않았다. 순수 읽기·기존 형상 거리 산술 점검에 한정하며 사전 입력 SHA 누락을 사후 완전 봉인으로 간주하지 않는다.
