# 실제4개 수집 독립 검수: PASS

고정 V6 fit·50·100·300의 새 확률 수집 원자료를 구현 비참여 peer가 검수했다. 기존559개 core 입력과 추가 검수 원자료의 SHA는 CPU 검사 전후 모두 일치했다. 실제 Python3.8.20에서 배열·텐서 계산만 수행했으며 추가 GPU·Isaac·native 장면·NN forward·fit·PPO 갱신은0이다. 실행 중인 전체 기울기 분석 산출물과 미봉인 보고서 코드는 읽지 않았다.

각 case의 완료·장면 닫힘·실패/cleanup/입력변경 없음, checkpoint 버전0/50/100/300, model/optimizer fingerprint 및 checkpoint SHA 불변,0회 fit/PPO/reference 호출을 확인했다. root는4개 프로세스 exit0을 보고했다. 이 검수에서는 별도 프로세스 종료 코드 기록을 사용하지 않았으며 저장된 실제 완료·정리 증거를 독립 확인했다.

각 case 원128개 고유 환경·첫 시도384음 분모를 검사했다. 원12개 buffer에서H32×11+H2, 총45312전이, reset 전후 episode ID와 clock 연속성, terminal next value0, 최종9개 가중 보상 합을 확인했다. score clock phase와 경계 통과도 원시 배열에서 재계산했다. 독립 NumPy GAE 재귀와 원 Torch GAE를 대조하고 공통 joint 정규화 분해의 합도 검산했다.

|저장본|첫 시도|음 기회|A/B7/B8 달성|세 음 달성|총 비용|
|---|---:|---:|---|---:|---:|
|fit|128|384|24/42/53|14|0|
|50|128|384|4/0/9|0|0|
|100|128|384|1/0/0|0|0|
|300|128|384|2/10/7|0|0|

fit와300은 기존 동일 저장본·seed·확률 평가의128개 전체 첫 원장이 정확히 같았다. env0 기록도 force를 제외한 모든 키(q·target·body·candidate·NN goal·정산 등)가 정확히 같았다. force의 최대 차이는 두 case 모두7.62939453125e−6N이며 별도로 기록했다. 이는 이번 observer wrapper가 기록한 범위의 동작을 바꾸지 않았다는 증거다.

앞선 미봉인 report 초안의 cause 라벨에 대한 정적 검토 의견을 정정한다. base Environment의 higher/lower/assignment를 확인했던 것은 현행 override 확인이 부족했다. 실제 FingerSkillEnvironment와 저장된 전체 계약은 `guitar_learning.wrong_press_sources.v2`의 `other_higher`, `own_wrong_fret`, `own_wrong_string` 순서다. 원시값과 실제 계약은 보존되어 있어 수집 자체를 무효화하지 않는다.

300의 A음에서 index3의 세 cause별 누적 발음시간 비율은 약0,0.984375,0.984375였다. 발음 중 endpoint에서 `own_wrong_fret`·`own_wrong_string`이 동시에 켜진 표본의 source fret5를 원자료로 확인했다(A 목표 fret4). 두 출처는 겹칠 수 있다. 이것을 실제 현 압력·음향이나 실패의 단독 원인으로 확대하지 않는다.

상세 원자료 SHA와 case별 수치는 `actual_collection_review.json`에 있다. 전체 기울기 분석·수정 보고서·그림 QA는 별도 후속 검수 대상이다.
