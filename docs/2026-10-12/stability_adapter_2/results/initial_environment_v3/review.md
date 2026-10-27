# P1a CPU 초기화·제어 계약 최종 검수

검수일: 2026-10-06. 검수: 별도 change-reviewer.
판정: 문제없음. Critical / Warning / Suggestion 없음.

첫 검수의 native POS 모드 effort 미적용과 COM 기준 경로점 속도 오류를 수정했다.
native solver POS PD의 실제 관절 응답과 offset-COM 점 속도를 회귀검사로 확인했다.
공용 tensor hybrid PD와 다른 CPU 제어 조건임을 문서화했고, 실제 적용 토크로
오인될 계산 torque 값과 무효 effort 호출을 제거했다.

검수자가 6개 테스트를 직접 재실행해 통과했다. v3 report의 16개 초기화 검사,
7개 trace sample(0~0.1초), source SHA-256과 문서 결과 수치를 대조했다.
프로젝트 보호 대상 87개 파일의 크기·mtime_ns와 이전 원본 source hash 15건은 불변이다.

이 판정은 CPU 초기화·제어 계약에 한한다. 초기 장면 렌더·관통/접촉 품질·실제 토크·
10초 정지 안정성·작은 손/팔 움직임·연주 호환은 미검증이다.
0.1초 뒤 기타 오차 65.315mm·7.318°는 자세 유지 성공이 아니다.
