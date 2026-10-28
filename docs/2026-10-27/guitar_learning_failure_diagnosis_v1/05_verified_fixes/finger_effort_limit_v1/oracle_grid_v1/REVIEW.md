# 동일 grid cap 준비 독립 검수

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

CPU self-test를 재실행하고833개 입력 SHA와 부모 grid/cap 봉인 superset을 확인했다. 공식 cap 실제 review PASS와 검토파일·verification 입력 연결, 원 grid execute/collect/settings/선정순위 재사용,135/180 유효 첫 시도 및450 선언표의 유지가 맞다. NN·체크포인트 경로는 없다.

가변 환경 수 전용 native 검사는 원 strict loader와 동일 K/D profile을 사용하며105필드 중16effort만0.25Nm로 바뀌는지 확인한다. 기존4환경 검증을 속이거나 우회하지 않는다. 원90쌍과135/180 readback 수를 확인한다.

실제 nested GridEffortPool을 작은 CPU fake parent에 연결해 정상 생성, native readback 실패, 생성 후 계약 실패를 검증했다. 각 실패는 장면을 한 번 닫고, close가 동시에 실패해도 원 AssertionError를 보존하며 cleanup 오류를 별도로 남긴다. pool·loader alias는 정상/예외 모두 복구된다. 기존/깨진 symlink 출력과 pending seal은 native import 전에 거부되고 runs는 생성되지 않았다.

GPU/native 실행은 하지 않았다. 실제 자원 적합성·315시도 완료·성공 후보는 미검증이며 effort를 접촉쌍 압력이나 실측 토크 상한으로 확대하지 않는다. 최종 파일 SHA와 pending 봉인의 입력 내용 fingerprint는 [review.json](review.json)에 기록했다.
