# Timed ENTRY 실행·목표 예측 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / 미해소 Suggestion 없음. 저장 코드·원자료·영상·문서만 검수했고 새 native 초기화·물리 실행은 하지 않았다. 실행 전 변경은 동결된 `pre_review.md`에 기록돼 있다.

- 완료 결과는 `native_retry_v1`의 1200 physics steps/300 controls/151 camera frames/21계약 통과다. trace152개에는 terminal step884의 별도 표본이 포함된다. 최초 `native`는 exit143/두 view 각94프레임 후 최종 report·controls·trace·after manifest 없이 중단됐으며 성공으로 사용하지 않는다. 두 시도의 초기값과 소비 runner/wrapper SHA가 같고, 외부 종료 신호 원인은 미확정이라는 기록이 적절하다.
- native1059개 입력은 현재1057개와 실행 당시 exact source 사본2개로 모두 해결되고 분석 입력7개는 별도로 일치한다. actual closed phase1 command16개 모두 READY geometry3이며, phase별 R9 damping 요청/전체81 native readback·setter state 보존도 재검증했다.
- timed-ENTRY retry와 이전 APPROACH-only의 2.5초 전 controls150개·2.5초까지 전체 native trace76개 및 비교6 SHA를 직접 대조했다. 첫 timely hit·첫 scheduled recovery를 포함한 prefix 동일성이며 전체1200-step 같음을 뜻하지 않는다.
- raw 합계는 timely hit1, physical hit2, geometry accepted2, release6, miss6, wrong4다. 첫 event0/string2 DOWN/1.35초는 `+44.484798ms` timely hit이고, 두 번째 event3/2.75초는 `−63.511612ms` premature physical hit로 timely_hit=false다. 첫 clearance lifted/reached/scheduled completion은 `1.4/2.183333/2.366667초`, source 종료는3.683333초다. PREPARE/PLAY/HOLD `49/172/79` 및 partial F1 `0.307692319`를 전체 성능 성공으로 확대하지 않는다.
- 기타 최대/끝 위치 `46.353646/28.895391mm`, 회전 `7.095455/3.690350°`, 사용자 범위 안 제어/policy 표본 `241/300`, `162/172`가 원자료와 일치한다. retry MP4 두 개의 SHA와 실제 ffprobe `1280×720/30fps/151프레임/5.033333초`, 5초 hands native frame을 확인했다.

`goal_authority_diagnosis_v2.py:12–35`의 6입력 pre/post SHA·봉인 후 helper import·Python3.8 AST를 확인했다. 저장 native 상태8개의 actual81q를 대조하고, R9만 최종 제출 목표로 대체한 독립 XML-calibrated FK를 계산했다. 현재 actual fingers 유지·actual anchor/ChestDelta 정렬·현재 기타 변환과 native 목표 bounds가 일치한다. 저장 예측과 재계산 차이는 최대 `2.85e−13mm`다. 목표 예측 Gz 범위 `−103.658297…−74.598310mm`, R9 최대 목표−actual 좌표 성분 차 `0.417103…0.710770rad`를 확인했다. 그래프의 실제 pick/READY20.3mm/목표 예측 세 곡선은 서로 구분된다.

실패한 authority v1의 PYTHONPATH import 오류와 exact 원문 SHA는 별도로 보존돼 있다. v2 FK 목표 예측은 미래 actual pose·미관측 방향 미분·PD 실패 원인·줄 접촉력/음향의 인증이 아니다.

해소한 문서 권고: 후속 링크·소유권 설명을 `STRIKE_TIMED_WAIT_PRIORITY_PLAN.md`의 닫힌 시간창 R9 READY 증분 목표로 정정했고, README:37의 측정 대상을 줄 위치가 아닌 **pick 위치**로 좁혔다. 정정 전 문서는 별도로 보존된다. 현재 절대 자료 링크는 모두 실존한다.

검수 SHA256: runner `0e6fc3e2c320738e1b9841c184fdcc4604420866e77e17daca52a22b9334353e`; retry summary `3b5e976bf968a64a6807a05a9a4545475361b592bc5edcd8ac54acc26d4499d7`; authority v2 producer `62920657e0af44f0745eed5e938cc4e536a9ab12757dd66876f5aa5d87f2d25f`; prefix 결과 `62ae9f4ac04a898dc72712689bf5663071dea427bfc2fadef7a55882050de3b8`.

최종 범위: READY waypoint 선택 계약과 첫 회복 완료는 확인됐지만 두 번째 timely hit·전체 연주 완료는 얻지 못했다. source 종료 뒤 HOLD 녹화와 미실행/별도 후속 비교를 구분한다. 남은 actionable finding 없이 이 기록을 동결한다.
