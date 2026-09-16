# StabilityAdapter 다섯 손가락 그립·운반 설계

## 1. 목표와 전제

목표는 `--task stability-adapter` 하나에서 다음 동작을 학습하는 것이다.

1. 기타가 스트랩에 걸려 충분히 느려질 때까지 기다린다.
2. 왼손 손바닥을 위로 향하게 하고 넥 아래로 접근한다.
3. 엄지는 넥 뒤쪽, 검지·중지·약지·소지는 넥 앞쪽을 감싼다.
4. 왼손 그립으로 기타를 목표 위치·회전 쪽으로 실제 이동시킨다.
5. 이후 오른팔과 몸의 허용된 부분으로 지지를 인계하고 안정적으로 유지한다.

GPU 병렬 학습 중에는 손가락–기타 **접촉 쌍별 힘**을 직접 얻을 수 없다. 따라서 학습에는
손가락별 유한 면 기하, 손가락 강체의 접촉 합력, 미끄럼, 손–기타 상대 운동 및 기타의 실제
이동을 결합한 `grip load proxy`를 사용한다. 이 대리 지표는 별도의 단일 환경 접촉 쌍 진단으로
검증한다. 합력만으로 접촉이나 쥐는 힘을 단정하지 않는다.

현재 실행 중인 v9은 비교 기준으로 유지한다. 아래 변경은 관측과 단계 상태를 바꾸므로 체크포인트
호환 버전을 올리고 새로 학습한다.

## 2. 현재 병목

현재 기하 구조는 네 손가락 중 넥에 두 번째로 가까운 손가락 하나를 대표값으로 사용한다.
그 결과 검지·중지·약지·소지가 각각 참여하도록 배우는 신호가 없다. 실제 그립 보너스는 엄지와
손가락 두 개가 기하·합력 조건을 동시에 만족한 뒤에만 발생한다. 현재 로그에서는 손바닥과 엄지는
접근했지만 손가락 대향 접촉이 0이므로 그립 보너스와 운반 보상도 계속 0이다.

또한 현재 오른팔·몸 지지 유도는 왼손 운반이 증명되기 전에도 남아 있다. 정책이 왼손 그립을
배우지 않고 몸이나 오른팔로 기타를 움직이는 우회가 가능하다. 새 설계에서는 왼손 운반 증명 전과
후의 권한과 보상을 분리한다.

## 3. 측정 구조

### 3.1 손가락별 기하

`stability_grip_geometry.py`에서 엄지·검지·중지·약지·소지 각각에 다음 값을 계산한다.

- `face_distance_m`: 해당 손가락 표면에서 목표 넥 면까지의 거리
- `face_gap_m`: 목표 면 법선 방향의 부호 있는 간격
- `face_lateral_m`: 유한한 넥 면 밖으로 벗어난 거리
- `axial_offset_from_thumb_m`: 엄지와 같은 넥 길이 구간에 있는지 나타내는 거리
- `surface_slip_m_s`: 손가락 재질점과 기타 재질점 사이의 접선 속도
- `surface_closing_speed_m_s`: 목표 면으로 접근하는 법선 속도
- `surface_facing_dot`: 선택된 손가락 표면 법선과 목표 넥 면 방향의 정렬
- `body_net_force_W_n`: 해당 손가락 강체의 월드 좌표 접촉 합력 벡터
- `normal_force_proxy_n`: 위 합력을 목표 면 법선으로 투영한 값

현재 mesh sampler는 삼각형 중심점만 남긴다. 구현 시 선택된 삼각형의 법선도 중심점과 같은 index로
보존한다. 손가락 mesh는 비균일 scale을 사용하므로 법선은 scale의 역전치로 변환하고 정규화한 뒤
강체 자세로 월드 좌표에 회전한다. 현재 pinch 경로의 `LH:thumb3`도 mesh이므로 다른 손가락과 같은
삼각형 법선 규칙을 사용한다. capsule 방사 법선은 legacy `LH:thumb_pad` 경로에만 적용한다.
`sampled_face_measure()`가 선택한 동일 표본의 법선을 사용해야 거리와 방향 판정이 서로 다른 표면점을
가리키지 않는다.

