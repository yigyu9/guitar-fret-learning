# seed2_strap_initial_v1 독립 검수

검수일: 2026-10-08. 대상은 새 입력 준비기·실행 래퍼·저장자료 분석기와 canonical artifacts_v3, 결과·누적 문서 및 다음 시작 목표각 계획이다.
검수 중 native 초기화·physics·source replay·그림 재생성은 하지 않았다. 원자료와 구현 파일을 수정하지 않았으며 이 기록만 작성했다.

## 요약 판정

**문제없음.** 남은 Critical / Warning / Suggestion은 없다. 실제 실행은 3 fresh 초기화·3600 physics step이며, 저장자료 후처리는 별도로 구분한다.

## 코드·원자료 확인

- 입력 준비기는 이전 seed2 전체 설정을 복사하고 절대 LA만 current / route / route−5/6000으로 바꾼다. 이전 입력 closure와 새 계획·프로듀서를 읽기 전후 봉인한다.
- 실행 래퍼는 선언된 trial SHA를 확인하고 integration 전에 실제 81 q·native 범위·초기 Python PD 목표·초기 route·선언 LA 및 fresh FK/source/up 검사를 요구한다. 기존 66 목표 합성·몸통9 목표·root/하체 고정·자유 기타·PD·5초 녹화 경로를 보존한다. 사전검수 뒤 추가된 strap 계수 metadata는 물리 변경이 아니다.
- 분석의 8검사와 3339개 입력 SHA를 확인했다. 세 조건의 초기 전체 상태·PD·기타 목표·상수 offset 조건, 1201/1200 저장 범위·60Hz 갱신 및 두 뷰151프레임을 검사하는 코드 범위를 확인했다.
- NumPy 독립 재계산에서 각 조건 1200개 force-law 구간 모두 오차가 정확히 0 N이었다. trace[k−1]의 route 위치·속도로 계산한 scalar를 완료 상태 trace[k]의 last_applied 값과 대조하며, 그래프 시각은 해당 구간 시작이다. native 힘 센서 값이 아니다.
- current의 states / trace / tasks / contacts / controls는 첫24step 및 전체5초 모두 이전 seed2 배열과 exact였다. 전체5초 exact는 관측값으로 구분한다.
- 실제 preload LA는 1.0857763528681235 m, 첫 제출 law scalar는 4.999999999999449 N이다. 소비된 leaf 계획의 …1234와 1 ULP 차이를 공개하며 지속5N으로 해석하지 않는다.

## 미디어·문서와 수정 해소

- 두 PNG를 직접 확인했다. 세 곡선의 축·단위·범례와 0~5초 범위, 마지막 law 입력1199/240초 및 실제 Gym 카메라 0/5초의 2×3 조건 배열을 확인했다. canonical v3 두 PNG는 확인한 v2 PNG와 바이트가 같다.
- v3 실행 종료0·로그/manifest SHA, 919개 입력 시작/종료/current SHA 및 두 출력 SHA가 일치한다. 보존한 v1/v2 producer 사본은 각각 당시 manifest producer SHA와 exact다. 재현 CLI를 별도로 실행하지 않았다.
- 마지막 law 샘플의 축 잘림, README의 이전 실행/manifest 링크, 초기 route 차이 표현, 전체5초 exact 관측값의 plot gate를 해소했다. producer는 해당 값의 bool 형식만 요구한다.
- README:22와 VISUAL §73은 ‘여섯 부위 모두3mm 이내’ 통합 조건 미달을 명시한다. 개별 여섯 gap이 모두 실패했다는 뜻으로 쓰지 않는다. 초기 route/pose는 같고 LA만 다르며 카메라로 strap 길이를 구별한다고 주장하지 않는다.
- 결과 README·CHANGED_FILES·IMPLEMENTATION_FILES의 절대 경로/줄 링크, main README:691 / PLAN:1314 및 날짜 문서의 §73 연결을 확인했다. 남은 pending/체크 표시는 root의 최종 상태 갱신 범위다.

## 검수한 소스 SHA256

- prepare_seed2_strap_trials.py: `a64bfbe7be08dfd0a7cac11a5420012a459b6a36f0434f87910b7100d3021780`
- run_seed2_strap_initial.py: `ef7ef5dc6c681d4d6a92f3ce78a98334967348ea189320fae7d5567aa1ea9759`
- analyze_seed2_strap_initial.py: `a12a393f29c8834bfcfc5025a6525ce41bbc4e810d19570139ca27a19c1278d6`
- make_seed2_strap_initial_artifacts.py: `81888b6af9214fbda0e946e3ee6cad2d19b6bd92cab8f5f912bc225181db4d82`

## 판정과 남은 한계

짧은 LA는 처음0.1초 두 오차를 줄였지만 5초 최대 위치 오차와 종료 위치·회전 오차를 악화시켰다. 최대 회전 오차 감소와 이 악화를 구분하여 current를 다음 진단 기준으로 유지하는 판단이 타당하다.
named-body의 양의 lambda 마지막 step과 전체 접촉행 마지막 step을 구분한다. 넥 rear/front/side 분류·연속 하중·cooked clearance·완성 grip·안정화/연주 성공을 인증하지 않는다. 유지되는 PD 목표가 실제 몸통 상태 고정을 뜻하지 않는다.
SEED2_STARTUP_TARGET_PLAN의 왼팔12 bias 0/.5/1 비교는 아직 미실행이다. 첫 Shoulder_x 목표 변화 −17.0104°는 좌표 목표 변화의 관찰이며 기타 움직임의 원인이나 전체 관절 SO(3) 회전으로 확정하지 않는다. 이 검수 기록은 최종 동결 가능하다.
