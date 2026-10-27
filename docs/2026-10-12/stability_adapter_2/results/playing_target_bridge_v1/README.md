# 연주 target bridge CPU 검증 요약

이번 phase는 `contract.json`의 CPU target/history 하위계약과 저장된 정책 평가를 요약한다. source target 60개와 Thorax 기준 6개를 하나의 81D native target으로 합성하는 구현에서 10개 계약 검사가 모두 통과했다. 이는 실제 연주·기타 안정화·자유 기타 정책 호환성을 통과했다는 의미가 아니다.

## 평가된 Fret 기록과 profile 간격

왼쪽은 저장된 두 Fret full-song evaluation의 `f1_l`이다. 두 값은 Fret 동일 task의 F1이고, Strike 지표는 이 panel에 섞이지 않는다. 오른쪽은 실제 −2 mm 유지조건의 PD target과 측정 초기 q 각각을 Fret 유효 profile 구간까지 옮기는 데 필요한 `required_min_target_change_rad`를 도 단위로 나타낸다. 각 막대는 부호 없는 최소 profile 이동폭이지 제안된 각도나 안정된 초기 자세가 아니다.

![저장된 Fret 평가 F1과 실제 target/q의 profile 최소 보정폭](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/playing_bridge_summary.png)

| Fret 기록 | 평가 범위/단계 | 저장 `f1_l` |
|---|---|---:|
| `fret_047000` | `goal_pair`, full-song stored evaluation | 0.1000981 |
| `fret_047500` | `goal_pair`, full-song stored evaluation | 0.0734856 |

47,000은 stalled `goal_pair` 단계의 진단 후보일 뿐이며, 47,500도 낮은 F1을 보인다. 둘 다 strict G0 적격으로 인증되지 않았다. evaluation 파일은 checkpoint 경로와 contract 연결을 기록하지만 평가 당시 checkpoint file SHA는 없다. 현재 checkpoint SHA를 과거 평가 시점 파일의 무결성 증거로 간주하지 않는다.

| Fret 관절 | 실제 baseline PD target → 유효 profile까지 (°) | 실제 initial q → 유효 profile까지 (°) |
|---|---:|---:|
| `LH:thumb1_x` | 5.430 | 9.580 |
| `LH:thumb1_y` | 35.389 | 37.888 |
| `LH:thumb3` | 28.866 | 34.437 |
| `LH:index1_x` | 11.729 | 9.678 |
| `LH:middle3` | 5.284 | 4.745 |
| `LH:ring1_x` | 11.823 | 8.107 |

6개 모두 현재 PD 유지 target이 Fret source의 유효 profile 밖에 있다. 가장 큰 필요 이동은 baseline PD target의 `LH:thumb1_y`에서 35.3886205°이고, 실제 initial q에서는 같은 관절의 37.8879097°다. Warm-start bridge는 이 불일치를 거절한다. 이 폭은 profile interval까지의 최소 unsigned 거리이지 움직였을 때의 물리 반응이나 새 target 선택이 아니다.

Strike 10,000은 별도 직접 평가에서 64 single-pick episode의 F1 1.0과 timing p95 5.628 ms를 보였으나 candidate evidence에 머문다. Strike 10,708은 중단된 저장 checkpoint이며 직접 평가가 없다. Strike 10,000을 포함해 모든 source가 strict G0 qualified 상태는 아니다. Strike 자료는 Fret F1 그림에 포함하지 않았다. 상세 기록은 [source/평가 연결 및 SHA 계약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/contract.json:1)에 있다.

## CPU bridge의 확인 범위와 한계

원본 `Base.apply_actions` AST의 80 step × batch 17 비교에서 residual 0의 최대 target 차이는 `2.384185791015625e−7 rad`였다. 이는 float32 반올림 차이가 남는 결과라 bitwise identical이라고 부르지 않는다. 최종 history를 decode한 최대 오차는 `1.1920928955078125e−7 rad`다. Source Fret 30 + Strike 30 + Thorax 6의 residual 권한과 66개 gradient 경로를 검사했고, held 15개 target은 정확히 유지됐다.

이 검증은 `420/303` 전체 observation 처리, 실제 source 후처리 연결, actor 실행 또는 physics를 구현하지 않았다. 정책의 이전 최종 목표를 source action history 표현으로 되돌리는 CPU 하위계약과 81D target 합성만 확인했다. 초기 유지 target이 source profile을 벗어나면 warm-start가 거절되어야 하며, 이 결과를 연주 성공이나 학습 준비 완료로 해석하지 않는다.

다음 후보 방향은 이 Fret profile과 양립하는 초기 자세를 별도 검토하는 것이다. 어떤 관절각을 선택하거나 새 물리 실행을 승인하는 결정은 이 artifact에 포함하지 않는다. root의 후속 결정 기록에서 조건을 정리한다.

## 이전 native 자료

아래 frame과 두 영상은 **이전 −2 mm native batch의 실제 Isaac Gym 캡처**다. 이번 CPU bridge phase에는 native 실행, 새 video, 새 video collection이 없다. 실제 렌더 자료와 위의 CPU 요약 chart를 구별한다. 공유 영상 collection은 128개 상태 그대로 둔다.

![이전 −2 mm native batch의 actual hands camera t=0 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/frames/hands/00000.png)

이전 −2 mm hands 영상: ![이전 native hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/hands.mp4)

이전 −2 mm whole-body 영상: ![이전 native whole-body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/whole_body.mp4)

## 재현 기록

그림 producer와 CPU checker wrapper 및 관련 source 파일은 첫 producer 실행 전에 `artifacts/source_snapshot/`으로 복사하고 SHA를 대조했다. 명령·exit code 0·로그·source/input 전후 SHA와 PNG SHA는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/artifact_manifest.json:1), [producer execution record](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/producer_execution.json:1), [producer log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/producer.log:1), [pre-run source snapshot](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/source_snapshot.json:1)에 보존했다. 이 그림 실행의 native initialization, physics, actor inference, training update는 모두 0이다.

계약/실행 원자료는 [contract.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/contract.json:1), [execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/execution.json:1), [execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/execution.log:1)이고, producer는 [make_playing_bridge_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_playing_bridge_artifacts.py:1)다.
