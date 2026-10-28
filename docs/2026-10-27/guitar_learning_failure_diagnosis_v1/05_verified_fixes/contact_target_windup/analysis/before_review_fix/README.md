# 고정 tape 세 조건 분석 준비

CPU 전용이며 기존696봉인·driver·raw·활성 소스를 수정하지 않는다. raw가 없으면 readiness만 출력하고 결과 폴더/수치/그림을 만들지 않는다. root가 세 native 실행을 끝낸 뒤 프로젝트 루트에서 실행한다.

```bash
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_windup/analysis/analyze.py --self-test
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_windup/analysis/analyze.py --status
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_windup/analysis/analyze.py
```

입력은 run_original/run_no_new_inward/run_no_new_inward_and_relax의 원래 physics240/control60/target_control60·128 episode/음 원장·평가·세 report·settings·전후 pin, 그리고 original_launcher.json/no_new_inward_launcher.json/no_new_inward_and_relax_launcher.json이다. source는 봉인된 contact_load_probe/run_final300_policy다. 런타임 보고를 신뢰하는 것과 별개로 아래를 NumPy로 재계산한다.

1. 원본 조건의 **모든 physics/control 배열·128 음 원장·evaluation 값**이 source와 exact인지, 세 조건의 첫480 **모든 physics 배열 필드**가 exact인지 검사한다. report의 경로·실행시간 metadata는 상태 동일성에 섞지 않는다. 원본 재현 또는 prefix 불일치가 있으면 matched 효과 해석을 보류하고 차이 필드를 명시한다.
2. 첫128 전체 성공·물리/손목 실패 분모, 원래 clock·4substep·동일 실패 endpoint부터 latch, 실제9보상 increment/cumulative/episode 및 최종 음 원장 일치를 확인한다. 힘은 실패 endpoint와 이후를 제외하며 pooled240Hz 통계와 환경별 peak를 구분한다. 노출0은 null이다.
3. 실제 guitar pose의 press/rear normal로 중지·엄지 resultant와 signed normal의 before/audible/after p50/p95/max를 구한다. 엄지 press와 rear의 부호 기준을 섞지 않는다. per-env peak는384행 모두 남긴다.
4. 추가60Hz는 **control 시작 시각**으로 구간을 나누고, 끝에 실패가 발생한 control 전체를 보수적으로 통계에서 제외한다. 모든 first control의 gate/skip/개입 수와 gate true 무실패 구간의 고정Jn target error·증분·접선변경·실제/예측 점속도 잔차를 분리한다. gate가 꺼진 행의 저장0을 실제0오차로 해석하지 않는다. gate/normal/J/dot/box/rate/tolerance와 prefix 무개입을 독립 재계산한다. rate/native/action **교집합 box** 경계 체류와4rad/s 경계를 기록하며 식별불가한 native 단독 체류를 주장하지 않는다.
5. 같은 clock/env의 original 대비 arm12 요청·손목오차 변화도 남긴다. 첫2초 일치 후 teacher feedback이 달라질 수 있으므로 선택4만의 고립된 효과로 해석하지 않는다.

완료시에만 results_v1/의 한국어 RESULTS.md, summary.json, force/control/environment/reward CSV, 작은 summary.png, raw SHA 및 독립 재계산 verification.json을 쓴다. 기존 results_v1은 거부한다. 검산 실패는 새 폴더의 verification.json에 오류를 보존하고 성공 보고서를 만들지 않는다. 실행 후 별도 change-reviewer 검수를 요청한다.

body resultant는 접촉쌍 압력이 아니다. 고정 material point는 any-candidate witness 인증점이 아니다. Jn·큰 target−q는 국소 선형 외삽이며 침투깊이가 아니다. 속도 잔차와 실제 속도를 함께 제시하고 큰 잔차의 방향 해석은 보류한다. 접선 보존·저부하 성공·새 힘 상한·일반 controller 채택·정책 단독 인과 해결을 미리 주장하지 않는다. 현재 파일은 분석 실행 전 명세와 합성 검사만이며 native 결과는 없다.