법선 투영의 부호는 코드에서 가정하지 않는다. 단일 환경 접촉 쌍 진단으로 실제 접촉 때의 부호를
확인한 후 고정한다. 합력의 크기와 투영값을 모두 로그에 남긴다.

### 3.2 손가락별 접촉 대리 지표

각 손가락 `d`에 대해 다음 조건을 모두 만족할 때만 힘을 그립 증거로 인정한다.

```text
geometry_d =
    gap 범위 안
    AND lateral 범위 안
    AND 엄지와 같은 넥 구간
    AND 손가락 표면이 지정된 넥 면을 향함

safe_loaded_d = geometry_d
    AND F_on[d] <= normal_force_proxy_d <= F_hard[d]
    AND slip_d <= slip_on[d]
```

접촉이 이미 성립한 뒤에는 `F_off[d] < F_on[d]`, `slip_off[d] > slip_on[d]`인 히스테리시스를
사용한다. 한 프레임의 힘 흔들림으로 그립 단계가 반복해서 꺼지지 않게 한다.

`F_on`, `F_off`, `F_soft`, `F_hard`는 모든 손가락에 같은 임의 상수를 사용하지 않는다. 엄지와 각
손가락별 진단 분포에서 정한다. 현재의 0.1 N은 노이즈 바닥 확인용 값으로만 취급한다.
단계 전환에는 `safe_loaded_d` 또는 이에 대응하는 최소 품질값을 사용해 과도한 힘으로도 전환되는
경로를 닫는다. `F_hard` 초과는 해당 손가락의 접촉 증거를 무효화하고 안전 비용 또는 종료 판정에
전달한다.

### 3.3 그립 품질

힘 크기를 선형으로 계속 보상하지 않는다. 손가락마다 0~1의 제한된 품질값을 만든다.

```text
q_d = q_geometry_d * q_force_band_d * q_slip_d
```

- `q_geometry`: 거리·면 내부·엄지와의 축 방향 정렬이 좋아질수록 증가한다.
- `q_force_band`: `F_off` 아래는 0, 안정 접촉 범위에서 1, 과도한 힘부터 다시 감소한다.
- `q_slip`: 상대 미끄럼이 작을수록 1에 가깝다.

`q_force_band`에 상한 감소를 넣는 이유는 기타를 강하게 누르기만 하는 정책을 막기 위해서다.
최대 합력·침투·충돌 속도에 대한 기존 안전 비용과 종료 판정도 유지한다.

다섯 손가락 품질은 다음처럼 별도로 보존한다.

```text
thumb_quality
index_quality
middle_quality
ring_quality
pinky_quality
```

평균 하나로 먼저 압축하지 않는다. 단계 전환과 로그가 어느 손가락에서 막혔는지 보여야 한다.

## 4. 한 에피소드 안의 단계

외부 태스크나 `--stage` 인자는 추가하지 않는다. `stability-adapter` 내부 상태만 다음 5단계로
바꾼다. `WAIT_SETTLE`은 기존 환경 단계로 그대로 앞에 존재한다.

### 4.1 `UNDERHAND_REACH`

- 손바닥이 넥 아래에 있고 손바닥 안쪽 면이 넥을 향한다.
- 손바닥이 넥에 가까워진다.
- 엄지와 네 손가락은 아직 힘 조건 없이 각자의 목표 면에 접근한다.
- 조건을 0.15초 연속 만족하면 `FINGER_WRAP`으로 간다.

### 4.2 `FINGER_WRAP`

- 엄지는 뒤쪽 면, 네 손가락은 앞쪽 면으로 감싼다.
- 각 손가락의 거리와 엄지 기준 축 방향 정렬을 독립적으로 개선한다.
- 손가락별 `geometry_d` 성립에 순차적인 일회성 보상을 준다.
- 진단에서 다섯 손가락 접촉 가능성이 증명된 경우에만 엄지+네 손가락의 기하 성립을 단계 완료
  조건으로 사용한다. 증명 전에는 학습을 시작하지 않고 자산·기준 자세를 먼저 수정한다.

### 4.3 `LOAD_GRIP`

