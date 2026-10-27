# 그래픽 격리 준비 자료 · CP241

## CP241 native capture

아래 비교 이미지는 완료된 CP241 평가의 저장된 Isaac Gym native frame에서만 만들었습니다. 물리 시뮬레이션이나 학습은 다시 실행하지 않았습니다. 원본 capture 기록은 30 fps, 492 frames, 16.3667초이며 renderer는 Isaac Gym native camera와 실제 strap-route overlay를 기록합니다.

![CP241 전체 장면의 실제 Isaac Gym 스트랩 표시 · 0초, 2초, 최종 16.3667초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v1/cp241_strap_full_scene_v1.png)

![CP241 손 장면의 실제 Isaac Gym 스트랩 표시 · 0초, 2초, 최종 16.3667초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v1/cp241_strap_hands_v1.png)

원본 [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/long_on_v2/evaluations/update_000241/native/episode_0001/media/capture.json)은 스트랩의 실제 routed cable path 시각화이며 천 두께·처짐이나 추가 물리를 포함하지 않는다고 기록합니다. 그림의 프레임은 capture frame 0, 60, 491이며 각각 0초, 2초, 16.3667초입니다.

## 완료된 reset probe v2 사실

별도 reset probe v2는 생성/반복을 60회 완료했고 한 에피소드 전체 horizon을 마쳤습니다. 비교 기록은 trace 983행과 controls 982행이 exact하며 position, quaternion, joint q, qdot 최대 절대차가 모두 0이라고 보고합니다. 이는 해당 probe와 저장된 비교의 결과이며, 모든 환경에서 오류가 발생하지 않는다는 보장은 아닙니다.

첫 probe는 reset 60회를 마친 뒤 학습 ABI에 진단 JSON 필드를 추가하는 과정에서 중단됐습니다. 원본은 보존했고 v2에서는 학습 ABI와 audit 입력을 분리했습니다.

## 그래픽 격리 범위

준비된 변경 범위는 학습 simulation에서 graphics device −1을 사용하고 별도 영상 평가에서 graphics device 0으로 native renderer를 쓰는 것입니다. physics, control, reward, baseline, 원본 strap 동작은 유지하는 범위입니다. CP242 평가와 후속 학습은 아직 완료된 결과로 취급하지 않으며 이 문서에서 성공으로 주장하지 않습니다.

## 입력과 산출물 기록

재사용 producer는 [build_cp241_strap_contact_sheet_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v1/build_cp241_strap_contact_sheet_v1.py)입니다. capture, 선택한 native frame, reset probe 비교 입력의 SHA 전후와 그림 출력 SHA는 [준비 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v1/cp241_preparation_provenance_v1.json)에 기록했습니다. 실제 변경 파일과 줄은 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v1/CHANGED_FILES.md)에 있습니다.
