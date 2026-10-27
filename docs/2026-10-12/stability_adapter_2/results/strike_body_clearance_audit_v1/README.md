# Strike 가상 피크와 기타 body 앞면 여유 감사

저장된 native 자세에 원본 XML/STL 형상을 적용한 정적 계산이다. 가상 피크의 정상 경로 자체는 Gbody box 침투를 요구하지 않는다. 그러나 손의 방향에 따라 ring/pinky 형상이 피크보다 훨씬 body 쪽으로 돌출한다. 피크 위치만 맞추는 제어는 전체 손 형상의 여유를 보장하지 않는다.

## 입력과 계산 범위

- POSITION: [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/initial_values.json), [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/trace.json), [controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/controls.json): 152개 저장 상태, 300개 제어 기록.
- EFFORT: [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/native/data/initial_values.json), [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/native/data/trace.json), [controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/native/data/controls.json): 151개 저장 상태, 300개 제어 기록.
- body 순서는 각 initial_values의 이름으로 찾았다. RHpick index51을 가정하여 계산하지 않았다. 각 mesh의 STL vertex에 asset scale, geom pose, 저장된 native body pose를 차례로 적용했다.
- source mesh는 [fixedlower XML](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:39)의 thumb/index/middle/ring/pinky 15개와 palm이다. 이 RH 형상들은 capsule/box가 아니라 `type="mesh"`다. [ring geom](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:343)과 [pinky geom](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:363)의 offset도 포함했다.
- 결과 [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_body_clearance_audit_v1/summary.json)에 모든 저장 상태, 각 segment 최소점, footprint 여부, source box 안의 vertex 수, 접촉 raw lambda와 읽은 입력 SHA256를 보존했다.
- A 코드·자산·physics를 수정하거나 실행하지 않았다. 감사 계산에서 새 D의 지정한 세 파일만 생성했다. simulator 초기화0, physics step0. geometry 최초 읽기 후 SHA를 수집했고, 그 수집 시점부터 종료까지의 SHA 대조 일치를 확인했다. **최초 geometry 읽기 전의 사전 봉인은 아니다.** 이 검증 범위 경고는 source FK/current 함수 일치나 계산 수치가 틀렸다는 finding이 아니다. 수정 전 README는 [보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/doc_before_hash_scope_review/strike_body_clearance_audit_v1.README.md)에 남겼고, 소비된 analysis.py와 summary.json은 수정하지 않았다.

## 앞면과 source 목표의 관계

[Gbody XML](/home/ajou/yigyu/3/tab2body/assets/guitar_asset.xml:124)의 body pos는 `(0,−.4,−.0217)m`, box half-size는 `(.15,.17,.02)m`이다. 따라서 앞면은 **Gz=−1.7mm**, footprint는 Gx±150mm/Gy−570~−230mm이다. neck의 +9.3mm 면과 다른 면이다.

아래 gap은 **앞면 −1.7mm를 기준으로 바깥 +Gz 방향으로 잰 간격**이다. Gz 위치와 같은 숫자가 아니다.

| source 점 | Gz 위치 mm | Gbody 앞면 기준 gap mm |
|---|---:|---:|
| string surface | 12.3 | 14.0 |
| READY | 20.3 | 22.0 |
| ENTRY | 10.8 | 12.5 |
| EXIT, clearance override 전 | 10.8 | 12.5 |
| recovery lift | 22.3 | 24.0 |

checkpoint의 `ready_height=.008`, `crossing_depth=.0015`, `clearance_height=.010m`와 [source waypoint 식](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:1427)을 사용했다. ENTRY/EXIT의 깊이는 string surface에서 아래로1.5mm이며 Gbody 앞면까지 내려가라는 목표가 아니다. recovery 중 geometry5는 source lift/next-entry-lift/next-ready로 바뀔 수 있다.

[grip reference](/home/ajou/yigyu/3/strike/02_physical_control/pick-grip-reference.json:11)는 pick_tip을 RHpick origin으로 정의하며 physical_pick_geometry=false다. [RHpick XML](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:297)은 index2에 붙은 `(7,−48,−5)mm` marker이며 geom이 없다. [실제 detector](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3632)는 이 body origin을 guitar frame으로 변환하여 사용한다. 별도의 nonzero virtual tip offset은 없다.

## 저장된 native 자세에서 source 형상 최소 여유

