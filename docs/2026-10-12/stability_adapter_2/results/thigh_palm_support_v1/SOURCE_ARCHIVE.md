# 입력·코드 버전 보존

원자료의 report.source_sha256는 실행 당시 파일 내용이다. 이후 검수 보완 때문에
현재 코드와 달라진 producer는 다음 byte-for-byte SHA 일치 사본으로 검증한다.

- search_wrist_only_producer.py: 손목3만 사용한 첫 실패 탐색. 후보3개는 정적 gate에서
  거절됐고 native 실행은 없다. search_wrist_only.json/log와 설정도 보존한다.
- search_producer_v2.py: 팔꿈치X+손목3의50/100/150µm 탐색 코드. search.json 입력 SHA와
  일치한다. 이후 역사 입력 SHA를 병합 전에 검증하는 보완을 추가했다.
- search_producer_v3.py:2µm near_touch 탐색 코드. search_near_touch.json의 SHA와 일치한다.
- runner_v1.py: reference/clear_50um/clear_100um 당시 코드. 기준 raw5의 시작 SHA 봉인과
  FK 실패 원자료 저장은 당시 아직 없었으나 정상 실행의 모든 원자료는 보존했다.
- runner_v2.py: clear_150um 당시 코드. raw5 봉인/FK 실패 저장을 추가한 버전이다.
  v1 사본에 당시 patch를 적용해 재구성했고 실제 report의 SHA와 정확히 일치함을 확인했다.
- runner_v3.py: clear_2um 당시 코드. near_touch·역사 producer 사본 검증과 native shape
  속성 계측을 추가했다. 이후 실패 저장 예외에도 환경을 닫도록 cleanup을 보완했다.
- analyzer_v1.py: 첫 comparison.json의 코드. 당시 실제 helper/asset SHA 봉인이 부족했다.
  첫 comparison.json 및 comparison_near_touch.json을 보존하고5실행을 재분석한
  comparison_validated.json을 canonical 결과로 사용한다. 수치 결과는 유지된다.

canonical 분석은 실제 XML/mesh/helper와 실행 당시 코드 사본까지111입력을 시작/종료에
검증했다. 이는 새 native 실행이 아닌 저장 상태의 재분석이다. 과거 metadata를 현재 코드의
SHA로 바꾸거나 실패 원자료를 삭제하지 않았다. 로그는 logs/에 있다.

최초 source 재생의 render/와 render_v1/은 같은 미디어·manifest를 보존한다.
당시 renderer 원문 사본은 누락돼 manifest의 producer SHA만 남았다. 종료 SHA 검사
보완과 보이는2D 설명 표식을 추가한 현재 producer는 실행 전에 source_render_v2/에
정확한 사본을 저장했다. 새 canonical render_v2의25프레임을 전부 다시 생성해,
실제 입력/helper/output SHA의 시작·종료 검사를 수행했다. 새 native 실행은 없다.
