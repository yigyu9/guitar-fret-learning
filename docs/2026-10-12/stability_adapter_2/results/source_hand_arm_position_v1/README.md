# 팔 단일축 변경의 source 형상 비교

두 손목 seed에서 Thorax·Shoulder·Elbow의 아홉 축을 각각 ±0.025/±0.05 rad 바꾼 74개 제안을 비교했다. 각 seed의 기준 행 2개와 범위 안에서 형상을 계산한 제안 66개, 총 68개가 그림에 들어간다. Thorax 축의 숫자 범위를 벗어난 여섯 제안은 geometry 계산 전에 제외했다.

![두 손목 seed의 팔 단일축 source 형상 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/artifacts/arm_source_geometry.png)

그림의 빈 위치는 결측값이 아니라 원자료에 기록된 숫자 범위 제외다. 두 seed 각각 `L_Thorax_x −0.05`, `L_Thorax_x −0.025`, `L_Thorax_y +0.05 rad`가 빠졌다. 제외 행은 0으로 표시하지 않았다. 공유 x축 formatter 때문에 그림의 dagger 문자가 실제 tick label에 나타나지 않으므로 제외 위치를 여기서 명시한다.

세로축은 각 조건에서 보고된 모든 human–guitar 교차쌍 중 가장 큰 LP 공통내접반경(mm)이다. 점선은 해당 wrist seed의 기준행이다. seed마다 기준 대비 가장 작은 행도 교차를 남긴다.

| Wrist seed | 기준 최대 HG 반경 | 가장 작은 행 | 전체 초기각 변화 L2 | 최대 HG 반경 | HG 교차쌍 | palm–G 반경 |
|---:|---:|---|---:|---:|---:|---:|
| 0 rad | 4.288365 mm | `L_Thorax_y +0.025 rad` | 0.025000 rad | 2.212093 mm | 5 | 0 mm |
| −0.1 rad | 2.076522 mm | `L_Thorax_z +0.025 rad` | 0.103078 rad | 1.231576 mm | 5 | 1.079516 mm |

표의 palm–G 반경 0 mm는 해당 행에 보고된 palm–G 교차쌍이 없는 집계값이며, 실제 표면거리가 0이라는 뜻은 아니다.

모든 68개 형상 계산 행에서 human–guitar 교차가 남았다. 양손 간 형상 검사와 self 1,188쌍 검사는 모두 비교차였고, palm-up proxy 최솟값은 0.925554였다. 열 조건에서는 thumb2의 보고 교차가 없었지만 다른 HG 교차쌍이 남아 전체 clearance 조건이 되지 않았다. 한 부위의 반경을 줄이며 다른 부위 교차를 남기는 tradeoff가 관측됐다. 이는 검사한 68개 행의 결과이며, 전체 팔 가동범위의 불가능성을 뜻하지 않는다.

LP 공통내접반경은 저장된 source 형상에서 계산한 값이다. PhysX cooked 형상의 침투 깊이, 실제 접촉, 지지력이나 안정성 인증이 아니다. 이번 phase에는 후보 선택이나 proposal/native/5초 실행이 없고 새 physics, actor inference, training은 모두 0이다. 기존 실제 영상 152개도 그대로 유지한다.

| 저장 입력·기록 | 확인 내용 |
|---|---|
| [search.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/search.json:1) | 74개 제안, 여섯 범위 제외, source 형상 결과 |
| [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/analysis.json:1) | 11개 분석 검사 통과, 68개 HG 교차 잔류, 선택 후보 없음 |
| [source arm 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md:1) 및 [범위 실행 기록](/home/ajou/yigyu/3/stability_adapter_2/ARM_POSITION_EXECUTION.md:1) | 두 seed·74 제안과 numeric 범위 선제외 규칙 |
| [bounded 연속 팔 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:1) | 후속 계획. 아직 미실행이며 이번 결과에서 수행하지 않음 |

산출물 생성은 Python 3.8 환경에서 저장 입력과 source closure SHA를 확인한 뒤 한 차례 실행했다. 82개 보존 파일의 복사 SHA가 원본과 일치하고, 실행 전후 입력 해시가 같으며 exit code는 0이다. 후처리에서 새 native/physics/actor/training 실행은 없었다. PNG·실행·SHA 기록은 [artifact index](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/CHANGED_FILES.md:1>)에 연결했다.
