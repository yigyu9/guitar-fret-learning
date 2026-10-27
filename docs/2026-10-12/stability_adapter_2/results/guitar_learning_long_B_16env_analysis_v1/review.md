# 장기 학습 실패 분석 독립 검수

## 요약 판정

**문제없음.** 실패 원인에 관한 확정 사실과 추정, 완료 업데이트와 미완료 수집, 음악 수행과 optimizer 상태가 구분되어 있다. 원 실행의 정상 완료나 전체 worker 감사 통과를 인증하는 판정은 아니다.

- Critical: 없음.
- Warning: 미해결 사항 없음.
- Suggestion: 없음.

그림 v2의 `0 audible hold` 표현은 실제 음향 측정으로 오해할 여지가 있어 수정 권장했다. 담당자가 기존 산출물을 보존하고 plot_v3.py와 training_diagnosis_v3.png에서 `0 s target-contact candidate hold`로 명시했다. v3 그림을 직접 열어 문구·가독성과 원 데이터의 대응을 확인했으며 README의 권장 링크와 음향 미측정 설명도 확인했다.

## 원자료 대조

지정 원 실행의 report.json과 transitions.jsonl.gz를 읽기 전용으로 검사하고 compact 로그를 순차 집계했다. 완료 14업데이트의 28,672전이에서 종료 320회, 미스 320회, 50/100ms 매칭·후보 유지 시간·물리 실패 종료는 모두 0이었다. 15번째 미완료 수집은 112 control tick×16환경=1,792전이이며 종료·미스 각16회, 매칭·유지·물리 실패는 모두 0이다. 분석의 두 구간 분리가 일치한다. 완료 구간의 compact 기타 이동 최대는 2.22076964mm이며 전체 240Hz 최대라고 주장하지 않는다.

report.completed=False와 worker0 IPC TimeoutError, worker0 최종 감사 누락을 확인했다. 남은15개 최종 감사의 failure는 None이다. 실패 report의 stopped 초기 라벨을 정상 완료 근거로 사용하지 않는 설명이 적절하다. 원 실행의 저장 모델은 initial.pt와 checkpoint_000009.pt이며 final.pt는 없다. 마지막 checkpoint 분석은 10업데이트 가중치만 대상으로 하므로 11~14번째 모델까지 복구된 것으로 설명하지 않는다.

analysis_v2.json의 352개 reset initial_values 입력이 사전 pin에 포함되어 있고 현재 SHA가 모두 일치함을 별도로 확인했다. 첫/22번째 reset의 worker 평균 RSS high-water 679.30/829.81MiB, 최대 KL 0.01356369, rollback 0회와 checkpoint 평균 std 0.04979071이 문서와 일치한다. checkpoint producer는 CPU 가중치 유한성·std 검사이며, strict resume나 native 재시작 검증이 아니라는 한계도 정확히 명시되어 있다. 이번 리뷰는 checkpoint를 다시 로드하거나 학습하지 않았다.

## 인과관계와 해석 범위

kernel_window.txt에서 10:34:34 OOM-killer 호출, 후속 global_oom 및 rg PID3201193 종료를 직접 확인했다. killed line의 anon-rss 8,240,456kB는 약7.86GiB다. task 표 RSS의 페이지 단위와 killed line의 kB 단위를 구분한 환산이 맞다. report의 MemAvailable 최소 585,998,336bytes도 약0.546GiB다.

원 reset 자료에서 worker0 PID3185159를 확인했고, 기록된 학습 worker PID와 커널 직접 kill 목록이 겹치지 않는 분석과 일치한다. 따라서 **호스트 RAM OOM은 확인된 사실, 이것이 worker0 timeout을 일으켰다는 설명은 유력한 추정**으로 남겨야 한다. 문서는 이 구분을 지킨다. rg의 실행 주체나 MainThread의 역할, worker0의 정확한 정체 위치, 학습 코드 메모리 누수를 단정하지 않는다. RSS high-water 합은 공유 페이지를 중복 포함하고 서로 다른 시점 최대값이므로 정확한 동시 전용 RAM 소비로 합산하지 않는다.

학습 중단 원인과 별개로 음악 매칭·목표 후보 유지가 계속0이라는 결론은 기록에 부합한다. critic loss 감소와 유한한 가중치/안정적인 KL은 연주 성공의 근거로 사용하지 않는다. 접근 보상의 짧은 시간창, 왼손 거리 proxy와 오른손 연속 접근 보상의 부재는 검증할 설계상 가설로 제시되어 있으며 이번 로그만으로 단일 원인을 확정하지 않는다. 실제 음향·현 압력을 측정한 결과는 없다.

8환경×H256 제안은 batch2048을 보존하는 **미검증 보수적 운영안**으로 명시되어 있다. 장기 메모리 안전성과 음악 학습 성과를 보장하는 선정값으로 취급하지 않는 것이 적절하다. 과거 N16 권장의 단기 처리량 근거와 장기 RAM 검증 부족도 보존되어 있다.

## 검수 범위

README, analysis_v2.json, checkpoint_analysis.json, kernel_window.txt, 지정 producer 및 v3 그림과 제한된 관련 원자료를 검사했다. 넓은 재귀 검색, 새 물리·학습·렌더링, 전체 검사는 실행하지 않았다. 검수자는 이 review.md 외 파일을 수정하지 않았다. 후속 final_verification/source 봉인은 담당자의 별도 작업이며, 미작성 산출물의 완료를 전제하지 않는다.

| 검사 시점 파일 | SHA256 |
| --- | --- |
| analysis_v2.json | `b5486d32f0d06442f301a00c95b976e21f9773b74d9f606fc8420464ff93471a` |
| checkpoint_analysis.json | `8bdcb44a88e8767b33c9af02df71918a600672e1532a017b7be425439451cec1` |
| kernel_window.txt | `fda979c1aed44eb1b24ef75760cc9671b169a7b88efbec5508e51e845b15715f` |
| analyze_v2.py | `cc416f987806023f4b61f131773982435b15c2afa07bbc97247db8bdaeaa846e` |