- 엄지와 네 손가락이 차례로 안전한 힘 구간에 들어오도록 한다.
- `safe_loaded_d`가 새로 성립할 때 손가락별 일회성 보상을 준다.
- 엄지+네 손가락 전체가 0.20초 유지되면 `LEFT_TRANSPORT`로 간다.
- 전환 후의 유지 조건은 엄지+최소 세 손가락으로 완화한다. 한 손가락의 순간적인 힘 손실 때문에
  전체 운반이 즉시 실패하지 않게 하되, 네 손가락 참여율은 별도 품질 지표로 유지한다.

### 4.4 `LEFT_TRANSPORT`

- 오른팔 그립 도움은 아직 열지 않는다.
- 왼손–넥 상대 위치가 유지되고 기타가 목표 자세 방향으로 움직일 때만 운반 보상을 지급한다.
- 기타 위치가 첫 그립 시점보다 최소 15 mm 개선되어야 왼손 운반 증거로 인정한다.
- 위치 개선뿐 아니라 회전 개선도 따로 기록한다. 둘 중 하나가 악화되는 큰 움직임은 제한한다.
- 왼손 운반 증거가 성립하면 `MAINTAIN_HANDOVER`로 간다.

### 4.5 `MAINTAIN_HANDOVER`

- 오른팔과 몸의 허용된 부위에 지지 권한과 접근 보상을 연다.
- 최종 기타 위치·회전·속도와 지지 안정성을 평가한다.
- 향후 Fret 연결을 위해 유지 단계에서는 네 손가락을 영구적으로 모두 닫아 둘 필요가 없다.
  엄지·손바닥 지지와 최소 두 손가락의 유지 접촉을 요구하고, 나머지 손가락이 압현 자세로 이동할
  수 있게 한다.

### 4.6 전환·강등 상태표

| 현재 단계 | 전진 조건과 dwell | 강등 조건과 dwell | 강등 위치 |
|---|---|---|---|
| `UNDERHAND_REACH` | underhand+근접 0.15초 | 해당 없음 | 현재 단계 유지 |
| `FINGER_WRAP` | 다섯 손가락 geometry 0.15초 | underhand 또는 손바닥 근접 상실 0.20초 | `UNDERHAND_REACH` |
| `LOAD_GRIP` | 다섯 `safe_loaded` 0.20초 | geometry 상실 0.20초 | `FINGER_WRAP`, underhand도 잃으면 `UNDERHAND_REACH` |
| `LEFT_TRANSPORT` | 운반 증거+유지 그립 0.35초 | 엄지+세 손가락 유지 상실 0.20초 | `LOAD_GRIP`, geometry도 잃으면 `FINGER_WRAP` |
| `MAINTAIN_HANDOVER` | 엄지·손바닥+두 손가락, 목표 자세·속도 0.50초 | 유지 지지 또는 목표 안전 범위 상실 0.20초 | `LEFT_TRANSPORT` 또는 `LOAD_GRIP` |

단계가 바뀌면 현재 단계의 `evidence_dwell`과 `lost_dwell`만 0으로 만든다. 손가락별 일회성 보상,
에피소드 best, 최초 그립 여부와 최초 운반 baseline은 강등·재획득 때 초기화하지 않는다. 최초
full-wrap에서 운반 baseline을 한 번만 고정하고 이후 재획득 시 다시 잡지 않는다. 목표 pose best는
접촉과 무관하게 모든 valid frame에서 계속 갱신해, 스트랩이 먼저 만든 개선을 나중에 그립 보상으로
회수하지 못하게 한다. 단계별 별도 timeout 종료는 추가하지 않고 기존 전체 recovery timeout을
유지하되, 단계별 체류·정체 시간을 로그에 남긴다.

## 5. 보상 구조

모든 양의 보상은 에피소드 최고 개선량 또는 최초 이정표에 대해서만 지급한다. 접촉을 반복해서
켰다 끄거나 같은 힘을 오래 유지해서 보상을 무한히 얻을 수 없게 한다.

### 5.1 접근 보상

기존의 손가락 두 개 대표값을 제거하고 다음 항목을 독립적으로 둔다.

