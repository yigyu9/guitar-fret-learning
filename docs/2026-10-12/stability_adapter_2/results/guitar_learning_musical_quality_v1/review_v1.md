# 음악 품질 구현 독립 사전검수

**요약 판정: 문제없음 — 최종 검수 완료.** 발견한4건이 해결됐고 미해결 Critical·Warning·Suggestion과 전달 차단 문제는 없다. 최종 전체 CPU297개와 독립 focused6개 검사가 통과했다. native 학습·평가와 최종 문서를 확인했으며 새 품질 성공은 양손 각각0/1이다. 수렴·성능 향상·음향 성공을 인증하지 않는다. 검수자는 구현·기존 봉인 자료를 수정하지 않고 이 보고서와 대응 JSON만 작성했다.

## 해결된 발견 사항

- **Critical — fresh worker 로거 재귀:** 최초 `train_musical_quality.py:native_environment`는 원 logger 바인딩 전에 compact를 교체했다. 별도 rl38 프로세스에서 specialist_parallel 미로드 상태로 교체 후 호출하면 RecursionError가 재현됐다. 현재 `train_musical_quality.py:38`의 선행 import와 fresh-subprocess 회귀 검사가 추가됐다.
- **Warning — 추가 관측 계약 미검사:** 최초 transfer는 새 이력 필드만 검사하고 scale tail을 잘랐다. 현재 `musical_quality_transfer.py:39`에서 전체 dimension·fields/scales 길이·새 scale 값·필드 순서를 검사한다. 잘못된 scale·누락 scale 거절 검사가 추가됐다.
- **Warning — 준비 접촉 metadata:** clean candidate가 기존 음악·timing·준비 보상에도 적용되는데 기존 metadata는 original candidate라고 설명했다. 현재 `musical_quality.py:43`의 preparation metadata v2와 candidate_source, 환경 reset·transfer 정규화가 이 의미 변경을 명시한다.
- **Warning — blocked 통과의 완료 조건:** 최초 summary는 unprepared/extra/timing wrong만 검사하면서 metadata는 blocked=0도 요구했다. 현재 `musical_quality.py:117`에서 나머지 blocked ID를 집합 차이로 별도 계산·감점하고 최종 성공을 막는다. unprepared/extra와 중복 감점하지 않으며 lifted/depth/zone/speed 탈락은 diagnostic으로 남는다. 그 카운터가 추가되어 최종 이력은27개, 상태는563개다.

## 소스로 확인한 연결

`fretting_quality.py`는 기존 양성 candidate를 보존하면서 확정된 같은 현 높은 fret을 veto한다. 실제 fret body와 원±2mm margin을 존중하고, 불명확한 feature·다른 현·지지 접촉을 일괄 오압현으로 확정하지 않는다. 목표 없이 낮은 fret만 누른 경우와 다른 손가락만 목표를 누른 경우를 missing과 구분한다. `TaskMeasurementV2._contacts`의 clean 집합이 기존 측정·ledger·보상 경로에 실제 전달된다.

`strike_quality.py`는 이전 표본까지 확보한 준비 상태로 crossing을 판정하며 현재 표본으로 소급 승인하지 않는다. 적격 matching 반복과 wait-rearm-only 반복을 별도 기록하고, accepted crossing 이후의 실제 분리 표본으로 현재 회복을 검사한다. 원 crossing candidates를 숨기거나 물리 파지·음향 성공으로 확대하지 않는다.

`musical_quality_environment.py:54`는 실제 네 substep의 quality 항을 최종 반환 reward·reward_terms·episode 합계에 연결한다. 실패 tick의 양성 항은 제거되고 실제 safety cost는 기존 경로를 유지한다. 노트 종료 뒤 기존 timing_hold 상쇄와 기존 LH timing_success 상쇄→audible clean 달성 보너스 대체도 확인했다. 최종 경계 검사에서 stage1 노트 후 유지+1의 정확한 상쇄·기존 성공 보너스 상쇄·audible 보너스 한 번 지급·해제 미달의 성공 차단을 확인했다.

