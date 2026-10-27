# 감싸기 seed2 자세에서 초기 strap 여유 줄이기

grip_palm_refinement_v1의 두 국소 보정은 손바닥 초기 gap을 줄였지만 5초 기타 최대
오차가 각각29.574633mm/8.691355°,28.296015mm/8.435918°로 seed2의
26.772807mm/8.323296°보다 커졌다. 초기 면 근접 개선만으로 자세를 채택하지 않는다.
다음 비교는 이전 multi_face_grip_v3의 seed2 초기각을 그대로 사용한다.

native seed2 initial_values에서 초기 route1.0866096862014567m, 현재 LA1.1018469719600776m다.
약15.237286mm 여유가 있다. route는 정적 초기 계측값이며 스트랩 slack이 기타 이동의
유일한 원인이라고 단정하지 않는다. 현재 기준에서 초기 slack을 줄이는 작은 실험이다.

1. 관절 초기값·G초기p,q·PD·startupoffset 법칙을 동일하게 두고 다음 절대LA를 준비한다.
   - current:1.1018469719600776m
   - 초기 route와 같은 값:1.0866096862014567m
   - 초기 정적 spring law5N 값:1.0857763528681234m(route−5/6000)
2. 각 조건 fresh native 초기 q/포즈/route/source교차/up를 확인하고 실제Gym에서5초씩
   실행한다(3init/3600step). 매조건 초기값·두151frame 영상·원자료를 저장한다.
   반복 baseline도 새 실행으로 구분하고 이전 seed2 raw와 첫24step 재현성을 검증한다.
3. 실제 초기 적용 장력, 직전step에 적용된 장력과 route/속도 변화, 손 body 접촉,
   기타 최대·종료p/q 오차와 몸통9 실제 좌표편차를 비교한다.
   5N은 후보 계산용 초기 정적 law 값이며 지속 장력·native force sensor 인증이 아니다.
   float32 계산과 첫step route 변화 때문에 실제 장력은 직접 기록해 확인한다.

기존 spring6000N/m/damping120N·s/m/cap300N law는 유지하며 새 인위적 힘을 추가하지 않는다.
G자유/root하체고정/몸통9 목표/양쪽66 제어 경로/selfcollision 조건을 유지한다.
기타 고정·강제 부착·지속 pose 쓰기는 사용하지 않는다. 실제오차feedback·학습은 아직 없다.

코드/trial은 stability_adapter_2에, 결과는 docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1에 둔다.
기존 STRAP_FIVE_SECOND_PLAN은 다른 초기자세의 미실행 계획으로 보존한다.
이 계획은 아직 실행하지 않았다.
