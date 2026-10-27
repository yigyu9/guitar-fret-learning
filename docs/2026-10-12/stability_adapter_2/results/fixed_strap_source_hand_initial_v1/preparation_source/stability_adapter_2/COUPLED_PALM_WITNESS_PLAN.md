# 실제 저장 형상점 기준 손바닥 우선 보정

## 근거와 이번 단위

직전 coupled_support_source_v1은 모델/검색 검증을 끝낸 progress다.
현재 palm inward alignment는0/0.1/0.5/5초에0.9959/0.9982/0.9998/0.9995로 이미
넥 옆면과 가깝게 평행하지만, 네 접촉 목표의 weighted LS는 손바닥 접근을 희생했다.
유일한 통과는0.5초1/4제안의약21µm 접근이며 실제 제어로 채택하지 않았다.

이번에는 **whole-palm과 지정 blue neck side patch의 최단거리 feasible witness**를
현재 손바닥 local point로 변환해 팔/손가락18축 제안을 계산한다.
목표는 대응 patch witness에서 현재 손바닥 방향으로0.1mm 떨어진 점이다.
엄지/검지/중지 feature는 현재 위치·법선을 부드럽게 유지하여 기존 지지점을 보존하고,
hinge6은 손바닥 접근 시 기존 손끝 위치를 유지하도록 보조한다.
손가락 목표를 새 앞/뒷면으로 동시에 당기는 항은 이번 비교에서 사용하지 않는다.

1. 기존 helper/model/검색 입력 SHA를 확인하고 새 search_coupled_palm_witness.py를 만든다.
   저장0/0.1/0.5/5초마다 source palm/patch witness를 다시 구하고 local point와
   Jacobian을 계산한다. h=0.0001/0.00005rad 중앙차분과 zero-delta identity를 확인한다.
2. 기존 bounds·네 접촉면 vertex 선형 제약·whole-source 교차 검사·up hemisphere를 유지한다.
   팔±0.05rad/hinge±0.10rad, native/Aug19/PDbase의 초기각±0.3rad 교집합을 그대로 쓴다.
   원본 control PDbase+delta에서 비선택63목표는 유지한다. 전체66 제어권은 유지한다.
3. 목적의 위치 가중치는 palm1/다른3feature0.1, 법선은 모두0.001m,
   관절 regularizer0.003m/rad다. 법선 평행은 soft 선호이며 hard exact 정렬이 아니다.
   Fraction1/0.5/0.25의16배치(4 baseline+12제안)를 모두 보존한다.
   Whole-palm 거리상한<기준하한, witness point 목표오차 감소, 기존 교차 증가 screen,
   upward proxy, actual/PD bounds를 모두 대조한다. 거리만 줄었다고 물리 지지로 판단하지 않는다.
4. 충분한 지속 접근 방향을 얻으면 다음 작은 actual PD 실행 계약을 작성한다.
   일부 시점만 통과하면 같은 delta를5초 내내 적용하는 근거로 삼지 않는다.
   새 native trial은 float32 최종 목표 한계 검사와0~5초 실제 strap 영상 두 개를 저장한다.

## 불변 조건과 기록

Root/하체 완전 고정, 몸통9 목표/PD×2, 기타 초기p/q, LA−2mm,
자유 기타·중력·passive strap, 기존 native collision 정책을 유지한다.
이번 source 계산의 native 초기화/physics/actor inference/학습은0이다.
기타 고정/손 부착/지속 pose 덮어쓰기/목표 견인힘/필수 WAIT는 사용하지 않는다.
기존 소스·출력·공용 자산·체크포인트는 수정하지 않는다.
메인 코드/계획은 stability_adapter_2, 결과/로그/그림은
docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1에 저장한다.

- [ ] witness 기반18축 Jacobian/identity와 bounds 확인
- [ ] 네 시점 제안·전체 형상 검사·이전 목적과 비교
- [ ] independent 검수·그림/보존 확인 후 실제 시험 방향 결정

Source witness/LP common-radius는 cooked 접촉·지지력·미래 PD 응답 인증이 아니다.
현재 측정 finger1 상대변환을 공급하는 조건부 모델의 한계도 유지한다.
