# 어깨 stiffness 비교 실행·분석·미디어 독립 검수

2026-10-07. 저장된 데이터와 새 분석·그림 producer를 검토했다. 검수자는 native 초기화·시뮬레이션·source query를 실행하지 않았다. 기존 code_review와 동결 결과는 편집하지 않았다.

## 요약

문제없음. Critical/미해결 Warning/Suggestion 없음. 승인된 stiffness 비교의 실행·측정 계약을 확인했으며 기타 안정화 성공을 의미하지 않는다. Stiffness300 미채택·200 진단 기준 유지 판정은 원자료와 일치한다.

## 실행 및 보존 계약

네 fresh 실행은 200/300 각24·120step, 총288step이며 실제 execution 기록의 종료 코드가 모두0이다. Native13계약과 wrapper 계약이 통과했다. 모든 초기 fullstate가 같고 structured PD의 다른 field를 유지한 채 Shoulder6 stiffness만 달랐다. SDK 저장 목표 보존, 상태·목표·PD를 보존하는 완료step1..24/120의 총힘 조회를 확인했다.

기준200의 raw7은 이전 sensor 실행과 exact, 각조건0.5초의 raw7·force 첫0.1초 prefix도 exact였다. Outer 입력94/88개 및 검증 분석131개 SHA가 current였다. source_native의6개 보관 사본 SHA가 manifest와 일치했으며 분석기·결과 문서의 이후 수정과 원래 실행 소스의 시점은 구분한다.

## 독립 수학·시점 검증

4개 실행 전체에서6/30회 업데이트와4tick 목표 유지, actual q 기반 error, 적분 rollback·단조 blocked mask·최대25회 종료, 총보정±0.15rad·C02/native box·이전 실제 전달 목표 기준0.02rad rate를 대조했다. 오른팔 PI clipping과 왼팔 bounded least-squares의 KKT 부호/자유축 조건도 독립 대조했다(자유축 gradient 최대7.3e−17). Float64 계산과 float32 전달의2e−7rad 허용치를 구분했다.

전체 pre-step route의 길이·길이변화율에서 재계산한 cable law는 다음 trace의 last-applied tension과 일치했다. 접촉 행·완료 state·제출 target·힘 샘플 시점을 구분했다. 기타 위치/회전, LH source 이탈, 목표–실제 scalar 차이 및 실제 scalar 한계위반은 저장 데이터와 일치했다.

후처리 첫 acos near-identity 실패는 native 실패가 아니다. 원래 소스·실패 로그를 보존하고 유한0..180° angle의 cosine을 raw quaternion/goal dot과4float64eps로 대조하도록 수정한 것을 확인했다. 원래 angle 관측을 유지한다. 문서화된 인터프리터의 순수 CLI 재실행 결과가 comparison_validated 전체 JSON과 exact였다(`/tmp/shoulder_pd_reviewer_current_djnet34y/comparison.json`). 다른 NumPy 환경의 마지막 재계산 오차 관측 차이는 원자료 변화가 아니다.

## 결과 및 해석

0.5초200→300의 기타 최대 위치/회전오차는36.091149→35.780031mm/4.761921→4.550541°였다. 그러나 종료 위치오차는34.773068→35.780031mm로1.006964mm 악화됐고 LH 이탈90.540508→91.485370mm, L_Shoulder_x gap21.619762→22.803789°, R_Shoulder_z gap17.266792→17.915964°도 커졌다. 실제 arm scalar 한계위반은0.030300→0.043885°였다. LH/RH 접촉은0/135→0/100행이다. 최대값 감소와 종료 개선, target 제한과 실제 state 제한을 구분한다.

## 최종 미디어·문서 검수와 동결

공용 x축이 실제 회전 t=0을 잘랐던 Warning은 독립 x축·모든 panel0..0.5 범위로 해소했다. Gap 선은 실제 완료step1부터 시작한다. Producer 수정 뒤 이전 manifest SHA가 남았던 경계도 새 artifacts_v3 기록으로 해소했고 이전 source/PNG/기록은 보존했다. 인덱스의 main108·최대/최종 설명20 줄 수정도 확인했다. source_plot_v2의 e8425f… 사본은 실행 후 검증 코드가 추가된 workingcopy이며 v2 실행 소스 자체가 아니다. 별도 source_plot_v2_executed에 복원한 소스는 fb2701ec… SHA가 실제 v2 execution과 PNG manifest 양쪽에 exact로 일치함을 독립 확인했다. 복원 방법은 RESTORE_CHECK.json에 기록했고 기존 사본·그림은 보존했다.

최종 지원 CLI를 새 `/tmp/shoulder_pd_reviewer_final_v3_60_m4u7h`에서 실행해 exit0, canonical2340×1475 PNG의 byte/RGBA exact 및 직접 시각 QA를 확인했다.131 upstream·13 direct input·현재 producer·출력 SHA가 일치했다. 결과 README:13/20/22/24/28, VISUAL_REPORT:892/898, 비교 계획:55, PLAN:991과 adapter README:453의 수치·범위·최종 경로가 맞는다.

총 DOF force는 actuator-only 토크·접촉력·effort 포화·PD 부족 원인의 증거가 아니다. Landmark/source proxy는 해부학적 palm normal·cooked clearance·지속 지지 인증이 아니다. 동일 제어 수식에도 상태 피드백과 전달 목표는 달라질 수 있다. 1초·추가 gain은 미측정이며 안정·연주 성공을 주장하지 않는다. 현재 runtime_review를 동결한다. 이후 보존 metadata·검수 완료 표시는 root가 처리한다.