```text
R_reach = Δbest(palm)
        + Δbest(thumb)
        + Σ Δbest(index, middle, ring, pinky)
```

손가락별 오류에는 면 거리와 엄지와의 축 방향 간격을 함께 넣는다. 따라서 다른 프렛 위치에서
넥에 닿는 것만으로는 접근 보상을 완료할 수 없다.

### 5.2 감싸기·하중 보상

- 각 손가락의 `geometry_d` 최초 성립: 작은 일회성 보상
- 각 손가락의 `safe_loaded_d` 최초 성립: 작은 일회성 보상
- 엄지+1, +2, +3, +4 손가락의 연속 유지: 점진적인 이정표 보상
- 다섯 손가락 전체 유지 완료: 첫 그립 획득 보상

점진적 이정표는 탐색 초기에 한 손가락만 성공해도 다음 방향을 알려 준다. 최종 단계 전환은 전체
그립을 요구하므로 두 손가락만 사용하는 정책으로 끝나지 않는다.

### 5.3 운반 보상

운반 보상은 다음 세 조건이 동시에 성립할 때만 지급한다.

```text
R_transport = pose_best_improvement
              * retained_grip_quality
              * left_hand_transport_evidence
```

`left_hand_transport_evidence`는 다음으로 구성한다.

- 엄지+최소 세 손가락의 하중 접촉이 유지됨
- 손바닥/손목과 넥의 상대 속도가 작음
- 기타가 목표 위치·회전 방향으로 실제 개선됨
- 오른손·오른팔 및 몸통 지지 대리 지표가 활성화되지 않음
- 동일 초기 조건에서 미리 측정한 수동 스트랩 이동 envelope를 초과함

학습 중 위 조건은 강한 대리 지표일 뿐 인과 증명은 아니다. 최종 평가는 동일 seed와 초기 상태에서
`왼팔 정상`, `왼팔 frozen/open`, `오른팔 frozen` rollout을 짝지어 비교한다. 왼팔 정상에서만
passive envelope를 넘는 목표 방향 개선과 낮은 손–넥 상대 운동이 나타나야 왼손 운반으로 인증한다.
몸통·오른팔의 실제 기타 접촉은 단일 환경 접촉 쌍 진단에서도 별도로 보고한다.

### 5.4 비용

다음 비용은 계속 매 프레임 적용하되 상한을 둔다.

- 과도한 접촉 합력과 침투
- 높은 접근 속도와 충격
- 손가락–넥 미끄럼
- 손바닥 방향 위반과 넥 위쪽에서의 접근
- 과도한 상체 변형
- 운반 증명 전 오른팔/몸으로 기타를 지지하는 우회
- 손가락을 지나치게 펴거나 관절 한계에 붙이는 자세

접근 단계에서 기타 목표 자세 비용은 현재처럼 크게 환급한다. 그립이 없는데 기타 이동을 요구하는
비용이 손 접근 학습을 압도하지 않게 한다. 반대로 `LEFT_TRANSPORT` 진입 후에는 위치·회전 비용을
전부 복원한다.

보상 계수는 임의로 한 번에 고정하지 않는다. 각 항목의 실제 분포를 기록해 PPO advantage에서
한 항목이 대부분을 차지하지 않도록 정규화한다. 첫 구현에서는 현재 총 양의 보상 예산과 음의 비용
예산을 유지하고, 기존 두 손가락 접근 예산을 네 손가락에 나누어 배분한다.

초기 구현의 에피소드 양의 보상 예산은 현재와 같은 9점으로 제한한다. 아래 값은 물리 임계값이
아니라 신호 간 상대 크기를 정하는 시작값이며, 짧은 pilot의 실제 advantage 기여율로 조정한다.

| 묶음 | 최대값 | 배분 |
|---|---:|---|
| 접근 | 3.0 | palm 0.5, thumb 0.5, 네 손가락 각 0.5 |
| 그립 획득 | 2.0 | geometry 최초 합계 0.5, safe-loaded 최초 합계 0.75, 참여 단계 합계 0.45, full-wrap 0.3 |
| 운반·인계 | 4.0 | 위치 best 개선 2.25, 회전 best 개선 1.25, 안정 인계 0.5 |

