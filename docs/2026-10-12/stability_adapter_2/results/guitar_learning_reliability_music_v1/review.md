# 신뢰성·음악 탐색 개선 최종 독립 검수

## 요약 판정

**문제없음.** 구현·실제 제한 실행·최종 문서의 범위가 일치한다. 중단/복구와 수정 pool의 실제 연결은 확인됐으며, 음악 연주 성과나 장기 메모리 안전성을 인증하는 판정은 아니다.

- Critical: 미해결 사항 없음.
- Warning: 미해결 사항 없음.
- Suggestion: 없음.

최종 검수에서 문서 두 곳의 불일치를 전달했고 담당자의 보존 후 수정을 확인했다. TRAINING.md 첫 단락의 과거 N16/H128 권장은 현재 N8/H256과 과거 비교 근거로 구분되었다. PARALLEL_TRAINING.md는 trainer 생성만으로 저장한다고 쓰던 내용을 `recovery_eligible=True`인 fresh 초기화/strict load 성공 상태만 저장하며 실패한 resume은 복구 파일을 만들지 않는 설명으로 고쳤다. 검수자는 이 review.md 외 파일을 수정하지 않았다.

## 실제 결과 독립 대조

7개 실행의 report와 지정 transitions.jsonl.gz를 읽어 전이·종료·실패·매칭·유지·pool 완료 목표를 순차 재집계했다. 총 **로그9,261전이, 학습 반영9,224전이, optimizer 업데이트6회**로 집계와 일치한다. 이는 서로 다른 정책·계약의 합이며 단일 연속 학습6회가 아니다.

| 실행 | 로그/반영 전이 | 완료 episode | 판정 확인 |
| --- | ---: | ---: | --- |
| interrupt_native_v1 | 32/0 | 0 | interrupted, 미완료32전이 폐기 |
| resume_native_v1 | 8/8 | 0 | 정상, 업데이트1회 |
| fake_memory_native_v1 | 5/0 | 0 | memory_guard, 미완료5전이 폐기 |
| dense_8env_native_v1 | 4096/4096 | 40 | 정상,20mm |
| dense_8env_native_v2 | 4096/4096 | 40 | 정상,50mm |
| pool_native_v1 | 0/0 | 0 | 초기 계약 불일치 실패 보존 |
| pool_native_v2 | 1024/1024 | 10 | 정상,공통 정규화 수정 |

모든 report의 입력 변경·import 누락·원 소스 parity·worker 감사 누락·guard·worker failure·물리 flag·cleanup 오류 목록은 비어 있음을 직접 확인했다. 두 예정 중단과 최초 pool 실패의 completed=False를 정상 완료로 집계하지 않는다. 전체 compact의 실제 물리 실패 tick, 50/100ms 매칭, 종료 episode의 목표 후보 유지 시간은0이다.

수정 pool의 완료 목표 순서는 worker0 `[2,1,3,0,4]`, worker1 `[1,2,4,0,3]`이다. reset 선택만이 아니라 각 worker에서 다섯 목표의 episode 완료를 직접 확인했다. 접촉 후보1틱은 목표 발음 구간의 성공적 유지나 음향으로 확대하지 않는다.

복구 분석 producer의 비교 경로와 summary를 확인했다. 중단 전 initial과 failure checkpoint의 모델/actor·value optimizer 일치, recovery와 재개 initial의 모델/optimizer/RNG 일치, updates10→11이 기록되어 있다. CPU 가중치 비교를 이번 리뷰에서 중복 실행하지 않았다. SIGINT driver는 자신의 학습 부모 PID만 중단하며 fake memory driver는 관측을3GiB로 바꾼다. 실제 host RAM을 고갈시키는 시험은 아니다.

두 dense 실행의 첫 동일 행동/거리에서 오른손 guide credit이 180.346배가 된 비교는 정의 변경의 효과다. 평균 guide 거리50.449/50.453mm와 매칭·유지0을 함께 제시하므로 반환값 상승을 성능 개선으로 해석하지 않는 결론이 타당하다. 기타 로컬 guide evidence는 실제 마지막 표본의 read-only proxy이며 제어/성공 판정을 바꾸지 않는다. 18.470GiB RAM 최소, 현재 RSS/PSS의5초 표본, 60Hz 접촉 비율의 한계도 문서에서 구분한다.

## 설정·코드·보존

현행 dense/legacy/pool 설정은 N8/H256/batch2048, 추가256업데이트, checkpoint5, soft wall28,800초, RAM 여유4GiB이며 모드와 명시 pool 목록을 구분한다. legacy 고정 계약의 실제 재개와 새 dense/pool 계약의 새 정책 시작을 혼동하지 않는다. pool native 검증은 N2/H512였으며 선택형 N8 pool의 장기 성능을 검증한 결과가 아니다. 새8시간 실행은 하지 않았다.

사전 세 검수 문서는 보존되어 있다. source_run_v3 manifest의 Python54파일과 현행 파일의 SHA가 모두 일치함을 이번 리뷰에서 확인했다. CPU 최종 로그는 **127개/41.590초/OK**다. preservation_check_v1.json의1,585경로/1,588 SHA버전·모델106파일·보존282copy·reset113개·raw111tick/444물리표본 감사와 inputs_union_v1.json의 버전 구분을 확인했다. 이 전수 보존 감사는 담당자 산출물을 검토한 것이며 이번 독립 리뷰에서 모든 자산을 다시 해시하지 않았다. 전체240Hz 원자료 저장으로 주장하지 않는 설명이 정확하다.

seal_final_v1.py는 읽기만 했다. 분석 입력/최종 소비 코드 확인, 새 source_final에 byte-identical 복사, 문서 링크 검사, 배타적 신규 JSON 작성과 streaming SHA inventory 구조를 확인했다. 기존 실험/검수의 내용을 덮어쓰지 않으며 새 final_verification을 bounded integration/recovery 범위로 작성한다. **실행하지 않았고 최종 봉인 산출물의 생성·성공을 이 리뷰에서 미리 인증하지 않는다.**

새 물리·학습·렌더·전체 검사를 추가하지 않았다. 실제 도달성·연주 성공, 보상별 장기 성능, 메모리 누수 부재, pad 압력·진동·음향·Root 자유 균형은 여전히 후속 연구 범위다.

## 검수 시점 SHA256

| 파일 | SHA256 |
| --- | --- |
| native_summary_v1.json | `ae1f2c3e7c62ffd1ce5c025de464ef1296c208a8cf9a38506d54eb67b133535e` |
| preservation_check_v1.json | `6a633037e8d80206bd5f9a292380ce2764a1a179a08ebd23f598d3f3e81f1692` |
| inputs_union_v1.json | `d0dbc9e98a8bd09cadc38567d225c75ad0a6e25ecc3a39ee221e78151c98ac3e` |
| seal_final_v1.py | `419c8b864329f3abc2a40d9e8e48e05bb3691c0e1e59702a4a41cc03b04206d2` |