`musical_quality.py`는 wrong/missing 점유 시간을240Hz 구간과 score 범위에 적분하고 release를 목표 손가락 소실이 아닌 qualified target-string contact 전체의 clear로 측정한다. release/recovery 일회성 지급 상태와 기타 차단 카운터가 관측 이력에 포함된다. 최종 성공은 기존 timing 달성에 품질 gate를 결합하며, timing-only 달성과 최상위·nested episode/specialist의 새 성공을 구분한다. LH는 stage별 clean fraction을 요구하는 완화 단계이지 모든 시간에 오류가 없는 전곡 판정은 아니다.

Actor 이전은 지정 손 encoder/head/std만 복사하고536 기존 입력 열을 유지·새27열을0으로 초기화한다. critic/optimizer/카운터는 새로 시작한다. 물리·행동·기본 관측·목표·timing 계약의 임의 변경을 허용하지 않으며 원 strict resume 코드는 변경하지 않는다. 같은 raw536 입력에서의 Actor 동등성과 실제 초기 물리/판정 변화 뒤의 성공은 별개다.

## 검사 상태

검수자가 직접 실행한 worker 판정/측정 검사28개와 root 통합·전이·fresh-worker 검사10개는 통과했다. 당시 소스 작성이 겹쳤으므로 이 실행을 최종 동결 소스의 인증으로 사용하지 않는다.

첫 전체 CPU 로그 `cpu_tests_v1.txt`의1개 실패는 post-note hold 테스트의 기본 stage0 fixture와 stage1 기대값 불일치였다. 최종 테스트는 stage1을 명시했고 `cpu_tests_final_v1.txt`는297개/140.310초 PASS다. 최종 동결본에서 검수자가 edge·transfer·fresh-worker 검사6개를 다시 실행해18.447초 PASS를 확인했다.

`source_before_native_v1.json`의148개 원경로와148개 정확 snapshot을 각각 SHA 대조해 변경0을 확인했다. `trace_comparison_v2.json` 입력14개도 모두 일치한다. 이는 최종 동결본 검사이며 수정 중의 앞선 실행과 구분한다.

이후 첫 native 시도는 Gymtorch 확장 import에서 Ninja를 PATH로 찾지 못해 장면 생성 전에 중단됐다. 실패 로그는 보존됐고, 새 v2 실행을 위해 `MUSICAL_QUALITY.md`의 두 예제에 rl38/bin PATH만 추가했다. v1/v2 pin 차이는 이 문서1개뿐이며 직접 diff로 확인했다. `source_before_native_v2.json`의148개 원경로와 snapshot도 모두 SHA 일치한다. runtime/test/config 코드는 변경되지 않아 CPU297개를 다시 반복할 근거는 없다. 재시도의 실제 결과는 아래에서 구분해 검수했다.

## 문서·저장 trace 비교

`MUSICAL_QUALITY.md`, README/AGENTS 최신 안내와 `trace_comparison_v2.md/.json`을 확인했다. 실행 문서는 원536 state 순서/scale 유지와 clean eligibility의 의미 변경을 구분하며, 새50/100ms 판정도 과거와 동일한 eligibility가 아님을 명시한다. 지원 범위는 첫 단음·손별·stage1 40% 완화이고 물리 피크·음향·전곡 화음/뮤팅·장기 수렴을 완료했다고 주장하지 않는다. 두 상세 문서의 local 링크8개도 존재/줄범위 검사를 통과했다.