접근과 운반은 정규화된 best 감소량에 비례하고, 나머지는 최초 한 번만 지급한다. 음의 비용은 현재
에피소드 최대 8점 계약을 유지한다. pilot에서 한 묶음이 양의 advantage의 60% 이상을 계속 차지하면
계수를 낮추고, 성립 가능한 이벤트인데 5% 미만이면 계수를 높여 다시 짧게 검증한다.

## 6. 제어 권한과 자연스러운 동작

현재는 손바닥이 5 cm 이내가 되면 모든 왼손 손가락 제어가 한 번에 켜진다. 이를 손가락별 연속
권한으로 바꾼다.

```text
authority_d = smoothstep(far_distance, near_distance, distance_d)
target_d = open_reference_d + authority_d * (policy_target_d - open_reference_d)
```

- 멀리 있을 때는 손을 자연스럽게 편 기준 자세로 둔다.
- 가까워질수록 해당 손가락의 정책 출력을 연속적으로 허용한다.
- 접촉 직전에는 기존 속도·가속도 제한을 더 낮춰 강한 충돌을 막는다.
- 97축 action ABI와 손가락별 자유도는 유지한다. 손가락을 하나의 고정 synergy action으로 합치지
  않는다. 단독 Stability 학습에서 손가락 독립 제어를 보존하기 위한 결정이며, Full 연결 권한과는
  별개다.

운반 증명 전에는 오른팔의 기타 방향 잔차 권한을 닫거나 매우 작게 제한한다. 왼손 운반 증명 후
원래 권한으로 부드럽게 연다. 몸통은 골반 고정 상태에서 작은 보정만 허용하고 현재의 높은 자세
비용을 유지한다.

### 6.1 Fret·Strike 인계 계약

현재 standalone 정책 출력은 정규화된 97축 target velocity이고, Full의
`ConditionalStabilityController`는 별도의 43축 radian residual 정책이다. 현재 checkpoint를 Full에
바로 꽂을 수 있다고 간주하지 않는다. 기존 Full bridge는 몸통·하지·근위 팔의 canonical 43축만
허용하고 손가락·손목·시선은 Fret/Strike source가 소유한다.

v10 standalone 구현은 다섯 손가락 그립과 운반의 물리적 학습 가능성을 먼저 증명한다. 이후 Full
연결 구현에서는 `GRIP_ACQUIRE` 동안에만 왼쪽 손목·손가락을 소유하는 명시적인 GripSource를 action
arbiter에 추가하고, `MAINTAIN_HANDOVER`에서 그 소유권을 Fret으로 넘긴다. 97축 standalone action을
그대로 Full residual로 재해석하지 않는다. 변환이 필요한 경우 다음 순서를 계약으로 고정한다.

1. standalone target-velocity action으로 이전 실행 target에서 다음 radian target을 적분한다.
2. joint name으로 97축 target을 Full 105축 actuator에 매핑한다.
3. 왼쪽 손목·손가락 target은 pre-handover GripSource 슬롯에만 넣는다.
4. canonical 43축은 Full source target과의 차이를 residual cap으로 제한해 제안한다.
5. 다른 손가락·손목·시선 축은 원래 Fret/Strike source 값을 그대로 보존한다.
6. 모든 source와 residual을 합성한 뒤 공유 EMA를 정확히 한 번 적용한다.

이 변환은 standalone의 `target_speed_limit`, 이전 실행 target, 이름 기반 97→105 index, radian residual
cap을 checkpoint/manifest에 함께 저장해야만 유효하다. Full 연결 코드는 별도의 통합 단계에서 수정하고
동등 target replay test를 통과시킨다. `MAINTAIN_HANDOVER`는 그 통합에 필요한 다음 상태를 내보낸다.

- `grip_handover_ready`: 기타 자세·속도와 최소 지지가 인계 범위 안인지
- `last_executed_target_rad[97]`: standalone 마지막 실행 target
- `grip_state`: 손가락별 geometry/loaded/retained와 단계·dwell
- `standalone_next_target_rad[97]`: target-velocity 적분과 제한을 마친 다음 target

