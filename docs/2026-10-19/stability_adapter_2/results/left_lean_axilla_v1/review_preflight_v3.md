# 왼쪽4° 근위 상완 접근 V3 사전 검수

요약 판정: **문제없음.** Critical 0 / Warning 0 / Suggestion 0. V3 변경/source 결과와 새 분석기 V2를 읽기 전용으로 검토했다. 새 native 실행·학습은 하지 않았다. source 수락은 제한된 native 진단 허용이며 유지 성공의 채택이 아니다.

[source V3](/home/ajou/yigyu/3/stability_adapter_2/search_left_lean_axilla_v3.py:24)는 기존 거절 해를 seed로 쓰고 Shoulder/Elbow 범위를±0.25rad, 기타 초기 Z 범위를±30mm로 확대한다. Thorax±0.05rad와 기타 나머지 이동 범위·수락 gate는 유지한다. 완료 후보는 전체 source clear, 근위65% gap4.695866mm, 전완2.209002mm, Hip 최소2.595971mm, 근위 normal world Z0.999366으로 gate를 통과한다.

기타 초기 delta는 world [−30.000, −36.087, +27.674]mm이고 기타 회전은 left4 기준과 같다. 기타 실제 state를 이동한 source audit를 사용한다. body/head/왼팔/손가락/오른손목을 포함한 다른72개 초기 scalar q는 left4 기준과 직접 비교해 exact였다. contract의 새 q_ref도 후보와 exact다. 설계 box 경계의 float32 오차 약1.19e−8rad는 코드의1e−7rad 허용 안이며 native 모델 한계는 통과한다. 입력582개 현재 SHA 불일치0개를 확인했다.

팔 외측268.483mm·아래37.835mm·손목 안쪽101.061mm, 손 위치 오차36.604mm다. 손 방향 변화8.507°는 soft 방향 목표의 결과이며 팔 world pose 보존을 의미하지 않는다. source clear·근위 gap은 cooked/native clearance나 실제 겨드랑이 지지력 인증이 아니다.

[runner V3](/home/ajou/yigyu/3/stability_adapter_2/run_left_lean_axilla_v3.py:116)는 V2와 계획/search 경로만 다르다. 기존 human right12 EFFORT/other69 새 POSITION 목표·고정 초기-world 전완 motor 목표·cap/owner window/상태 불변/Jacobian 가드를 유지한다. 기타 직접 외력·부착·런타임 pose 덮어쓰기는 추가하지 않는다. 몸통·팔·기타 배치를 함께 바꾼 조건이므로 이후 성능을 단일 기울임만의 효과로 설명할 수 없다.

[분석기 V2](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_lean_axilla_v2.py:19)는 config를 필수로 받아 candidate/config SHA를 attempt 입력과 대조하고, 초기 실제81 q를 candidate float32 및 effort 기준과 비교한다. G 초기 p도 float32 기준으로 비교한다. 이전 초기 불변 마스크에서 제외되었던 R_Wrist3을 포함해 검사하므로 **사전 리뷰 V2의 손목 검사 Warning은 코드상 해소됐다.** 완료 기록·명령·접촉 검증의 범위이며 전체 gravity/Jacobian·힘 기여·안정화 성공 인증이 아니다. 실제 새 분석기 실행 결과는 후속 검수 대상이다. Python3.8 구문은 확인했다.

검수 SHA256:

- 계획 V3: `26f0d598f1fb24c59c78313925b2ae5cde3a7d37a370f9cba04420c1717066f6`
- search V3: `eefbb56ba77a1f6fe5df51958bf5f8913e4ec13eece98d1d24e7b036de54bf55`
- runner V3: `1beebf9eb3f19fb19db97ab23825a00b890903397bbcdbcbcd5a2dcc364f9c8a`
- 분석기 V2: `9422d8c394497ec8054c02184a628f5f0d547d73bcf695ae927bb2ef14748f62`
- 완료 search.json: `a195908996179303e6809d6ed234d282076a94c5e2c44f5800ea3efadaa64f90`

이 새 리뷰 파일 외 원본·기존 실험·이전 리뷰는 수정하지 않았다.
