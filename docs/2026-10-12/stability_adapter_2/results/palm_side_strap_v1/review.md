# palm_side_strap_v1 독립 검수

검수일: 2026-10-07. 새 runner/analyzer/plotter·네 입력·이번 원자료·최종 문서/그림을 검수했다.
이 기록만 작성했으며 이전 동결 결과와 다른 작업자 파일은 변경하지 않았다.
검수 중 native 초기화·physics 실행·source replay는 0회다.

## 요약 판정

문제없음. Critical / Warning / Suggestion의 남은 항목은 없다. 이 기록을 동결한다.

## 구현·원자료 확인

- 네 설정은 절대 LA만 변경한다. 기존 초기 q·기타 p/q·PD·normal .08/cap .3 bias·PI·nonleft 목표·root/하체 고정·self collision·66목표 경로를 유지한다. 실행 중 길이 변경·기타 인위적 제어힘·state 덮어쓰기는 없다.
- LA 1.1018469719600776/1.0804741130331008/1.0796407796997676/1.078807446366434m의 최초 수동 law 값은0/0/5/10N이다. 저장된 모든 pre-step route/속도에서 재계산한 장력과 다음 trace의 last_applied 값 차이는0이었다. 초기 law와 runtime 일정힘은 구별된다.
- 9init/124steps, 초기 fullstate exact, current 이전4raw exact, 네 first-step→short6배열 prefix와 camera/headless6배열 exact를 독립 확인했다. task 재계산 차이는 최대5.56e-17, PI·rollback·최종 clipping 차이는2.99e-16 이하, float32 목표 전달 차이는6.23e-8rad 이하로2e-7rad 허용치 안이다.
- 원래 생성 목표와 초기 shift에서 기타 p오차를 재계산한 차이는4.34e-19m 이하, 회전오차 cos 대조는1.12e-16 이하다. 종료 속도는 저장 native velocity norm과 일치한다. 최종 analyzer10계약/184개 실제 입력 SHA가 현재 파일과 일치한다.

## 지적 해소·그림·문서

보존 판정에 소비한 inventory의 SHA 누락과 camera overlay helper SHA 누락 Warning을 해소했다. 두 inventory는 분석 시작 전에 봉인하고, 실제 overlay helper는 사용 전에 manifest 입력에 포함한다. 기존 analyzer/분석·plot producer/그림/manifest는 보존했으며 저장 자료 재분석·재생성만 수행했다.
최종26개 plot 입력·producer·두 출력 SHA가 일치하고, 이전 producer 사본은 최초 manifest SHA와 exact, 두 PNG는 최초 그림과 byte-identical이다. 두 그림을 직접 확인했으며 단위·범례·전체0–0.1초 범위·같은 시점 source 표식이 맞다. CHANGED_FILES의 절대 경로와 실제 줄 링크도 유효하다.
README:3/12/14/18의 네 조건 집계·10N 양의 raw lambda 예외·직전 step 장력 시점·이번 native camera 실행 구분을 확인했다. t0 last_applied=0은 적용 전 초기값이며 초기10N law를0N으로 해석하지 않는다. 실제 plot 재현 명령/환경에 MUJOCO_GL=disable가 기록됐다. import 실패는 plot 후처리이며 original/v2 analyzer 실행은 모두exit0이다.
EXPERIMENT_WORKFLOW.md의 새 입력 봉인 매뉴얼은 소비한 helper/inventory·실제 import 환경·시점·이전 producer 보존을 명시하는 품질 규칙이며 물리 조건이나 성공 기준을 바꾸지 않는다.

## 검수한 현재 소스 SHA256

| 파일 (`/home/ajou/yigyu/3/stability_adapter_2/`) | SHA256 |
|---|---|
| run_palm_side_strap.py | 4ac5bbc852cc9e05d3c554ead1819cc93540acf407108f68cbf8ae44fbb81c27 |
| analyze_palm_side_strap.py | bbaf264ea158f6e6cf02a9b58a3f17bc4a641f1b8aaf395a111afd689ced8891 |
| plot_palm_side_strap.py | e43dbf14d3a5213badd8556408feac85cc107fe74b32d23dbbd61c8c64dee51b |

## 최종 결과와 한계

10N 조건의0.1초 기타 최대오차2.536296mm/.356604°는 current5.107730mm/.969008°보다 작지만 첫 step은 악화했다. Palm15행은step1–4이고 양의 raw lambda .669739902는step1 단1행뿐이며 이후 접촉이 없다. 종료장력0과 속도.071236m/s/.181603rad/s가 남는다.
5N의 종료 속도 .057018m/s/.129383rad/s와 장력1.996061N도 함께 읽어야 한다. 손바닥의 지속 하중·cooked 접촉점·안정성·연주 성공을 인증하지 않는다. 10N은 최종 길이로 채택하지 않으며 다음 동일 네 조건0.5초 진단은 별도 실행·집계로 남겨야 한다.