Full 진입 시 Fret/Strike의 손목·손가락 source target은 마지막 실행 target에서 시작해 첫 목표로
유한 시간 blend한다. Stability의 8프레임 물리 관측 history는 계속 갱신한다. Synchronizer hold와
safety gate는 기존처럼 adapter의 canonical 43축 권한도 거부할 수 있다. GripSource가 구현되기
전까지 v10 checkpoint에는 “standalone only”로 표기하고 Full 연결 완료를 주장하지 않는다.

## 7. 단일 태스크 내부 초기 상태 커리큘럼

97축 정책이 현재의 전체 초기 상태에서 우연히 다섯 손가락 접촉을 찾기를 기다리지 않는다.
태스크 이름과 네트워크는 하나로 유지하면서 reset 분포만 혼합한다.

1. `closure` 분포: 검증된 underhand 열린손 자세에서 손가락 감싸기와 하중 형성을 학습
2. `reach` 분포: 손을 넥 아래 가까운 영역에서 시작해 접근부터 학습
3. `full_drop` 분포: 현재와 같이 기타 방치·정지·접근·그립·운반 전체를 수행

초기에는 `closure` 비율을 높이고, 접촉 획득률이 검증 기준을 넘으면 `reach`, 이후 `full_drop`
비율을 높인다. 이전 분포를 완전히 제거하지 않아 망각을 막는다. 정책 관측에는 reset 분포 식별자를
넣어 Markov 상태를 보존한다. 최종 성능 보고는 `full_drop`만으로 수행한다.

`closure`와 `reach` 상태를 tensor에 기록한 직후에는 링크 위치가 이전 episode 값이고 상대 속도도
유효하지 않다. 따라서 두 번의 물리 갱신으로 위치와 유한차분 속도가 모두 준비될 때까지 기록된
관절 target을 그대로 유지하고 PPO 표본에서 제외한다. 준비 구간에 임의 action이나 열린손 기준
자세가 검증된 reset 자세를 덮어쓸 수 없다.

`closure`용 자세는 손으로 보기 좋은 값을 다시 쓰지 않는다. 제한된 관절 범위 안에서 기하 목적을
최적화한 후보를 PhysX로 실행하고, 실제 손가락–기타 접촉 쌍과 안전한 힘을 통과한 자세만 저장한다.
이 자세는 reset 커리큘럼의 시작점일 뿐 모방 목표가 아니다.

## 8. 힘 기준 보정과 진단

### 8.1 단일 환경 접촉 쌍 검사

CPU 파이프라인 또는 GPU solver+CPU pipeline의 단일 환경에서 다음을 기록한다. 현재
`probe_stability_grip.py`가 직접 생성하는 production task는 GPU pipeline을 강제하므로 그대로 쓰지
않는다. `audit_stability_contacts.py`의 audit task factory처럼 `use_gpu_pipeline=False`인 전용 task를
사용하고 solver, pipeline, contact collection, dt, substep 설정을 결과 manifest에 봉인한다.

- 실제 `LH:thumb3/index3/middle3/ring3/pinky3`–기타 접촉 쌍
- 각 접촉의 법선 힘 `lambda`와 마찰력
- 같은 프레임의 손가락 강체 합력·법선 투영값
- 거리·gap·lateral·축 방향 간격·미끄럼

이를 통해 `geometry_d AND net-force proxy`가 실제 손가락–기타 접촉을 얼마나 잘 구분하는지
혼동행렬로 검증한다. 같은 joint target 시퀀스를 production GPU pipeline에서도 다시 실행해
강체 합력·기하 분포가 진단 pipeline과 크게 달라지지 않는지 별도로 비교한다.

### 8.2 손가락별 힘 기준

각 손가락에 대해 세 분포를 수집한다.

1. 비접촉 상태의 합력 노이즈
2. 기하 접촉만 있고 기타를 유지하지 못하는 상태
3. 접촉 후 작은 검증 외력을 견디며 상대 자세를 유지하는 상태

