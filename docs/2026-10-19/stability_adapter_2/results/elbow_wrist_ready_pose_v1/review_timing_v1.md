# V6 올려치기 시간 변경과 FK 진단 검수

요약 판정: 문제없음. V5→V6 변경은 시간 배열 한 줄뿐이며 기존 요청/최종 hard gate·목표75·속도 항·유한 effort 경로를 유지한다.

Critical: 0

## 확인 근거

- [V6 시간:10](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v6.py:10): 증가하는 시각 [2,2.6,2.9,3.2,3.55,3.75,4.45,4.7,5]와9 vertices의 개수가 일치한다. 첫2초/접근/하강/down은 기존과 같고, down 끝 대기 .20초→up .70초→대기 .25초→회복 .30초로 총5초를 유지한다. 정지/첫2초는 깊이 보정 없이 기존 V5와 동일하다.
- 실제 waypoint의 횡단 폭 .0648994263m를 .70초로 나눈 nominal Gx 속도 .0927134661m/s는 원 .05m/s보다 크다. down 속도 .1854269322m/s도 유지한다. 끝점 대기 .20초는60Hz 12control이며 원 재무장2frame보다 길다. 실제 상대 속도·깊이·거리·ARMED 상태는 native detector 원자료로 판정한다.
- V6는 V5와 시간 배열 외 diff가 없다. 기존 finite/model/±1rad/requested 및 rate-applied norm160/3rad/s/원cap·PD·LEFT OFF·33EFFORT/48POSITION/단일 actuator/readonly marker·other75 목표 보존을 유지한다. Gz 보정 V4나 거절된 ±6mm envelope를 사용하지 않는다. 형상·초기값·목표 경로도 바꾸지 않는다.
- [진단:13](/home/ajou/yigyu/3/stability_adapter_2/diagnose_elbow_wrist_tracking_v1.py:13)는 초기 native로 FK를 보정하고 각 완료 control의 실제 q와 동일 endpoint의 실제 pick/G를 비교한다. 두 완료 사례 각300점의 저장 최대오차는 .001919908mm이며, desired는 직전 control 목표를 사용한다고 명시한다. stored 최대 desired−actual 차이는 strike12.307453mm/velocity14.794535mm로 FK 재현 오차와 실제 목표 추종을 구분한다.
- V6/diagnostic AST와 진단 producer 현재 SHA 일치를 확인했다. 진단에서 실제 읽는 human XML은 기존 두 native attempt 맵의 before SHA와 현재 파일이 일치함을 확인했다. solver/diagnostic/native를 재실행하지 않았다.

## Warning

- [TIMING_PLAN:3](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_TIMING_PLAN_V1.md:3)의 FK 오차는 source/native 좌표·회전 재현이 실제 같은 q에서 잘 맞는다는 근거다. 표본은60Hz control endpoint 300개이며 모든240Hz 상태나 collision/material/동역학 모델 전체의 정확성을 인증하지 않는다. 추종 차이가 있다는 진단을 전체 모델 문제 부재의 증명으로 확대하지 않는다.
- [진단 before 맵:10](/home/ajou/yigyu/3/stability_adapter_2/diagnose_elbow_wrist_tracking_v1.py:10)은 A py와 완료 native 산출물1987개다. FK가 읽는 XML은 직접 진단 맵보다 기존 native input 맵의 합성 핀으로 닫힌다. 독립 새 XML-before 맵 인증으로 설명하지 않는다.
- nominal 속도와 대기는 실제 RELEASE 또는6줄 up 순서를 보장하지 않는다. 실제 native 성공/완료·첫 구간 동일성·손/LEFT 접촉·드리프트·detector lane/속도/깊이/재무장 검수는 후속 범위다. 현재 실행 중 산출물을 완료로 인증하지 않았다.

## Suggestion

없음. 현재 시간 변경의 읽기 검수에서 blocking 구현 오류를 발견하지 못했다.