모든 수치는 mm. thumb/index/middle/ring/pinky는 각 branch의 source mesh vertex 중 앞면까지의 최소 signed projection이다. 음수는 source vertex가 무한 앞면의 뒤쪽에 있다는 뜻이다. 다음 표의 음수 최소점은 box XY footprint 안에도 있다. 접촉 열은 같은 시간의 controls에 기록된 **양의 raw lambda를 가진 body**다.

| POSITION native 시간 s | pick origin gap | thumb | index | middle | ring | pinky | 양의 Gbody 접촉 |
|---|---:|---:|---:|---:|---:|---:|---|
| 0.000000 | 51.202 | 53.445 | 57.731 | 56.078 | 54.497 | 62.835 | 없음 |
| 1.000000 | 2.912 | 10.604 | 9.834 | 5.453 | −0.628 | 3.242 | ring3 |
| 1.200000 | 19.059 | 29.447 | 23.002 | 14.433 | 1.741 | −0.191 | pinky3 |
| 1.333333 | 9.702 | 18.216 | 15.251 | 8.703 | −0.644 | 1.552 | ring3 |
| 1.366667 | 9.000 | 15.768 | 15.413 | 10.230 | 3.535 | 8.621 | 없음 |

| EFFORT native 시간 s | pick origin gap | thumb | index | middle | ring | pinky | 양의 Gbody 접촉 |
|---|---:|---:|---:|---:|---:|---:|---|
| 0.000000 | 51.202 | 53.445 | 57.731 | 56.078 | 54.497 | 62.835 | 없음 |
| 1.000000 | 27.472 | 38.005 | 34.990 | 32.143 | 25.486 | 29.034 | 없음 |
| 1.166667 | 12.322 | 19.265 | 17.861 | 10.292 | 2.584 | 6.250 | 없음 |
| 1.200000 | 10.462 | 16.925 | 15.621 | 7.364 | −0.718 | 2.694 | ring3 |
| 1.366667 | 15.204 | 21.043 | 18.944 | 9.182 | −0.558 | 1.102 | ring3 |

1.35초 native snapshot은 없다. 앞뒤 실제 저장 시각1.333333/1.366667을 별도로 보존했고, requested1.35의 최근접 선택은1.366667이다. 보간하지 않았다. 5초 상태에 붙은 contact는 마지막 controls4.983333초 기록이며 JSON에 별도 시간으로 표시했다.

최초 양의 RH–Gbody 접촉은 POSITION .983333초 ring3(`lambda=16.26754`), EFFORT1.2초 ring3(`12.85483`, `15.28659`)다. EFFORT1.2초 ring의 source 최소점은 G좌표 약 `(.07987,−.30403,−.00242)m`이며, pick origin보다 **11.180mm 더 body 쪽**이다. POSITION1.2초에는 pinky가 pick보다19.250mm 더 body 쪽이다. 피크 origin 여유10.462mm는 string surface가 아니라 **Gbody 앞면 기준 gap**이다.

## 여섯 hinge와 네 hinge +0.2rad의 정적 FK 비교

실행에 소비된 [calibrated_fk](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/native/source_before/stability_adapter_2/underneck_initial_search.py:28)만 AST로 추출하여 호출했다. 현재 A의 같은 함수 AST와 일치한다. 실제1.2초 pose/q를 calibration으로 사용하여 baseline을 정확히 보존하고, native scalar bounds로 clip한 후보만 계산했다. 원래 native-initial calibration + 현재 Chest 보정도 독립 비교했다. 원래 calibration의1.2초 RH pose 오차 최대는 POSITION .06962mm/.10164deg, EFFORT .06495mm/.09442deg이며 결론의 방향은 동일했다.

아래 역시 Gbody 앞면 기준 gap(mm)이다.

| trial1.2초 | 변경 | middle 최소 | ring 최소 | pinky 최소 | free12 reference RMS rad |
|---|---|---:|---:|---:|---:|
| POSITION | 실제 baseline | 14.433 | 1.741 | −0.191 | .027538 |
| POSITION | middle2/3+ring2/3 네 hinge | 21.981 | 6.521 | −0.191 | .120716 |
| POSITION | 위 네 hinge+pinky2/3 여섯 hinge | 21.981 | 6.521 | −0.707 | .137090 |
| EFFORT | 실제 baseline | 7.364 | −0.718 | 2.694 | .032123 |
| EFFORT | middle2/3+ring2/3 네 hinge | 17.106 | 5.781 | 2.694 | .126692 |
| EFFORT | 위 네 hinge+pinky2/3 여섯 hinge | 17.106 | 5.781 | 3.049 | .144740 |