과부하·침투가 발생하는 네 번째 분포도 수집해 `F_hard[d]`를 정한다. 분포가 분리될 때만
`F_off[d]`, `F_on[d]`, `F_soft[d]`, `F_hard[d]`를 결정한다. 비접촉/안정 접촉 분리가 되지 않거나
안정 접촉과 과부하 사이의 안전 구간을 만들 수 없으면 v10 학습을 시작하지 않는다. 이때는 접촉
형상·collision filter·센서 대리 지표를 먼저 수정한다. 힘 조건을 조용히 제거하는 대체 경로는 두지
않는다. 보정 결과와 코드/자산 hash는 `stability_adapter/grip_force_calibration.json`에 저장한다.
이 파일에는 CPU/GPU 양쪽의 dt, substep, GPU pipeline/solver 사용 여부, solver 반복 수, contact
collection, contact/rest offset, 최대 침투 복원 속도와 중력도 함께 저장한다. 두 실행의 공통 물리
설정이 다르거나 probe·물리 환경 소스 hash가 현재 코드와 달라지면 보정 파일을 거부한다.

### 8.3 운반 능력 검사

첫 그립 뒤 오른팔 권한을 닫고 목표와 무관한 작은 검증 외력을 기타에 가한다. 힘의 크기와 지속
시간은 사전 sweep으로 안전하면서 접촉 없는 상태와 안정 그립 상태를 구분하는 최소값을 선택한다.
검증 외력 후 다음을 만족해야 운반 가능한 그립 후보로 인정한다.

- 엄지+최소 세 손가락 유지
- 손–넥 상대 이동과 미끄럼이 허용 범위 안
- 과도한 침투·힘·관절 한계 없음
- 외력 종료 후 기타 속도가 안정됨

이 검사는 기준 자세와 체크포인트 평가에 사용한다. 학습 중에는 자연스러운 스트랩 하중과 실제
운반 결과를 우선 사용하고, 필요할 때만 낮은 확률의 커리큘럼 교란으로 추가한다.

## 9. 관측·로그·체크포인트

관측에 손가락별 lateral, 축 방향 간격, 미끄럼, 법선 힘 대리값, 접촉 히스테리시스 상태 및 5단계
one-hot을 추가한다. 최근 8프레임 입력은 유지한다. 관측 차원이 바뀌므로 체크포인트 schema를
`v10`으로 올리고 v9 체크포인트 재개를 거부한다.

학습 로그는 매 프레임 원시 접촉을 저장하지 않고 iteration 집계만 남긴다.

- 단계별 점유율과 전환율
- 손가락별 geometry/safe-loaded 성립률과 연속 유지 시간
- 손가락별 force p50/p95/max, slip, axial offset
- 엄지+1/2/3/4 손가락 이정표 획득률
- full-wrap 획득률, retained-wrap 비율
- 왼손 단독 운반 거리와 위치·회전 개선량
- 운반 전 오른팔/몸 지지 발생률
- 실패·종료 사유

접촉 쌍 원시 자료는 단일 환경 진단 결과에만 저장해 로그 용량 증가를 막는다.

## 10. 수정 파일

- `tab2body/stability_grip_geometry.py`: 손가락별 기하·법선 힘·접촉 히스테리시스 입력
- `tab2body/stability_pinch.py`: 5단계 상태, 손가락별 best/milestone, 운반 증거와 보상
- `tab2body/env/tasks/task_stability.py`: 손가락별 연속 권한과 오른팔 단계별 권한
- `tab2body/stability_task.py`: 커리큘럼과 제어 제한 설정 계약
- `tab2body/tools/probe_stability_grip.py`: 접촉 쌍별 `lambda`·마찰력 기록
- 새 보정 도구: 대리 지표와 실제 접촉 쌍 비교, 손가락별 힘 기준 생성
- `tab2body/train_stability.py`: v10 관측/체크포인트 manifest와 집계 지표
- 후속 Full 통합의 `tab2body/full/action.py`, `stability_bridge.py`, `stability_controller.py`:
  pre-handover GripSource 소유권, 이름 기반 target 변환과 인계 계약
- 관련 단위·통합 테스트와 문서

## 11. 구현 순서와 통과 기준

### 단계 A — 물리 가능성 확인

