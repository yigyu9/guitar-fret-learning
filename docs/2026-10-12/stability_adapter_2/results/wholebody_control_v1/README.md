# Root 고정 전신 관절 제어 계약

사용자의 최종 방향은 **root를 제외한 전신 관절을 제어하고, 연주하지 않는 관절도 초기 지지 자세를 유지하는 데 사용하는 것**이다. 이를 반영해 하체를 포함한105채널의 목표와 유한 PD 명령을 계산하는 CPU 계약을 추가했다. 신경망은 연주에 필요한39개 목표 변경을 결정하고, 나머지66개는 외부에서 지정한 기준 자세를 추종한다.

현재 native 초기 자세 연구는 기존 fixed-lower 조건으로 보존한다. 이번 구현은 새 음악 환경을 위한 제어 계약이며, 실제 native 환경을 전환하거나 전신 지지·음악 학습 성능을 확인한 결과는 아니다. 초기 자세 확정 후 하체가 포함된 reset과 물리 환경을 연결한다.

## 무엇이 달라지는가

| 구분 | 이전 음악 CPU 계약 | 새 전신 CPU 계약 |
|---|---|---|
| 제어 모델 | 하체24관절이 제거된81채널 | 원본 하체24를 포함한105채널 |
| 학습 정책 출력 | 왼팔·손33 + 오른쪽 팔꿈치·손목6 | 같은39개 연주 목표 |
| 기준 자세 유지 목표 | 지지부15 + 오른손21 + 목·머리6 =42 | 위42 + 하체24 =66 |
| 하체 상태 | fixed-lower 자산에 링크 변환을 구워 넣음 | 실제 관절 각도·속도를 받아 유한 feedback 명령 계산 |
| root | 고정 | 고정하는 native 계약을 요구하며 정책·토크 출력에서 제외 |
| 기타 | 자유 물체 | 자유 물체 유지 |

원본 `smpl_mpl_hands_body.xml`에는105개 scalar joint 채널이 있고, 양쪽 Hip·Knee·Ankle·Toe에24개가 있다. 이 중 양쪽 Knee_y/z·Toe_y/z의8축은 원래 관절 한계가0이다. 따라서 **105개 목표/명령 채널과97개의 비영 가동 범위**를 구분한다. 해부학적 관절 한계를 바꿔105개가 모두 독립적으로 움직일 수 있다고 만들거나 설명하지 않는다. 허벅지를 포함한 하체의 비영 가동 축16개를 실제 물리 관절로 복원하는 것이 기존 fixed-lower와의 핵심 차이다.

새 자산을 복사하거나 기존 fixed-lower 자산을 수정하지 않았다. 원본에 필요한 관절이 이미 존재한다. 단, 이 원본의 초기각·충돌 설정·관절 importer 결과가 현재 고정 하체 자세와 같다는 뜻은 아니다.

## 초기 자세 유지도 제어가 되는 조건

제어기는 목표각을 실제 상태에 대입하지 않는다. 매 물리 단계에서 실제105차원 각도와 속도를 받아 다음 명령을 계산한다.

`tau = clip(Kp * (q_target - q) - Kd * qdot, -effort_limit, effort_limit)`

연주 관절의 `q_target`은 정책 출력에서 오고, 유지 관절의 `q_target`은 초기 기준각에서 온다. 목표가 일정하더라도 접촉 반작용으로 실제 각도나 속도가 변하면 제어 명령이 달라진다. 이처럼 **움직임을 만드는 제어와 자세를 유지하는 제어를 전신에 함께 적용**한다. 모든 채널에 양의 유한 Kp와 effort limit을 요구하고, Kd는 음수가 될 수 없다. 출력은 계산된 명령 토크이며 측정 토크가 아니다.

이 단순 PD는 중력이나 접촉에 의해 정상상태 오차가 생길 수 있고, 토크가 포화되면 자세를 유지하지 못할 수 있다. 큰 gain으로 몸을 사실상 잠그는 것이 전신 제어의 검증 목표는 아니다. 실제 native 연결에서 추종 오차·속도·명령/측정 토크·포화율과 기타 지지를 함께 측정해야 한다. 원래 range=0인8축의 채널 존재를 실질적인 운동 제어 기여로 계산하지 않는다.

전신 제어를 위해 신경망의 출력까지105개로 늘릴 필요는 없다. 현재 구조에서는 연주 목표39개를 학습하고, 전신의 관절 feedback이 그 목표와 지지 자세를 함께 추종한다. 따라서 **전신 feedback 제어**와 **모든 관절 목표를 학습 정책이 결정하는 전신 학습**은 다른 주장이다. 후자는 이번 구현 범위가 아니다.

## 구현 계약

[WholeBodyTargetContract](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/control.py)는 원본105개 이름 집합을 정확히 요구한다.81개 배열이나 root가 포함된 배열은 거부한다. 배열 순서에 의존하지 않고 이름으로 기존 upper81 변환과 하체24를 대응시킨다. 기존39행동의 범위·평활화·속도 제한은 검증된 [v2 변환기](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/control.py)를 재사용한다.