trace 비교 생산자는 저장된 LH 접촉 evidence를 재분류하고 RH 실제 reset geometry0과 geometry1~1680을 준비 detector에 순서대로 넣는다. LH initial contact를 만들어 넣지 않으며 audible 경계를 완전히 관측했는지 검사한다. LH clean963/1680·audible1.0이면서 노트 후 목표현 clear0인 결과와, RH accepted down1·반대방향 eligible up1·extra down1을 구분한 설명은 산출물과 일치한다. 높은 nominal cell과 fret-body margin을 혼동해 오압현으로 재분류하지 않는다. 이 비교는 새로운 정책/물리 실행이나 전체 QualityLedger reward·새 성공 판정의 인증이 아니며 기존 결과도 보존한다. 이번 검수에서는1,680표본 분류를 다시 재집계하지 않았다.

## 실제 native 연결 결과

양손 학습(`left_native_train_v2`, `right_native_train_v1`)의 원 report·compact 전이420개씩·저장 rollout·initial/final checkpoint를 직접 확인했다. 각 초기 카운터0→최종1, rollout shape[420,1,563], 첫2초120전이 모두 goal mask와 실제 nonzero action이 있다. 총 학습840전이와 각1회 결정적 평가840전이는 구분한다. 재사용 worker는 정상 close/exit0이며 persistent audit completed·errors[]다. report의 source parity·changed inputs·물성·guard·worker 오류도 없다.

실제 학습 reward_terms를 전이에서 다시 합산하면 musical_quality_report와 정확히 일치한다. 반환 reward/episode 합과의 최대 차이는 약5.43e−8로 float32 반올림 범위다. LH 해제 지연−1.2739, post-note hold 상쇄−1, 기존 성공 상쇄−1·audible 성공+1, RH extra−0.1·회복+0.1이 실제 PPO 수집에 포함됐다. 마지막 analytic KL은 LH0.0138914241(재시도2)·RH0.0175722577(재시도1)로0.02 이하이며, 중간 시도의 큰 KL이 없었다고 설명하지 않는다.

평가 원 result·reset은 각 strict_PPO load로7초/420tick을 timeline_complete로 마쳤고 source_unchanged=True다. 두 평가의 실제 transitions를 독립 집계해 각1,680개 연속240Hz와 safety failure 표본0, LH correct964/missing716·RH missing1,680을 확인했다. RH의 비활성 왼손 missing은 오른손 보상에 포함되지 않는다. 평가 reward-term 합 오차는 최대2.22e−16이다. 최상위 timing·specialist·episode nested timing의 새 성공은 일치한다. 두 손 모두 timing-only=True이나 새 품질 성공은0/1이다.

- LH: audible clean fraction1.0이지만 마지막 release=False·clear dwell0·release late2.5478초이므로 새 성공을 통과하지 않는다.
- RH: accepted 목표 통과 `1010:2`, unprepared0·extra1·timing wrong1·현재 recovered=True다. 목표 방향 최초/유일 accepted 오차는85.1353157ms이며 추가/반대방향 통과로 새 성공을 통과하지 않는다. 학습 표본의 `1032:2`와 평가 표본을 혼동하지 않는다.

`native_summary_v1.json`의 집계 범위와 위 결과는 원자료에 일치하며 입력14개 SHA도 직접 확인했다. 실제 결과는 새 측정·보상·PPO·strict load의 연결과 부족한 해제/추가 타현을 검출하는 것을 보여준다. 한 업데이트의 개선·통계적 성공률·장기 수렴·전곡/음향 성과로 해석하지 않는다.

## 최종 문서 확인

최종 phase README·native summary·preservation 보고서를 확인했다. 훈련840전이와 평가840전이, 실제 완료4실행과 Ninja 시작 실패1실행, 새 성공0/1과 timing-only 달성, 이전 저장 궤적 비교와 새 정책 결과를 정확히 구분한다. 물리 지표와 한 업데이트의 의미를 과장하지 않는다. README local 링크19개는 모두 존재하며, 종료 뒤에도 source v2의148개 현재 파일 SHA 변경0을 확인했다. 평가에 별도 runtime import census가 없다는 보존 감사의 한계를 현재 학습의 실측 import 근거와 구분한다.

최종 판정은 문제없음이다. 이 두 검수 파일을 확정하며 추가 수정하지 않는다.
