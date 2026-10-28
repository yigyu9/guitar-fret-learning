# 실제 cap 분석 독립 검수

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

CPU에서 기존 출력 쓰기를 메모리로 가로채 두 분석 스크립트를 재생했다. comparison·verification JSON, 두 본문 CSV, arm JSON/CSV가 현재 저장본과 일치한다. 직접 입력815개·검증 입력794개와 arm 보조 입력19개의 SHA를 확인했다. arm JSON의 누락된 readback SHA 두 개는 작성자가 보완했으며 수치 변화는 없다.

새8개와 기준선8개의 전체 첫 시도, 두 종료 장면,105 native 속성 중16 effort만 변경됨, 선택4 action/target tape 동일성,439개 CPU 판정 재현을 검수했다. 별도 NumPy 계산으로 LH 힘264행, arm 경계144행,16개 원장·9보상 지급을 대조했다. reward 합 잔차 최대6.1795e−7이다. 그림도 직접 확인했다.

검지3/4→0/4·wrong100%, 손목 평균오차0.843→12.440mm 및 중지4/4 유지가 원자료와 일치한다. Wrist_y 하한 체류와 Wrist_z 추종오차를 구분했고, actual의 미세한 actionbox 이탈을 native 실패로 바꾸지 않았다. 기준선 nearest-height 불일치,60Hz·env0 범위, native velocity 좌표 및 pair pressure/단독 인과 한계가 정확히 유지된다. 분석 PASS는 음악 기준 충족이나0.25Nm 기본 채택 승인이 아니다.

검토한11개 파일의 최종 SHA와 독립 계산값은 [review.json](review.json)에 기록했다. GPU·native scene 실행, 활성 소스·원자료·기존 분석파일 수정은 하지 않았다.
