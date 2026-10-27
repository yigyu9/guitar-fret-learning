# palm_support_weight_v1 독립 검수

검수일: 2026-10-07. 새 runner/analyzer/plotter와 이번 세 조건의 원자료·문서를 검수했다.
수정 범위는 이 검수 기록뿐이며 기존 동결 결과와 다른 작업자의 파일은 변경하지 않았다.
검수 중 native 초기화·physics 실행·source replay는 0회다.

## 요약 판정

문제없음. Critical / Warning / Suggestion의 남은 항목은 없다. 이 기록을 동결한다.

## 구현·원자료 확인

- 방향 scale .08/.02/0을 응답행렬·startup baseline·FK·feedback error에 일관되게 적용한다. .08 bias는 저장값을 사용한다. 순수 계산에서 세 bias/inverse의 유한값과 최종 box를 확인했고 scale0은 orientation inverse 열이 정확히0이다.
- 같은 초기 q·기타 p/q·절대 LA·PD·몸통/오른팔/손가락 목표·root/하체 고정·self collision과 66축 목표 경로를 유지한다. 초기각과 runtime initial±.3∩native 목표 box를 구별하며 state 덮어쓰기는 없다.
- 저장 pose에서 세 task를 다시 계산한 차이는 최대5.56e-17이었다. 총18회 업데이트의 PI·적분 rollback·최종 clipping·잔차±.15rad/rate1rad/s를 독립 계산한 차이는 최대1.54e-16, 실제 float32 target 차이는 최대6.26e-8rad로 2e-7rad 허용치 안이다.
- 3init/72steps, 각25상태·24제어/접촉·6update, 초기 state exact 및 .08 기준의 states/trace/contacts/normal_tasks exact를 확인했다. 첫-step tracking오차 .08500494mm는 과거 bias-only .08500153mm와 별개의 제어 조건이다.
- analyzer6계약과125개 입력 SHA가 현재 파일과 일치한다. 이전 phase 보존 검사와 실행 exit0 기록이 연결돼 있다. 초기 후처리 EGL import 실패는 보존됐고 물리 실행 실패나 추가 native로 집계하지 않는다.

## 그림·문서 확인

최종 PNG를 직접 확인했다. 14개 입력·producer·출력 SHA가 manifest와 일치하고 표/곡선의 단위·범례·전체0–0.1초 범위가 맞다. scale0의 법선각도 weighted tasks가 아닌 원래 normal_tasks의 .08m/rad를 기준으로 계산하므로 방향항을 제거했다고 측정 각도가0으로 표시되지 않는다. CHANGED_FILES의 실제 절대 경로/줄 링크가 유효하다.
평행성은 지지를 위한 선택적 선호로 기술하며 bias와 feedback을 함께 바꿨다는 한계를 설명한다. 접촉 우선 제어가 새로 구현됐거나 해부학적 법선·PhysX cooked 여유·힘이 인증됐다고 주장하지 않는다.

## 검수한 현재 소스 SHA256

| 파일 (`/home/ajou/yigyu/3/stability_adapter_2/`) | SHA256 |
|---|---|
| run_palm_support_weight.py | f52b28e5de4bea35042ccb053e7ae3cb1e14bfe5f4ab94774f70930c639a58f7 |
| analyze_palm_support_weight.py | ceaa2ca5bb35feccb6113155e6ec0fb92cac429170dcb034f2996f869b2fb364 |
| plot_palm_support_weight.py | 0f1b2af79398fbcfba8db17f6baceb060c9c4d0c9ac56fe570252d02ceec6d87 |

## 최종 결과와 한계

추적점 최대오차는 .08/.02/0에서12.186877/12.447904/17.168120mm, source 법선각 최대는1.280689/1.281836/6.954837°다. 기타 body states는 세 조건 모두 기존 기준과 exact이고 최대오차5.107730mm/.969008°도 같다.
.08/.02는step1–2의7palm 행,0은step1–3의10행이 모두 raw lambda0이며 이후 기록이 없다. 한 step 추가 접촉 행을 지지력이나 하중 개선으로 판정할 수 없다. 방향 가중치 완화의 지속 접촉·기타 안정화 개선은 관측되지 않았으며 .08/±.3은 기존 진단 기준으로 남는다. 0.1초 결과를 후기 안정성·원인의 단독 확정·연주 성공으로 확대하지 않는다.
