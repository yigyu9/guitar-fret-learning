# 왼팔 강성 단독 비교 독립 검수

검수일: 2026-10-08. 검수 범위는 이번 analyzer, 세 설정·저장 실행 결과, 최종 산출물·문서와 다음 단계 계획이다. 기존 동결 자료를 수정하거나 native 실행을 추가하지 않았다.

## 요약 판정

**문제없음.** 남은 Critical / Warning / Suggestion 없음. 이번 3조건 비교의 기록·분석·산출물 검수는 완료했으며, 지지·안정·연주 성공을 뜻하지 않는다.

## 코드·저장 자료

- 실제 3회 초기화·3600 physics step, 조건별 1200 step / 5초 / 두 카메라 뷰의 각 151프레임을 확인했다. 초기 자세·기타 목표·절대 LA·constant target 및 다른 PD 필드는 같고, 왼팔 12축 stiffness만 1/1.5/2배이며 damping은 고정이다.
- 분석 7개 검사와 1418개 입력 SHA, 초기 상태·named 66 목표 연결·300회 목표 제출 일정 및 held target, capture의 두 뷰와 기록된 프레임 SHA를 확인했다. 기존 기준의 첫 24 step 원자료 일치 범위를 유지한다.
- 저장 native pose로 source 추적점·움직이는 패치 법선 간격·기타 위치오차를 독립 재계산했다. 회전오차는 정규화 quaternion의 abs-dot과 저장 각도의 half-angle cosine을 대조했다. 최대·종료값 및 접촉 행/step 집계가 분석과 일치한다.
- 사전 Warning 두 건은 해소됐다: 기록된 capture SHA·두 뷰 검사 누락과 baseline constant-target 검사 누락을 각각 analyzer:84–88, :72–75에서 보완했다. 추가 물리 실행 없이 검수했다.

## 최종 미디어·문서

- 최종 PNG 두 장을 직접 확인했다. 곡선 단위·전체 5초 범위·음수 간격 표시와 카메라 2×3의 실제 프레임 6개(전신 t=0 / 손 t=5초)가 저장 자료와 일치한다. 26개 산출물 입력 SHA와 두 출력 SHA, 실제 실행 종료 기록을 확인했다.
- 이전 producer 사본은 당시 archived manifest SHA와 일치하고 이전 이미지도 보존돼 있다. 추가 6개 검증 입력 프레임과 실제 표시 프레임 6개를 구분한다. 151프레임 영상의 컨테이너 5.033초와 시뮬레이션 5.0초를 구분한다.
- README:13의 실제 torso drift / 유지된 9개 목표 구분, :23의 kd 고정·kp 비교와 kd 독립 효과 미검증, :33의 세 초기값 링크 수정을 확인했다. CHANGED_FILES·IMPLEMENTATION_FILES와 상위 README:657 / PLAN:1262 / 날짜별 README:414 / VISUAL_REPORT:1274의 실제 경로·줄 연결을 확인했다.
- 다음 STRAP_FIVE_SECOND_PLAN은 같은 kp=1, kd=1에서 고정 LA 세 조건을 각각 5초 비교하는 미실행 계획이다. 초기 5 N 법칙은 실행 중 일정 힘이라는 뜻이 아니다.

## 검수한 소스 SHA256

- `analyze_palm_stiffness_only.py`: `d43668c7cab2545d2a264a4b03b297d8e0c2365a59256025391fde21d07428f9`
- `make_palm_stiffness_only_artifacts.py`: `4b730086e85ffee1e54f1fb4b878f7f1fc73dd635f48359c4a9ea54993e0e9e0`

## 해석 한계·동결

kp 상향의 5초 최대 기타 오차는 기준 82.047 mm / 10.831°보다 크게 악화됐다. kp=1, kd=1 유지와 상향 후보 미채택은 자료에 부합한다. 음수 source 간격은 움직이는 유한 패치 투영값이며 cooked 관통 깊이가 아니다. raw λ, 접촉 기록, palm-up proxy만으로 지속 지지력·안정성을 인증하지 않는다. 실제 DOF 좌표 성분의 torso drift를 whole-joint SO(3)나 원인으로 해석하지 않는다.

이 검수 기록을 동결한다. 이후 체크리스트·최종 source/inventory 보존은 상위 작업자가 담당한다.
