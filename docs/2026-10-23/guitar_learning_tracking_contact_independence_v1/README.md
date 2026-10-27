# GPU 왼손 추종 보상의 접촉 배율 제거 v13

활성 손가락 패드 추종 보상에서 `candidate`일 때 점수를2배 주던 항만 제거했다. 추종은 목표 거리와 근접 방향품질로 계산하고, 최초접촉·clean유지·연속달성의 기존 보상은 계속 지급한다. 후반 단계의 추종 비중 축소는 이번 변경에 포함하지 않았으며 실제 학습은 실행하지 않았다.

## 계산과 범위

~~~text
d = 지정 손가락 패드와 선택된 유한 목표까지 거리
near = clamp(1 - d/0.02, 0, 1)
A = 1 - 0.2 * near * (1 - clamp(normal_cos, 0, 1))
Q = (1 + d/0.04)^(-2) * A
rate = 2 * sum(valid selected Q) / 곡에 등장하는 손가락 수
~~~

원래의 `(1+candidate)`만 없앴다. 이전candidate=false 점수와 새 점수는 같고, 이전candidate=true의 추종 점수는 절반이다. 정상후보가 아닌데 새로 감점하거나 거리/방향을 바꾸지는 않는다. 최대 추종률은4/s에서2/s로 바뀐다. 한 손가락만 등장하고 거리0·정렬1인 예에서는 접촉 전후 모두2/s다.

목표 선택, 기본2/s,4cm거리scale,2cm 안에서만 최대20% 방향조정, 등장 손가락 수 평균,240Hz 적분, 속도/행동 비용0을 유지했다. 최초접촉의 연속50ms, clean유지의 누적시간 비례식, 음달성의 연속40%와0.5보너스, 손목·자세·오압현·물리안전·제어·PPO·CPU왼손/오른손은 그대로다.

공용 `finger_reward.py::finger_tracking_reward`의 v5 계약은 보존한다. 활성 `fingertip_pad.py::pad_tracking_reward`에서 중립후보 텐서를 전달해 원래 선택기·입력 형상/dtype검사·거리율을 재사용한 뒤 근접 방향품질을 적용한다. 기존 공용함수 직접호출의2배 동작을 새활성추종과 혼동하지 않는다.

## 계약

전체 보상은 `gpu_tensor_song_reward.v13`, 활성 추종은 `gpu_finger_tracking_rate.v7`이며 `candidate_multiplier=1`, 범위는 `[0,2]/s`다. 거리·법선·목표가 같을 때 candidate·속도·행동은 추종 품질을 바꾸지 않는다. candidate의 형상·dtype 검사는 유지한다.

표면 보상 묶음v6·표면 관측v4·원장v5·상태544/event24/priority8/커리큘럼3331값은 유지한다. v12 이하와 보상 의미가 달라 strict resume를 거부하며 동일v13 전체 계약만 복원한다.

## 검증

관련 **24모듈236개 CPU검사 모두 통과**했다. 새7개와 기존패드20개는 후보 배율 제거·독립 거리/방향수식·상한·빈/미할당 목표·움직임비용0·원입력 보존·공용함수 유지·실제 텐서환경에서 하중만 다른 행의 추종 동일성과 기존 최초접촉/유지/연속달성 보존·v13복원/v12재개거부를 확인했다. 나머지 회귀도 통과했다.

독립 change-reviewer가65개 CPU검사를 실행했다. 별도 스칼라 계산의212개 손가락slot 선택/품질과53개 최종율이1e-14 오차 이내로 일치했고, candidate전체반전에도 rate/quality/indices/valid가 정확히 같았다. 보관463개 SHA·기존공용helper 원문 동일성·447개 활성Python의 문법/동결SHA와 이전v12 보고서474개 파일 보존을 확인했다. 남은 코드 지적은 없다. [검사 목록·원문 로그](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_tracking_contact_independence_v1/cpu_tests.json)와 [검증 수치](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_tracking_contact_independence_v1/verification.json)를 보존한다.

이는 CPU 텐서로 GPU경로의 계산·관측·보상·저장 계약을 확인한 것이다. native/실제GPU 실행·장기학습 성과는 이번 범위에 포함하지 않는다. 기존 별도 GPU544/옛512 기대 불일치는 [이전 보고서](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_wrist_region_v1/README.md)에 보존했고 이번236개 검사 수에는 포함하지 않았다.

변경 전 v12의446개 Python과17개 관련 문서, 총463개 원문은 [보관 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261023_before_tracking_contact_multiplier_v1/manifest.json)에 보존했다. [이전v12 결과](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_continuous_clean_v1/README.md)는 그대로 유지한다.