네 hinge 후보의 pick origin, pinch9, pinky4 및 나머지77좌표는 그대로다. M/R 결과는 six 후보와 같다. 여섯 hinge를 일괄 늘릴 때 pinky를 안전하게 접는다는 일반 결론은 성립하지 않는다. single-hinge 비교에서 pinky2 +.2는 POSITION/EFFORT 여유를 각각1.457/.966mm 줄였다. 모든 선택 snapshot의 네 hinge 후보도 JSON에 보존했다.

reference pose 자체에서 네 hinge만+.2면 free12 RMS는.115470rad이다. source 성공 판정의 free RMS 한계.261799rad와 source 정책의 개별 free residual cap±.22rad는 별개다. 실제1.2초 EFFORT 후보는 middle2 reference delta .224943, ring3 .267107rad로 개별 residual cap을 넘는다. POSITION은 ring3 .257216rad가 넘는다. native bounds 내 후보이며 성공 RMS 조건 아래라는 사실만 확인했다. source action/학습 profile 전체 호환성 또는 실제 grip 성공을 판정하지 않았다.

## 위치만 정확히 맞출 때 남는 기하 한계와 다음 단일 요인

현재 손 orientation/finger pose를 유지하고 손 전체를 앞면 normal 방향으로 평행이동하여 pick gap만 ENTRY/EXIT의12.5mm에 맞춘 정적 사고실험도 계산했다. 실제 도달 가능한 팔 움직임이나 native contact 예측이 아니다.

- POSITION1.2초 baseline의 ring/pinky 최소 여유는−4.818/−6.750mm다. 네 hinge 후에도 ring−.037mm/pinky−6.750mm다. 이 방향 그대로 ENTRY에 맞추는 것만으로 모든 형상을 front-plane 밖에 둘 수 없다.
- EFFORT1.2초 baseline은 ring+1.320/pinky+4.732mm, 네 hinge 후 ring+7.819/pinky+4.732mm다.
- EFFORT2초는 손 방향이 달라져 baseline에서 middle−19.024/ring−32.871/pinky−34.114mm다. 네 hinge 후에도 middle−11.649/ring−23.041/pinky−34.114mm다. 늦은 시점에는 이 굽힘만으로 전체 손 방향 문제를 해결할 수 없다.

다음 **한 요인** 후보는 middle2/3+ring2/3 네 hinge의 작은 positive curl이다. 최초 EFFORT ring 접촉 주변에서 source 형상 여유를 직접 늘리고 pinch/pick/pinky를 보존한다는 근거가 있다. 전체six 일괄 curl은 추천하지 않는다. 네 hinge만으로 late PLAY clearance, 원래 grip 제어범위, 실제 native 접촉 해소 또는 타현 성공을 보장하지 않는다. orientation 후보와 동시에 바꿔 이 계산을 성공 원인으로 해석하지 않는다.

## source 형상과 native 접촉의 구분

STL vertex의 front support는 그 vertex convex hull의 front support와 같다. 그러나 native cooked hull, importer 처리, contact margin/offset은 확인하지 않았고 이 projection을 native 접촉 signed distance로 부르지 않는다. [SDK mesh 설명](/home/ajou/yigyu/3/isaacgym/docs/programming/assets.html:157)은 기본 PhysX mesh collision을 단일 convex hull 근사로 설명한다. [native 환경](/home/ajou/yigyu/3/stability_adapter_2/environment.py:60)의 contact_offset=.002m/rest_offset=0와 XML hand margin=0도 실제 native shape별 readback과 구분해야 한다. raw lambda는 측정 Nm/N 힘이나 causal impulse 인증이 아니다. 기타 회전의 원인을 이 감사만으로 확정하지 않았다.

계산 진입점은 [analysis.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_body_clearance_audit_v1/analysis.py)이며 `/home/ajou/miniconda3/envs/rl38/bin/python`을 사용했다. 기존 입력 파일은 읽기만 했다. geometry 최초 읽기 이후 수집한 SHA와 종료 SHA의 일치, 전체 raw 개수, RHpick 무형상, 16개 RH mesh를 검사했다. 최초 읽기 전 무변경까지 검증한 것으로 해석하지 않는다. 소비된 script와 summary는 보존하므로 기존 출력 경로에서 재실행하여 summary를 덮어쓰지 않는다.
