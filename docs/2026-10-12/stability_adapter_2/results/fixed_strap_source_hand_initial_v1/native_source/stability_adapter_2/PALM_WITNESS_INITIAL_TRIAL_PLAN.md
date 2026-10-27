# 손바닥 witness 기반 초기 자세의 실제5초 비교

## 실행 이유와 구분

coupled_palm_witness_v1의 첫 source 검색은 초기 full 제안에서 손바닥 patch 간격
0.421669522→0.109504850mm와 비연결 source 교차0을 얻었다.
최대 초기각 변경은0.00261648rad(약0.15°)다. 중간0.5초 방향에는 손가락 교차가 남으므로
이를 runtime 보정 정책이나 지속 접근 방향으로 채택하지 않는다.

이번 별도 actual trial은 **초기 자세와 이에 대응하는 유지 목표**의 작은 변경이
초기 기타 이탈/손바닥 접촉에 도움이 되는지 측정한다. 시점별 delta를 재생하거나
기존 검색의 통과를 후기 안정성 근거로 사용하지 않는다. 이후 실제5초 결과가 그 근거다.
사용자가 허용한 초기 자세·strap 반복 탐색 범위 안의 한 후보다.

## 준비·실행·검증

1. prepare_palm_witness_initial_trial.py는 source 검색 입력 SHA와 t0 full 통과를 확인한다.
   기존 실제 초기81각 중 selected18만 float32로 변경한다. 기존 left33 offset은 유지하므로
   PD 유지 목표도 같은 초기각 변경에 맞춰 이동한다. 비선택63각/PD 목표는 exact 유지한다.
   native/Aug19 한계 및 목표 offset±0.3rad를 **float32 합성 후** 다시 확인한다.
2. Quantized delta로 조건부 source body pose를 다시 계산하고 모든 원본 형상 검사와
   fresh native FK 비교용 expected source_state를 준비한다. 양손/인체–기타/
   같은 왼손 비인접 source 교차가 없는지, 손바닥 upper hemisphere와 patch 거리 감소를 확인한다.
   소비된 원본 proposal/trial은 수정하지 않고 새 proposal/trial/로그를 저장한다.
3. run_palm_witness_initial_diagnostic.py에서 기존 run_small_wrist_recorded_diagnostic.py를
   새 trial/proposal로 재사용한다. 원본 audit hook만 process 안에서 확장하고 종료 시 복구한다.
   fresh native pose/shape filter readback으로 모든 native허용 graph>2 self 및
   same-left 비인접 source쌍을 검사하는 gate를 추가한다. 상태/설정 writer는 추가하지 않는다.
   fresh native t0의 모든81각, source no-overlap, expected FK pose 대조를 통과한 뒤
   actual1200step/5초를 실행한다. 같은 L_Wrist_x±0.005rad1Hz 파형을 t0부터 사용한다.
   초기값·원native PNG·actual strap 경로 표시 전신/손151frame 영상을 보존한다.
4. LA−2mm 기존 시험과 기타 초기 위치/회전 최대·종료 오차,2~5초 변화,
   손바닥/엄지/검지/중지 접촉과 실제 wrist 응답을 비교한다.
   유지 목표가 바뀐18관절 외63목표 exact, root/하체 exact, PD/기타 초기p/q/LA 동일을 확인한다.
   이전 원자료의 재생을 새 물리 trial로 표시하지 않는다.

Root·하체 고정, torso9 목표/PD×2, 나머지 gain/물리/충돌·free G·passive constant LA−2mm를 유지한다.
기타 고정·손 부착·지속pose 덮어쓰기·인위적 기타 목표 힘은 없다.
원본 source native runner는 수정하지 않는다. Runner의 기존 scope 문구에서 ‘same initialq’는
그 trial 내의 일관성을 뜻하며, 이번 비교의 초기각18개가 기준과 달라진 사실은 별도 명시한다.
완전 grip/연주/초기p/q 복원 성공을 미리 선언하지 않는다.

- [ ] float32 초기각/PD·source no-overlap·입력 closure 준비 검수
- [ ] 새 actual5초와 strap 영상 두 개 저장
- [ ] 기존LA−2mm와 raw 비교/검토·산출물·보존 확인

구현/입력은 stability_adapter_2에, 결과는
docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1 아래 저장한다.
