# 짧은 준비 환경 실제 결과 검수

**요약 판정: 문제없음.** 기본2초 준비 후1초 유지의 실제 연결 결과와 최종 문서의 주장 범위가 일치한다. 기존 사전 검수는 보존했으며 이번 검수에서 CPU 검사·물리 실험·PPO를 추가 실행하지 않았다.

검수 범위: `native_v1` 실행 보고서·초기/준비/최종 기록·241개 raw 상태/접촉/판정·사전 입력 pin, `analyze_native_v1.py`, `native_analysis.json`, 결과 README 및 `guitar_learning/README.md`. 다른 담당자 파일은 수정하지 않고 이 문서만 작성했다.

- 실행 보고서는 completed=true, failure=null, 실제 물리 시간3.0초, import pin 누락0개·원 소스 대조 오류0개·PPO 업데이트0을 기록한다.
- 실제 초기 step0 → 준비 완료480 → 최종720이다. 후속 raw241개 표본의 native/contact/measurement/progress step이480–720으로 연속·일치함을 직접 확인했다.
- 모든 표본에서 고정 목표 현1/5프렛/index의 접촉 후보와 Chest/R_Shoulder/R_Hip 각각의 기타 양성 접촉이 존재한다. 최종 연속 관측 시간은1.0초이며 금지 호출 목록은 빈 배열이다.
- 초기 human DOF 위치·속도 readback 차0, reset setter 횟수 human DOF1·기타 RB1·인간 RB0·position target1을 확인했다. 인간 link pose 최대 차15.413µm/0.01735°는 native FK 재구성의 한계로 명시되어 있으며 전체 solver checkpoint exact를 주장하지 않는다.
- 실행 전 pin1538개를 검수 시 직접 재해시하여 변경0개를 확인했다. 실제 import 목록74개와 보고서의 소스 감사 결과도 보존되어 있다.
- 기타 이동0.489881mm/회전0.067657°는 초기화 직후와 준비 종료 두 시점의 차이다. 준비 구간 전체의 최대값으로 표현하지 않는다. 준비 종료 대비 후속1초의 최대 이동0.040842mm/회전0.005892°와 구별한 분석 및 README가 적절하다.
- 현재 안내는 `guitar_learning.environment`를 기본 진입점으로,2초 기본값/1–2초 옵션을 명시한다. 실제 native 시험은2초 기본값만 수행했고1초 옵션은 CPU 계약 검사 범위라고 구별한다. 이전22초 방식은 재현용으로 보존한다.

이 결과는 한 번의 짧은 reset·제어 인계 연결 확인이다. 전체 V3 안정성·장기 반복 reset·학습된 새로운 압현 동작·현 압력/진동/음향·PPO 성능을 인증하지 않는다. 추가 수정 요청 없음.
