# Moving-guitar geometry v1 independent review

판정: **문제없음.** 요청 범위의 pure geometry CPU 단계에서 차단 사항을 발견하지 않았다. native 환경·detector·압현 성공 연결을 승인한 결과는 아니다.

- 기타 기준은 이름 `guitar`의 body 원점이며 실제 각 표본의 pose를 사용한다. 세계 공통 회전·이동에 대한 상대 좌표 불변성이 맞다. source COM을 위치 변환에 더하지 않는다.
- `body_point_motion`은 body-origin pose와 COM linear velocity 계약에서 `v_point=v_COM+omega×R(local-COM)`을 적용한다. `relative_point_motion`은 기타 원점 속도를 먼저 구하고 회전 좌표계 항을 뺀다. 수식과 기존 controller의 point_kinematics 사용 계약이 일치한다. 이 CPU 검수는 native 보고 속도와 자세 차분 차이의 원인 규명을 새로 완료한 것은 아니다.
- `relative_sweep_inputs`는 각 시각에서 이미 변환된 local pick을 사용하며 연속 physics step과 local 현 끝점 불변을 검사한다. endpoint-linear sweep의 근사 범위를 명시했다. 실제 detector·재무장·타현 시각 판정은 아직 연결되지 않았다.
- 물리 현 번호 1..6, musical fret 0의 `None` 반환과 legacy sentinel 거부를 확인했다. fret target은 측정한 fret interval의 중점이며 실제 손가락 패드·접촉 압력·음악 성공을 주장하지 않는다.
- CPU unittest 4개를 rl38 환경에서 독립 실행해 모두 통과했다. 테스트 전후 소스 SHA는 동일하다. 로그와 결과는 같은 review 아래 `cpu_geometry_v1`에 있다. scene 생성·물리 실행·소스 편집은 하지 않았다.

검수 SHA-256:

- geometry_v1.py: `e2e17b0083b6c29734a1a7232dbdbe6107fd27c8fc1782114cde1ec84e69a392`
- test_geometry_v1.py: `d3c43bfc5ef32100c378b47e7e02758bd928fc728caf4a692aa8f522fe705ab9`

Critical / Warning / Suggestion: 현재 범위에서 미해결 항목 없음.
