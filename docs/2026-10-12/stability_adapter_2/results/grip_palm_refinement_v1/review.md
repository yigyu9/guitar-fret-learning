# seed2 손바닥 국소 보완 독립 검수

검수일: 2026-10-08. 이번 source 탐색·새 runner/analyzer·저장 raw·최종 v4 산출물·문서와 다음 계획을 검수했다. 기존 동결 자료·공유 코드를 수정하거나 native 실행·source replay를 추가하지 않았다.

## 요약 판정

**문제없음.** 남은 Critical / Warning / Suggestion 없음. 이번 두 조건의 실행·자료·산출물 검수 완료이며 지속 grip·안정성 성공은 아니다.

## 코드·저장 자료

- seed2의 native t0 hull witness를 body-local 고정 proxy로 사용하는 FK fit, 왼팔±.03 / 손가락±.10와 기존 baseline 팔±.3 / native한계의 교집합, alpha 보간을 확인했다. 후보별 full-hull QP 및 사람–기타 / 양손 / graph-distance>2 왼손 LP 교차·palm-up를 재검사하고 최대 gap과 palm gap이 모두 감소해야 admit한다.
- source 8후보·5개 admission 중 선택된 half/quarter만 실제 Gym에서 각5초 실행했다. 새 실행은 2 init / 2400 step이며 이전 seed2의 저장 summary/curve 재사용은 exact다. 저장 기준을 새 실행 수에 합산하지 않는다.
- 저장 actual q / 초기 PD target·비선택48 DOF exact, local / baseline / native box, PD·LA·solver·기타 목표·전체 G 초기 상태 공통을 독립 대조했다. 새 runner의 q·source/FK hard gate는 첫 적분 전에 적용되고 이후 목표 제출·root/하체 유지·부분 기록 경계를 보존한다.
- 배열 길이 1201 state/trace/task와 1200 control/contact, 300회 constant-target 제출 일정, 151 paired camera frame을 확인했다. 분석 6검사 및 3026개 입력 SHA가 일치했다.
- FK 최대 위치 오차는 half .159510 µm / quarter .133921 µm, 회전 오차는 3.03115e−7 / 3.46791e−7 rad로 기록과 일치한다. 저장 G pose로 재계산한 위치 곡선 차이는 3.56e−15 mm 이하, quaternion half-angle cosine 차이는 4.45e−16 이하이며 named-body 접촉 행·양의 λ step·마지막 전체 행 집계는 exact다.

## 최종 미디어·문서

- v4 PNG 두 장을 직접 확인했다. 0–5초 위치 mm / 회전 degree 곡선과 2×3 실제 Gym hands 이미지의 이전 seed2 / 새 half / 새 quarter, t=0 / t=5 프레임 구분이 정확하다. source 렌더나 추가 물리 실행이 아니다.
- producer·font·전체 906 PNG를 포함한 918개 입력의 시작/끝 SHA와 현재 값, 두 출력 SHA, 실제 후처리 exit0 기록을 확인했다. v1–v4 producer 사본은 각 historical manifest SHA와 exact다. 글꼴·여백·입력 봉인 보완은 후처리 네 실행이며 native 재실행으로 세지 않는다.
- 결과표·초기 source gap·목표 유지와 실제 torso 좌표 변화·초기값/영상 링크, CHANGED_FILES / IMPLEMENTATION_FILES의 실제 경로·줄, main README:678 / PLAN:1296 / 날짜 README:439 / VISUAL §72:1325를 확인했다.
- 문서 Warning은 해소됐다: CHANGED_FILES:20의 후처리-only 표현을 산출물 생성 작업에 한정하고 이번 물리 단계의 2 init / 2400 step과 분리했다.

## 검수한 주요 소스 SHA256

- search: `0a1de8a25d4311fd9d4cc40e77cecb748a53b8d40aa7ff5b506b59d7f44a5aa3`
- runner: `5f77e7106feb5329aa4215465cabc650765daaab13db83041c885e6e541c734e`
- analyzer: `48a8f4d76368e1d7b2f9c971cb7b09c111139eae6401af7064276f3ef49a68df`
- v4 artifact producer: `360b6808a9d94ed61eaace529211c621ed48b965d7a6d6b54c7cbe0cc5eaba69`

## 판정 한계·다음 계획·동결

half의 초기 여섯 source gap≤3 mm 달성은 cooked clearance·실제 세 면 접촉·지지 성공이 아니다. 두 후보의 기타 최대 오차 29.575 mm / 8.691°, 28.296 mm / 8.436°는 저장 seed2의 26.773 mm / 8.323°보다 커 미채택이 자료에 부합한다. palm 마지막 양의 λ / 전체 행은 half112/122, quarter142/149 step으로 구분한다. body쌍 기록으로 넥의 면이나 뉴턴 하중·연속 지지를 인증하지 않는다.

SEED2_STRAP_INITIAL_PLAN은 원seed2 각·공통 물리 조건에서 절대 LA만 current / 초기 route / route−5/6000으로 바꾸는 미실행 계획이다. 초기 slack을 유일한 원인으로 단정하거나 초기 law5N을 실행 중 일정 장력으로 해석하지 않는다. 다른 초기자세의 기존 strap 계획·이전 동결 자료는 보존한다.

이 검수 기록을 동결한다. 이후 main 완료 체크 및 source/inventory 봉인은 상위 작업자가 담당한다.
