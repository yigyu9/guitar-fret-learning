# seed2_startup_target_v1 독립 검수

검수일: 2026-10-08. 새 준비기·실행 래퍼·분석기, 저장된 세 실행, canonical 그림·manifest·결과/누적 문서 및 다음 기타 응답 식별 계획을 검수했다.
검수 과정에서는 native 초기화·physics·source replay·producer 재실행을 하지 않았다. 원자료·구현·타인 문서를 수정하지 않았으며 이 기록만 작성했다.

## 요약 판정

**문제없음. Critical / Warning / Suggestion 없음.** 실제 실험은 3 fresh 초기화·3600 step이며 저장자료 그림 후처리 두 번과 구분한다. full을 다음 진단 기준으로 유지하는 판단은 타당하나 안정화 성공을 의미하지 않는다.

## 코드·저장 원자료 확인

- 준비기는 이전 current 전체 trial을 복사하고 정확히 왼팔12 startup offset만 0/.5/1배로 바꾼다. 입력 closure 및 새 producer/leaf를 시작·종료 봉인한다. 래퍼의 기존 제어·5초 녹화·부분 결과 보존 경로는 유지하고 비왼팔69 목표 유지 검사를 강화했다.
- 분석 8검사와 4292개 입력의 current SHA를 확인했다. 세 조건의 초기 전체 상태·PD·LA·physics·기타 목표가 이전 current와 exact였다. 실제 초기81 q/FK/source/up 검사는 integration 전에 수행한다.
- 저장된 각1200 제출 목표가 float32 초기q+scaled offset을 native 범위로 clip한 결과와 exact였다. 각300회/매4step 갱신과 상수 목표를 확인했다. 비왼팔69 예상 목표는 초기q와 같고 runner의 유지 검사도 true였다. 이는 기록된 Python 목표 제출/검사 범위이며 새 SDK 목표 getter 계측을 뜻하지 않는다.
- 최대 목표 변화는 0/8.505211955/17.010423911°이며 세 조건 모두 target clipping은 없었다. 실제 왼팔 좌표의 초기q 대비 최대 편차 18.427194683/12.256113645/12.444310970°를 독립 재계산해 저장 통계와 exact 일치를 확인했다.
- 1201 states/trace/tasks 및1200 controls/contacts 범위, full의 첫24step과 전체5초 states/trace/tasks/contacts/controls가 이전 current와 exact인 것을 독립 대조했다. 전체5초 exact는 별도 관측 bool로 저장하고 그림 성공 조건으로 요구하지 않는다.
- 각조건1200 구간의 trace[k−1] route 위치·속도에 수동 strap law를 적용한 값과 trace[k]의 last_applied scalar 오차는 독립 NumPy 계산에서 모두0 N이었다. LA는 상수다. OFF/half 최대 scalar0 N, full 최대21.026342503 N이며 native 힘 센서 측정이 아니다.
- LH/RH↔ANY 기타 body의 rows/양의 raw lambda rows/unique steps/마지막 전체행을 원시 접촉에서 재집계해 전체 dict가 일치했다. RH는 세 조건 모두 빈 dict다. full thumb3/index3/middle3 마지막 양의 기록1200, palm 양의121/전체행134를 구분한다.

## 그림·문서·보존본 확인

- 두 canonical PNG를 직접 확인했다. 위치mm·기타 SO(3) 회전도·실제 scalar 좌표 드리프트/목표 변화의 세 패널과0~5초 축, 점선/실선 구분이 읽힌다. 별도 최댓값을 같은 관절의 tracking error로 해석하지 않는다. 카메라 표는 실제 각실행 step0/1200의2×3 저장 프레임이다.
- canonical919 입력 시작/종료/current SHA 및 두 출력 SHA, 실제 후처리 종료0·로그·manifest SHA가 일치했다. 첫 glyph 초안 producer SHA와 archive 이미지 바이트는 당시 manifest의 기대 SHA와 일치했다. 보존 manifest의 원출력 경로와 현재 archive 위치는 구분해 대조했다.
- 첫 후처리는 성공 exit0이지만 U+2212 글꼴 표시 문제가 있었고, ASCII 표기로 수정한 두 번째 후처리가 canonical이다. 추가 native가 없다는 설명은 산출물 작업 범위로 한정한다.
- README:13의 bias 묶음 영향/특정 Shoulder_x 원인 구분과 target clipping 표현, full↔이전current exact 문구, 통합 all6≤3mm 미달 및 LH/RH contact 한계를 확인했다. README·CHANGED_FILES·IMPLEMENTATION_FILES의 절대 파일/줄 링크와 main README:711 / PLAN:1342, 날짜 README:459 / VISUAL §74:1355 연결을 확인했다.

## 검수한 소스 SHA256

- prepare_seed2_startup_trials.py: `e20d958025a798afca32395f5e1be7eb9b40e28ddd9151751c95a337ea378c34`
- run_seed2_startup_target.py: `a87a43783f0c463d081083a9fc16258e38e1d994ac1c0d4d8fd604cb41526692`
- analyze_seed2_startup_target.py: `b598d92ff826017aabdd1419c950ba7ced4b6e89faf5fd4ca99afc93454c4c2e`
- make_seed2_startup_target_artifacts.py: `b2662ce2763635e39adf7e4df52b708f58534a04fcfca56113cf3ca40c00e52d`

## 판정과 미검증 범위

OFF/half/full의5초 최대 기타p/q 오차158.087560mm/26.354560°,120.156654mm/21.523804°,26.772807mm/8.323296°를 구분해 full을 유지한다. 팔12 bias 묶음 비교의 결과이며 특정 축·중력·모터 포화를 단독 원인으로 입증하지 않는다.
q_actual−q_initial 및 q_target−q_initial은 서로 다른 좌표 지표이고 q_actual−q_target tracking error나 전체 관절 SO(3) 각도가 아니다. 몸통9·손가락·오른팔 목표 유지가 실제 상태 고정을 뜻하지 않는다. 양의 lambda 기록의 끝점만으로 지속 지지·rear/front/side 면별 접촉·뉴턴힘·cooked clearance·완성 grip·연주 성공을 인증하지 않는다.
SEED2_GUITAR_RESPONSE_PLAN은 아직 미실행이다. 66 연주 목표+지지 bias+기타 residual의 합성과 몸통9 목표 유지 관계를 설명하고, 같은초기/full/LA에서6probe(+.002rad)와 결합 heldout(축별±.001rad)을 최대8init/9600step으로 검증할 계획이다. 실제 float32 적용량·clipping·예측/실측 비교 후 판단하며 새 runtime 기타 feedback·학습은 구현하지 않았다. 이 검수 기록은 최종 동결 가능하다.
