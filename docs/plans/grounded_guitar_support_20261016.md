# 양발 접지 유지 + 자유 기타 지지 안정화 V1 (2026-10-16)

사용자 요청: 양발을 안정적으로 바닥에 둔 자세에서 기타의 나머지 안정화 조건도 만족시킨다. 기존 실험·입력·코드를 보존하며 새 phase `paper/initial_pose/lower_body_release_v1/grounded_guitar_support_v1`, 새 구현 `stability_adapter_2/grounded_guitar_support_v1`을 사용한다. 프로젝트의 2026-10-07 자율 실험 지침에 따라 진행한다.

## 확인된 기준과 가정

- 기준 `seated_foot_support_v1/source_v3`, `static5_v6.json`, runtime_v6: 동일 실행 V6/V7에서 양발 접지·발바닥 형상·정지 통과. Root/chair 초기 Z -36mm, cube full .4×.28×.456m. 하체16유효축 유한 제어, 원본0가동범위8축 보존,105입력과97비영범위 구분.
- 기준 기타 전체0..5s 최대 중심이동26.550mm, 회전14.913°, 넥5.240°, Chest actualpositive0. 회전은 step3 오른 허벅지 접촉부터 생기며 step1/2는 자유낙하. 제어 cap포화가 원인이라는 근거는 없다.
- 기타 현재 위치를 따라가는 오른팔 목표와 Chest 실제접촉 부재를 구분한다. scalar DOF와 부모-자식 회전, command와native sensor를 동일시하지 않는다.
- 첫 비교는 controller/gain/하체 그대로, 초기 Gbody convex AABB 중심pivot의 넥+.4°/중심Z+.7mm만 변경한다. 이는 수평 허용±3° 안의 작은 후보이며 동적 성공을 뜻하지 않는다. source gaps 예상 Chest.390/RShoulder.410/RHip.325mm. 팔q를 그대로 보존하므로 손-기타 상대변화는 감사해야 한다.

## 순서와 검증 체크리스트

- [ ] 원자료 첫step 진단을 새 phase에 기록하고 기준 SHA 보존.
- [ ] 새 초기 후보: 전human q/발/좌석/Root 보존, G와손 상대변화 기록, capsule/convex·box·원본접촉제외·좌석 감사. 원자료 mesh XML전체 입력 SHA 사전/사후 기록. source 합격과native접촉 구분.
- [ ] independent change-reviewer 검수 후 실제 static5초 비교. 첫step 및0..1/1..5/4..5s 기타·접촉·상체·발 결과 기록. 실패하면 원인에 맞는 새 버전만 추가.
- [ ] 전체static성공 뒤 동일설정재현, 그다음 압현·타현·결합 시험. static실패 중에는 playing/release/PPO 시작하지 않는다.
- [ ] 결과·실패·미해결·실제영상·변경근거 기록, oldinventory 보존감사 및 newphase 최종 입력snapshot/봉인.

## static5초 사전 성공 기준 (기존 기준 유지)

물리1200step 정상종료;Root고정;G자유/중력ON/strapOFF;상태덮어쓰기·G직접힘·부착0;원본105/0범위8 유지;유한 cap;원자료 및 wrapper 입력불변.

전0..5초: Gbody convex AABB 중심 초기대비이동≤30mm, SO3 회전≤5°, |넥고도|≤3°, 원본human lateral오차≤20mm; Torso/Chest total≤5°, |righttilt|≤3°. settle1..5초 Chest+RShoulder actualpositive동시접촉≥95% 및 양발actualpositive지면접촉≥95%.

마지막1초 각 Ankle/Toe 원본BOX bottom4 전체 Z∈[-1,+3]mm, soletilt≤2°, bodyorigin peak-to-peak norm≤3mm, origin선속도≤.02m/s,각속도≤.2rad/s. 형상은 정규화native회전+XMLgeom으로 재구성하며 cookedpenetration 인증이 아니다. rawlambda를N으로 해석하지 않는다. fixedRoot이므로 freeRoot하중평형으로 주장하지 않는다.

## 실패 시 다음 단계 판단

첫 비교에서 초기회전/Chest접촉 변화를 원자료로 확인한다. 단순gain증가나과거실패설정복원은 하지 않는다. 새finite human목표가 필요하면 초기G자세에 대한 복원과 현재G를 따라가는 지지점을 분리하고, 기존발목표의 최종소유권을 유지한다. 추가제어는 별도leaf계획/코드/입력으로 사전기록한다.
