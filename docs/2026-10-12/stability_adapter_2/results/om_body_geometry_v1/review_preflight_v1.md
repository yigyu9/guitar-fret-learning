# OM 바디 형상 사전 검수

판정: **문제없음 — 지정한 5초 native 진단을 막는 Critical을 발견하지 않았다.** 읽기 전용 코드·저장된 소스 결과 검수이며, 리뷰어는 물리 실행이나 자산 재생성을 수행하지 않았다.

- 두께 추출의 mm→m 변환, 측면 491mm와 외곽 491.957431mm의 축 정규화 및 앞·뒤 구면 재구성 식을 대조했다. 측면 중심선 깊이는 꼬리 104mm, 넥 약 85mm, 최대 107.197860mm이다. 횡방향 구면 연장과 가려진 앞판 연장은 명시된 재구성 선택이다.
- [바디 생성기](/home/ajou/yigyu/3/stability_adapter_2/build_om_body_geometry_v2.py:60)의 63 convex 분할은 저장 결과상 XY 외측 최대 0.494161mm, 내측 최대 0.457272mm, 최대 162정점이다. 기존 body frame과 비바디 물리 geom 보존 검사 6개가 참이며 v1/v2의 OBJ 64개는 byte-exact이다.
- [초기 후보 검색](/home/ajou/yigyu/3/stability_adapter_2/search_om_right_clearance_v2.py:18)은 오른팔 12개만 native 한계∩기준±0.15rad로 조정한다. 실제 저장 후보 변경 채널도 그 12개뿐이다. 최대 변화 0.074425rad, 손목 이동 7.045315mm, 10mm witness 요청의 맞춤 오차 0.770333mm이며 source_clear가 참이다.
- [진단 runner](/home/ajou/yigyu/3/stability_adapter_2/run_om_body_geometry_trial_v1.py:40)의 native G:body 63 shape gate, construction 한정 물성 setter, 기존 각 body 질량 유지·새 COM/I readback, COM/질량 캐시, 초기 기타 p/q·속도, 하체 고정 및 단일 PD 제출 경로를 확인했다. 초기 q_ref 목표는 5초 동안 일정하며 실제 자세 고정을 뜻하지 않는다.

Critical: 없음.

Warning:

- [생성기:62](/home/ajou/yigyu/3/stability_adapter_2/build_om_body_geometry_v2.py:62): 0.5mm 오차는 구간당 101개 XY 표본 검사이다. 연속 전체 표면이나 PhysX cooked 형상 오차 보증으로 확대하지 말고, native 형상 수·영상·간섭 결과를 별도로 보고한다.
- [runner:85](/home/ajou/yigyu/3/stability_adapter_2/run_om_body_geometry_trial_v1.py:85): 추가 collision 카메라는 appearance 카메라와 달리 음수 handle 검사가 없다. 실제 생성 실패 시 오류 기록은 남지만 원인 식별이 불명확할 수 있으므로 후속 버전에서 동일 검사를 권장한다.

라이선스 문서의 출처·변경·비상업·동일조건 표시와 바디 파생 자산에 한정한 범위를 확인했다. 연구 명칭만으로 NC 충족이나 전체 프로젝트 라이선스 변경을 인증하지 않는다. 원질량 유지 또한 실물 중공 바디의 질량 분포·강성 인증이 아니다. native 로딩·충돌·물성 readback·5초 유지·연주 성공은 이 사전 검수의 인증 대상이 아니다.

검수 SHA: 사전 핀 77개 모두 현재 일치. [사전 핀](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/source_before_native_v1.json)의 SHA256은 `48afe15187154a2fd0c7a6ebae3fd384894023662f9b7a51779c6e6d32ef3be2`이다. 생성기 v2 `966cca56dcb84556aec8d72710d6c1376de3277b0010a4945ec1c485528aafb2`, 검색 v2 `a3a68ede7df1d230085c0cad4a5a9ffbe87bfed3cbc72361dce5116edc43a55b`, runner v1 `9f5110863ca7c858d657d94a5150867b8d767a245345ab54f6bf2d021fdb41ff`.