- 입력: native 순서의105차원 기준각·관절 한계·속도 제한·Kp/Kd/effort limit과39차원 목표 변경 범위.
- `targets(action39, previous_target105)`: 요청 목표와 제한을 적용한 최종105차원 목표를 반환한다. 유지66개 목표가 기준각에서 달라져 있으면 오류로 거부한다.
- `torques(q105, qdot105, target105)`: 전신 PD 명령105개를 반환한다. 유지 목표 오염과 연주 목표의 유효 범위 이탈을 거부하고 토크 한계를 적용한다.
- Metadata: full joint order,105/39/66 역할, 모든 제어 파라미터,0 범위 축과 비영 가동 채널 수를 기록한다. 새 정책 생성 시 이 metadata를 입력·제어 계약에 포함해야 한다. 기존81채널 체크포인트와 동일한 계약으로 재개하면 안 된다.

관절 범위가 같은 lower 축은 그 각도에서만 유지할 수 있다. 새로운 하체 기준각이나 gain은 임의 값으로 채우지 않는다. 현재 테스트의 기준각·gain·교란은 합성 fixture이며 실제 자세 선정 또는 제어기 튜닝 결과가 아니다.

기존 fixed-lower 모델은 기록된 링크 변환을 직접 구워 넣었다. 따라서 기존81개 상체 각도를 원본에 복사하고 하체를0으로 채우는 방식으로 이전 자세를 재현했다고 주장할 수 없다. 새105차원 초기각을 구성한 후 root 기준 몸·허벅지·발·기타의 위치와 접촉을 다시 대조해야 한다.

## 검증 결과

[CPU 테스트5개](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/test_control.py)가 통과했다. 이름 순서를 뒤집어도 같은 목표를 만드는지,39/66 소유권이 겹치지 않는지, 하체를 포함한 채널에 가상 각도 교란을 주면 복원 방향의 명령이 생기는지, 감쇠·포화·입력 오류 거부가 올바른지 확인했다. 원본 XML의105개 이름, 하체24개와0 범위8개도 대조했다.

[검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wholebody_control_v1/cpu_v1/result.json)에서 실행 전후 입력 SHA가 일치하고, 이전 음악 파이프라인 입력55개와 과거 native 입력1333개도 변경되지 않았다. 원본 human XML과 선언된 mesh37개를 함께 pin했다. 이는 XML·파일 구조와 CPU 계산의 검사이며 PhysX 형상·접촉·추종 성능 검증은 아니다. 새로운 native 실행은0회다.

재현 명령:

```bash
cd /home/ajou/yigyu/3
PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -m unittest -v \
  stability_adapter_2.music_pipeline_v3.test_control
```

## 새 물리 환경에 연결할 조건

1. Root만 전역 고정하고 하체 관절이 살아 있는 자산을 사용한다. 실제 importer가 반환한 이름·한계·채널 수를 검사한다. 기타는 자유 상태, 내부 충돌 조건은 유지한다.
2. 전신105개 초기각과 속도, 몸·발·기타의 초기 배치, gain·유한 effort를 함께 기록한다. 기존 fixed-lower 안정성 결과를 새 조건의 결과로 재사용하지 않는다.
3. 실제 전신 각도·속도와 기준/직전 목표, 기타 상대 상태·접촉·지지 여유를 관측에 포함한다. 정책이 전신 상태를 볼 수 있게 물리 입력 ABI를 새로 확정한다.
4. 명시적 PD 토크를 쓸 때는 적합한 native effort mode를 사용한다. native position PD를 선택하면105개 관절의 gain·한계를 설정하고 목표를 전달하는 별도 경로로 검증한다. 두 방식을 중복 적용하지 않는다. 이 CPU PD 식과 native solver PD의 동작이 동일하다고 가정하지 않는다.
5. 먼저 연주 없는 자세 유지, 다음 작은 팔 동작과 타현, 이후 압현·음악 시각 조건으로 진행한다. 다리·발의 변위, 접촉 변화, 관절 추종과 포화, 기타 허용 범위와 연주 성공을 같이 평가한다.

## 논문에서 사용할 설명 범위

현재 단계의 정확한 표현은 **“root를 고정한 humanoid의 전신 관절 제어를 목표로 하며, 연주 목표 정책과 전신 자세 추종 제어를 결합한다”**이다. Native 연결과 검증이 완료되면 다음과 같이 방법을 서술할 수 있다.

> With the humanoid root fixed, a joint-level controller tracks targets across the articulated body. A music-conditioned policy updates the left-arm and left-hand targets for fretting and the right-elbow and right-wrist targets for striking, while the remaining joints track a reference support and pick-grip posture.

이 문장은 실제 구현·검증 완료 후 Methodology에 사용할 후보이며 현재 결과 주장으로 넣지 않는다. “전신 제어”는 모든 관절이 크게 움직인다는 뜻도, 모든 관절 목표를 RL이 학습한다는 뜻도 아니다. Root가 외부 반력을 제공하므로 자유 보행·부유 root 균형 제어를 달성한 것으로 확대하지 않는다. 연구의 기여는 명칭보다 자유 기타 지지와 시간에 맞춘 압현·타현을 어떤 조건에서 함께 달성하는지로 보여준다.


[독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wholebody_control_v1/review.md)에서 현재 CPU 계약 범위의 미해결 Critical/Warning이 없음을 확인했다. 최종 원문·입력 SHA와 파일 목록은 같은 폴더의 final_verification.json, source_final, artifact_inventory.json에 보존한다.
