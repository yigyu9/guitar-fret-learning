# 타이밍 커리큘럼 독립 구현 검수

**요약 판정: 문제없음.** 최종 코드에서 미해결 Critical·Warning·Suggestion을 발견하지 않았다. 검수자는 구현 소스를 수정하지 않았으며 이 보고서만 작성했다.

## 검수 범위

git상 `guitar_learning/`과 이번 결과 디렉터리가 untracked이므로, 작업 전106파일 보관본과 현행 파일을 비교하고 이번 신규 timing 모듈·검사·설정·안내 문서를 검수했다. 과거 실행·보관본의 광범위한 개선은 범위에 넣지 않았다.

- `timing_environment.py:19`: 실행 press/onset/end에만 같은 pre-roll을 더하고 원 목표·source시각·provenance를 보존한다. 실제 행동 구간5초와 native 정착2초를 구분하며 기존505 필드 순서·time4/count960 정규화를 유지한다.
- `timing_curriculum.py:118`: 실제240Hz 연속 표본만 유지 시간으로 적분하고 접촉 소실 시 연속 길이를 초기화한다. 마지막 LH 단계는 원onset/end 전체를 요구한다. RH는 원래 유효 기하 통과를 사용하고 중복·반복 성공 보상과 정밀도 보상 상한을 처리한다. 안전 실패와 truncation은 성공으로 집계하지 않는다.
- `timing_transfer.py:122`: BC/PPO 활성 Actor와 해당 std만 이전한다. 505→536 새 입력 열은 정확히0이며 동일 기존 입력의 정책 응답을 보존한다. 행동·물리 안전·목표·관측 prefix 변경은 거부하고 strict PPO resume를 완화하지 않는다.
- `timing_demonstration.py:21`: 원240개 행동과 마지막 행동60회 유지로 새300×536 자료를 실제 수집한다. 안전 완주·타이밍 성공·입력 무변경인 자료만 학습으로 읽고, 활성 Actor 이외의 critic·반대손·std 불변을 검사한다. 실패·예외의 부분 원자료와 cleanup 결과도 남긴다.
- `train_timing_v2.py:8`: fresh spawn에서 원 compact logger를 먼저 캡처한 뒤 timing wrapper를 설치한다. 모듈 최상위 worker여서 spawn 전달이 가능하고 중단 시 dispatch를 복원한다.

## 발견 후 해결된 사항

- `timing_environment.py:145`: timing 측정/보상 후처리 예외가 나면 다음 물리 진행을 막도록 `finished=True` 처리했다. 예외 주입·추가 step 거부·reset 복구 검사가 있다.
- v1 PPO worker의 lazy logger 순환은 원 실패를 보존하고 새 `train_timing_v2` 진입점으로 해결했다. 별도 새 interpreter 회귀와 실제 PPO 수집/업데이트로 재확인했다.
- Actor 이전 설명은 활성 Actor만 복사하도록 문구를 명확히 했고, 초기 상태 비교는 관측 가능한 상태와 숨은 solver/contact 상태의 한계를 구분한다.

## 검증 근거

검수자가 ledger·환경·Actor 이전·runner/evaluation·새 teacher/BC·fresh-worker 관련 검사를 별도로 실행해 통과를 확인했다. 최종 동결 코드의 전체 회귀는 `cpu_tests_v3.log`의 **238개 통과**를 확인했다. 중간 소스 변경과 겹친 CPU_v1/RH 초기평가는 최종 근거에서 제외했다.

| 실제 실행 | 확인 결과 |
| --- | --- |
| 양손 새 teacher 재생 | 각각300tick·안전5초 완주·단계0 성공·입력 무변경 |
| 새 BC 정책 평가 | 손별2/2 안전 완주·단계0 성공·입력 무변경 |
| PPO smoke v2 | 손별1업데이트/300전이·완료·실패 없음·persistent audit 오류 없음 |
| 최종 PPO 정책 평가 | 손별2/2 안전5초 완주·단계0 성공·입력 무변경 |

최종 LH의 원음 구간 접촉후보 coverage는 두 회1.0, RH의 최소 목표방향 시간오차는 두 회17.42178ms다. 원래 joint music50/100ms 매칭은 모두0이다. BC 수치 tolerance 미달과 실제 정책 성공을 구분하고, 직접 이전한 LH의 초기 안전 실패도 보존했다.

작업 전106개 archive 파일의 SHA가 원 manifest와 모두 같음을 독립 확인했다. 직전 phase 보존 집계는 `previous_preservation_v1.json`의720산출물·115소스·1637소비입력 확인을 참조한다.

이번 판정은 첫 단음·동일 준비 시작의 단계0 구현과 짧은 연결 검증에 한정한다. 단계1~4의 학습 완료·장기 수렴·양손 동시 연주·압력·음향·일반화를 인증하지 않는다.