- [ ] 다섯 손가락의 실제 기타 접촉 쌍을 단일 환경에서 확인
- [ ] 각 손가락의 합력과 접촉 쌍 힘의 상관을 확인
- [ ] 안전한 열린손→감싸기 자세를 생성하고 침투를 검사
- [ ] 다섯 손가락 접촉 후 검증 외력을 견디는지 확인

여기서 실패하면 보상을 조정하지 않고 손 자세·넥 충돌 형상·관절 가동 범위를 먼저 수정한다.

### 단계 B — 측정과 보상 구현

- [x] 손가락별 측정값과 관측 추가
- [x] 접촉 히스테리시스와 품질값 추가
- [x] `FINGER_WRAP`, `LOAD_GRIP` 단계 추가
- [x] 일회성 손가락별 보상과 운반 게이트 추가
- [x] 오른팔 사전 사용 우회 차단
- [x] v10 schema와 상세 집계 로그 추가

2026-09-16 구현 상태: CPU 안정성 테스트 298개에서 단계 전이, 히스테리시스, 과도한 힘·미끄럼 거부,
왼손 운반 전 오른팔 우회 차단, 보상 상한을 확인했다. `probe_stability_grip`에는 CPU 접촉쌍 모드와
GPU 재생 모드를 분리했고, 두 결과를 비교하는 `calibrate_stability_grip_force`를 추가했다. 현재
코드의 힘 구간은 실제 probe 전까지 provisional이며 자동으로 보정값을 적용하지 않는다. 검증된 힘
파일과 closure/reach reset 파일이 없으면 일반 학습을 차단하고 smoke에서만 full-drop 진단을 허용한다.
closure/reach reset은 링크 위치와 속도가 갱신될 때까지 정책 표본에서 제외하고 기록된 자세를 유지한다.

단위 테스트에서는 잘못된 면, 다른 넥 위치, 관련 없는 합력, 과도한 힘, 보상 반복 획득이 모두
그립 성공으로 계산되지 않아야 한다.

### 단계 C — 짧은 학습 검증

- [ ] GPU smoke test에서 비유한값·차원·reset 오류 없음
- [ ] `closure` 평가에서 손가락별 safe-loaded 성립률이 0이 아님
- [ ] 모든 손가락의 참여가 증가하고 특정 두 손가락에만 수렴하지 않음
- [ ] full-wrap과 첫 그립 획득이 실제 평가에서 발생
- [ ] 오른팔을 닫은 평가에서 왼손 운반 15 mm 이상 발생

2,000회까지 손가락별 접촉이 전부 0이면 물리/관측 문제로 돌아간다. 5,000회까지 full-wrap이 0이면
장기 학습을 계속하지 않고 reset 분포와 보상 규모를 재점검한다.

### 단계 D — 전체 동작 검증

- [ ] `full_drop` 평가에서 정지 대기→접근→그립→운반→유지 전환 확인
- [ ] 초기 기타 위치·회전에 작은 노이즈를 준 hold-out 평가 통과
- [ ] 오른팔 차단 ablation에서 왼손 운반 증거 유지
- [ ] 같은 초기 상태의 왼팔 frozen/open 대조에서 passive strap 이동 envelope를 유의하게 초과
- [ ] 합력 보상 제거 ablation과 비교해 실제 접촉·운반률 개선 확인
- [ ] Fret 연결 시 손가락 권한을 반환할 수 있는 maintain 상태 확인
- [ ] 후속 Full 통합에서 standalone target replay와 GripSource→Fret 인계의 target 연속성 확인

## 12. 결정 사항

- 학습 중 손가락–기타 쌍별 힘을 가짜로 추정하지 않는다.
- 합력 크기만 키우는 보상을 사용하지 않는다.
- 다섯 손가락을 각각 관측하고 각각 학습 신호를 제공한다.
- 전체 그립은 다섯 손가락으로 획득하고, 운반 중에는 엄지+최소 세 손가락으로 히스테리시스를 둔다.
- 기타의 실제 목표 방향 이동과 손–넥 상대 유지가 있어야 “옮길 힘이 있는 그립”으로 인정한다.
- 오른팔 지지는 왼손 운반 증명 뒤에 연다.
- 태스크와 97축 action ABI는 유지하며, 관측 변경 때문에 새 체크포인트에서 학습한다.
