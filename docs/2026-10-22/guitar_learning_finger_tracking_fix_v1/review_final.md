# 독립 change-reviewer 검수 기록

2026-10-22. `/root/review_gpu`의 읽기/CPU 검수 메시지를 root가 기록했다. reviewer는 활성 소스·문서·원자료를 변경하지 않았고 GPU/GL을 실행하지 않았다.

최종 판정은 문제없음이다. 원인 진단·정책 입력 교차검산·native N6 도구·solver16 래퍼·실제 자세 로그·검증 도구·최종 원자료와 문서를 각각 확인했다.

- 실제12개 NPZ의526프레임·0..2100/4 시계·285→405 이동량과 유지오차가 두 분석 JSON 및 README 표와 일치했다. 접촉 있는 약지x1.56을 무접촉 표에서 제외했다.
- 기존435 대비 활성 변경은 환경의 자세 진단·기존 검사 저장량 기대값·새5개 검사뿐이었다.436개 source SHA가 모두 manifest와 같았다. source 네 기저가 palm 직속·identity rest·x/z축인 것도 확인했다.
- reviewer가 직접 관련12개 CPU 검사와 pose-replay 참조2개 검사를 통과했다. root의 파일별 CPU8로그도73개 전체 OK로 집계했다. 전체865개 단일 프로세스 통과로 확대하지 않았다.
- palm 상대 quaternion·zero-y 참조·국소 SO(3) 오차·60Hz RMS/최대·선택 reset·H32 유지·기존 학습 출력 불변·오른손 미적용이 맞았다.
- policy architecture의 전체 계약과 PPO identity 비교를 확인해 이전 진단v1만 달라도 모델/optimizer/RNG 적재 전에 strict 거부된다는 문서가 정확했다.
- CPU/CUDA 저장 자세 재생의599핀 및 독립 계산 오차2.77e-16/3.37e-16rad를 확인했다. 이는 새 native 물리나 학습 성능 검증과 구분했다.
- 반복16의 소지 잔차 개선 부재·기본4 유지·native 내부 원인 미확정·과거435 학습 성과 미상속이 적절했다. 최종 README 링크와5개 무접촉 비교 그림도 확인했다.

실행 전 지적된 문제는 작성자가 수정 후 재검증했다: N6 settings SHA를 inputs_before에 넣는 저장 순서, simulator 생성 후 readback 실패 시 반환 전 handle 정리, 엄지 effort4Nm 표기. 최종 문서의 배열 표현은 '각 배열의 네 손가락 순서'로 정정했다. 나머지 실제 제어/학습 개선이 검증됐다는 판정은 아니다.
