# 세 면 접근 초기 자세와 동일 절대목표 비교

엄지는 기타 넥 후면, 검지·중지·약지·소지는 전면, 손바닥은 옆면을 지지하는 초기 후보를 비교한다. 직접 종료각 보간은 상대offset 한계로, 명시적 초기각 투영은 사람–기타 source 교차로 거절됐다. 두 준비 단계는 native0과 로그/소스를 보존한다.

기존 grip_palm_refinement_v1의 w1_a0p25/0p5는 source 형상 안전검사와 fresh native 초기 FK를 통과했다. half는 여섯 source hull–면 패치 거리가 모두3mm 이하였으나 이전5초시험에서 기타 이동을 개선하지 못했다. 당시에는 초기각과 절대 PD 목표가 함께 달라졌다. 이번에는 그 초기33각만 가져오고 저장 constant_0p016의 절대81 PD 목표를 유지해 초기 배치 효과를 분리한다. 과거 결과를 새 실행으로 세지 않는다.

1. 저장 source-verified quarter/half의 왼쪽33 초기각을 native float32로 변환한다. 나머지48 초기각, 몸통9 PD목표·오른팔손·root하체물리고정, 기타초기/목표p/q와속도·절대LA·PDgain·solver는 유지한다.
2. 팔12는 C02±.3 및 native hard limits, 손가락21은 native hard limits, 모든 relative offset은±.3을 검사한다. 합성은 float64 후 float32로 하고 절대81 목표를 저장값과 exact 대조한다. clipping이나 body pose/속도 transfer를 하지 않는다. 최종66 제어권은 그대로다.
3. source 기타/양손/비인접 왼손 교차와 palm-up 반구를 다시 검사한다. 엄지 후면/네손가락 전면/손바닥 옆면의 거리·면 방향을 측정한다. 거리≤3mm는 품질 관측이며 cooked 접촉 인증이 아니다.
4. baseline repeat와 source허용 quarter/half 최대2개를 fresh native 초기 FK 검사 후 각5초 실행한다. 매실험 초기값/실제81각/절대목표와 실제 Gym 전신·손0~5초151frame 영상을 저장한다. 초기검사 거절시 t0·부분영상·오류를 남긴다.
5. 최대/종료/첫.1초/마지막1초 G오차, 손바닥/엄지/각손가락/허벅지 접촉·몸통 실제각·수동strap 법칙을 분석한다. baseline5raw 배열/영상 exact는 관측이며 새controls는81목표 schema로 달라질 수 있다. Sol 분석 후 Luna 이미지설명/문서, 독립 검수, 기존 SHA 보존 검증을 수행한다.

자유 기타에 목표힘/고정/강제 손부착/지속pose 덮어쓰기는 없다. 초기6부위 접근과 실제 body접촉, 면별 지속지지는 구분한다. 정식 안정화 성공과 학습구조는 아직 결정하지 않는다.
