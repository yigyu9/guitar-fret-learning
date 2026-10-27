# 팔 연속 조정과 실제 기타 유지 검증으로 돌아가는 다음 소단계

74개 숫자 제안 중 6개는 관절 범위를 넘었고, 68개 source 형상 조건은 모두 손–기타 교차를 남겼다. 원 seed에서 Thorax_y +.025rad의 최대 HG 공통내접반경은 2.212093mm, Wrist_y −.1rad seed에서 Thorax_z +.025rad는 1.231576mm였다. 두 번째 조건도 palm·thumb2·middle3 교차 5쌍이 남는다. 일부 조건은 thumb2 교차를 없애지만 다른 부위 교차를 남긴다. 따라서 축을 하나씩 바꾸는 비교에서 팔 전체의 작은 조합으로 넘어간다. 이 반경은 PhysX 침투 깊이가 아니다.

## 1. 범위와 실행 상한

기준은 fixed_strap_source_hand_initial_v1의 실제 초기 state다. 손가락 상대 자세와 original left33 offset은 유지하고, L_Thorax/Shoulder/Elbow/Wrist의 12개 초기각을 함께 조정한다. Original baseline 대비 각 축 ±.15rad 이내이며 source/native/normalized 초기·held 범위와 Wrist_x ±.005rad 명령 양끝의 교집합으로 더 줄인다. Wrist_y −.1rad는 이미 이 범위 안이다. 모든 실제 입력은 float32로 조립하고 clipping 없이 검산한다. Torso/Spine/Chest 목표, 오른팔/손, 기타 초기 fullstate, LA1.1018469719600776m, PD, root·하체 고정과 최종66 제어권을 유지한다.

원 seed와 직전 row47 seed(원 Wrist_y−.1rad + Thorax_z+.025rad)에서 각각 최대400회 source 목적함수 평가, 합계800회를 상한으로 둔다. 평가 횟수와 optimizer terminal reason을 기록하고 시간 관측 timeout 때문에 같은 작업을 다시 시작하지 않는다. Solver 성공 표시는 범위·형상·지지·실제 초기검사를 대신하지 않는다. 단순 한축 격자를 더 세분화하지 않는다.

## 2. 형상과 지지의 관계

12차원 bounded Powell 탐색을 먼저 사용한다. 목적함수는 손–기타 교차 반경 제곱합을 우선 줄이고, palm/허용 옆면 patch 및 thumb3/후면 patch의 source 거리, 작은 초기각 변화, palm–neck 평면 정렬을 부드럽게 선호한다. Palm 위쪽 반구는 필수다. 구체적인 단위·가중치는 구현 전에 별도 실행 leaf에 기록한다. 원자료가 없는 손 접촉이나 정적 평형 힘을 목적함수에 만들어 넣지 않는다.

모든 평가의 실제 float32 초기/held 입력, 목적함수 구성값, HG 교차쌍, palm 방향과 patch 거리 interval을 순서대로 저장한다. 범위 위반은 형상 평가 전에 명시 제외한다. Sourceclear가 나오는 평가에서는 cross-hands와 self1188 전체를 추가 검사한다. 선택 전에 움직이지 않는 mesh·상위 body와 손가락 상대 계층 보존도 검산한다. 전체 sourceclear만 candidate가 될 수 있다. 목적함수 감소, thumb2 교차 소실, optimizer success만으로 통과시키지 않는다.

Clear 후보는 palm과 thumb3 patch 거리 상한 제곱합이 작은 순서, original baseline 대비 초기각 L2 norm, 평면 정렬, 평가 순서로 한 개를 선택한다. 손이 넥에서 멀어지는 단순 회피를 지지 성공으로 설명하지 않는다. Source patch 근접은 물리 접촉이나 force closure의 인증이 아니다.

## 3. 한 번의 실제 초기화와 5초 검증

선택한 후보 한 개만 fresh actual native 초기검사를 한다. Source 예측 pose와 실제 body pose의 오차를 별도로 측정한다. 기존 직접 HG/cross/self1188, palmup, 全81 실제 초기각·held·PD·기타fullstate·LA·root하체를 검사한다. 통과하면 같은 초기화에서 자유 기타와 실제 관절 PD로 1200step/5초·전신/손 두 스트랩 영상을 남긴다. 거절하면 실제 초기 이미지·0step partial·교차쌍을 보존한다. 기타 고정, 손 부착, post-start pose/state 덮어쓰기와 인위적 기타 복원힘은 쓰지 않는다.

실제5초가 있으면 초기 p/q 최대/종료 오차, 2~5초 완전1초 창 변동, 실제 손 접촉, 관절 범위, palm 방향을 기존 quiet 기준과 비교한다. 임시30mm/5°·후기5mm/1°는 정식 성공 기준으로 승격하지 않는다. 연주 목표와 안정화 보정을 합치는 구조, 실제 fret/strike 전환은 이후 원시 결과에 근거해 검증하며 이번 source 단계로 대체하지 않는다.

## 4. 이번 탐색에서 후보가 없을 때

800회 상한에서 sourceclear가 없으면 새 native를 임의 실행하거나 동일 범위 source 탐색을 무한히 늘리지 않는다. 가장 작은 위반 조건과 교차 부위를 남긴다. 다음에는 이미 actual5초를 확보한 initial_middle3_alignment_v1 quiet 기준으로 돌아가, 기타 초기 유지와 작은 관절 움직임의 실제 결과를 기준으로 손가락 초기 자세·연주 목표 전환에 필요한 조건을 다시 설계한다. Checkpoint 출력 범위 호환은 실제 안정화/자연스러움/연주 성공을 대신하지 않는다. Source 모델 불확실성도 actual 검증 결과와 분리한다. 새 조건은 먼저 파일에 기록하고 사용자 자율진행 지침에 따라 작은 단위로 수행한다.

- [ ] 두 seed의 범위·목적함수·입출력 저장 leaf와 새 구현
- [ ] 독립 검수 및 최대800회 source 조합 검사
- [ ] 한 actual gate/통과시 동일초기화5초 또는 bounded 실패 원인
- [ ] 원 quiet 기준과 비교·이미지/영상·문서·후속 물리 제어 결정

아직 미실행이다. 예정 새 결과 경로는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1 이다. 현재 phase와 이전 소스·계획·영상은 보존한다.
