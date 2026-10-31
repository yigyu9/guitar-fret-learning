# V4 capture 준비 검수

**요약 판정: 문제없음 — PASS.** 미해결 Critical / Warning / Suggestion 없음. 범위는 capture 준비물이며 별도 학습 worker의 runtime/learn 코드는 포함하지 않는다.

실제 rl38 Python3.8.20에서 제어 전557상태·5관측필드·4목표의 detached 복사와 원자료 변형 후 보존, RNG 불변, 예외 후 별칭 복구 CPU 검사를 독립 재실행했다.502개 입력 SHA가 일치하며 V2 원488핀 preflight와 pending 리뷰 gate의 수치모듈/Isaac import 전 거부를 확인했다. SOURCE 깊이와 geometry의 임시 V2 HERE 문맥 및 복구가 맞고, reference proxy는 명시 shared로 원 V2 평균을 한 번 호출하므로 재귀나 새 난수·물리 스텝을 만들지 않는다.

최초 검수에서 원 native 오류 뒤 partial 저장과 오류로그까지 실패하면 원 예외가 바뀌는 경로를 발견했다. root 수정 후 mocked execute로 원 예외 객체 유지·두 보존오류 부착·HERE/SCHEMA/support/geometry 원복을 독립 재현했다.

원 V2 mean·9보상·PD·물리·종료·128원장을 바꾸지 않으며, 수집은 clock0..1412 제어 전 관측과 원 다음끝점 목표를 연결한다. 실제 실행 뒤1416행·원 q/target/body/candidate·128원장·현재계약 동일성을 강제한다. baseline은 명시 재사용이다. 아직 native 수집 동일성이 증명된 것은 아니므로 실행 후 capture_verification과 입력·cleanup 감사를 별도 확인해야 한다.
