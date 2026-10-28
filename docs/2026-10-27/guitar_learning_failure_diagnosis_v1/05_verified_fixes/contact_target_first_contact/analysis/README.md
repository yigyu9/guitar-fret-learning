# 첫 접촉 timing 실제 결과 분석 준비

현재는 **자료 대기/CPU 합성 검사만** 한다. 기존739봉인·producer·원자료를 수정하거나 GPU를 실행하지 않는다. 결과 파일·수치·그림은 run_01과01_launcher.json의 실제 종료 기록이 모두 준비된 뒤에만 생성한다.

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=. /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_first_contact/analysis/analyze.py --self-test
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_first_contact/analysis/analyze.py --status
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_first_contact/analysis/analyze.py
```

기존 contact_target_windup/analysis/results_v1의 검수된 original·2초 지연 no_new_inward summary/CSV를 그대로 읽고 SHA를 확인한다. 이전 세 조건 전체 감사 도구를 다시 만들거나 이전 raw 전체 통계를 다시 계산하지 않는다. 새로운 run_01만 기존 단일조건 analyze() 감사 함수에 연결한다. 연결 차이는 경로·first_contact_report 이름·새 gate 검사·환경별 실제 첫 변경 prefix 감사다. 기존 모듈의 임시 연결은 호출 뒤 복원한다.

`target_checks()`는 기존 수학/box/rate/접선/alias 검산과 동일하며 **clock>=480 gate와 첫120 무개입 assert를 제거**한다. 원래 함수의 고정480 prefix 비교도 실행하지 않고 새로운 driver의 env별 실제 first-change prefix로 대체한다. 힘/성과 시간창은 원래 actual local time, control은 start clock이다. gate 꺼짐의 저장0을 실제0으로 평균하지 않는다.

새조건도 모든128 성공·clean 유지·wrong·물리/손목 실패를 보존한다.240Hz 힘은 실패 endpoint부터 제외하고,60Hz 개입/투영 통계는 실패로 끝난 control 전체를 보수적으로 제외한다. 중지/엄지의 audible·after resultant와 실제 guitar pose 기준 signed normal, target/rate/부호/접선·고정점 속도잔차·팔 teacher 혼입·원9지급/원장은 기존 감사 함수를 재사용한다. 원래 두 조건의 full-source/480-prefix exact 전제와 신규조건의 실제 first-change 이전 physics30필드/전체control exact 및 전체tape 일치를 함께 확인한다.

추가로 환경별 첫 gate/첫 실제 target change(없으면null), 그 control 시작 직전 실제 중지 resultant/signed force, old target−actual4의 norm/4축값·고정Jn proxy를256행 event CSV에 남긴다. gate와 실제 변경은 다르며, 중간 physics tick의 최초 load와 다음60Hz control에서의 개입 시각도 구분한다. fixed material point는 source clock480에서 사전선택한 점이며 최초 any-candidate witness 인증이 아니다.

완료 시 새 results_v1/에 한국어 RESULTS, 비교 CSV/summary, 작은 그림, input SHA/검산 verification을 쓴다. 기존 output은 거부하고 오류는 새 verification에 보존한다. 자료가 없을 때는 readiness만 반환한다. 실제 결과와 신규 event 비교는 별도 독립 검수 후 보고한다.

body resultant는 접촉쌍 압력이 아니고 큰 Jn·target 오차는 침투 mm가 아니다. 같은 tape라도 팔 feedback/실제 자세/접선운동이 바뀐다. 최초 하중 억제의 하중/성공 효과를 자유 손 production 개선·정책학습 성과·새 힘 상한 해결로 확대하지 않는다. 이번 준비에는 실제 결과가 없다.
