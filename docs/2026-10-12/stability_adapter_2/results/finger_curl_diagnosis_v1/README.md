# 중지 굽힘과 저장 접촉 기록

이 요약은 고정 LA·어깨 +0.008 rad 조건의 기존 5초 native 결과를 읽었다. 분석은 4개 검사 통과, 손가락 21개 scalar target이 1200 step 동안 일정함을 확인했으며 새 native/actor/학습 실행은 없다.

| 손가락 | finger2 유지 목표 (°) | finger3 시작 (°) | finger3 유지 목표 (°) | finger3 실제 5초 (°) |
|---|---:|---:|---:|---:|
| 검지 | 60.685 | 7.063 | 7.991 | 7.975 |
| 중지 | 64.343 | 60.146 | 60.684 | 60.684 |
| 약지 | 49.586 | 5.169 | 2.954 | 2.955 |
| 소지 | 57.801 | 32.154 | 33.027 | 33.027 |

중지 말단 관절의 큰 scalar 각도는 처음부터 약 60.146°였고, 유지 목표도 약 60.684°라서 5초 뒤에도 그 값에 머물렀다. finger2 목표도 약 64.343°다. 따라서 손가락 굽힘 전체를 middle3 하나로 설명하지 않는다. 제어기는 손목 x 파형을 조정하지만 손가락 reach를 접촉에 맞춰 적응시키지 않으며 21개 target은 일정하다. 이 기록만으로 현 길이가 중지 굽힘에 필수라고 판정할 counterfactual 비교는 없다. 표의 값은 scalar 관절 좌표이며 전체 관절 방향, 해부학적 DIP 인증, 자연스러움 판정이 아니다.

## 손가락 말단 body 접촉 기록

| body | 양의 raw λ 기록 step 수 | 첫–마지막 step | 2초 이후 step 수 | 기록된 기타 body |
|---|---:|---:|---:|---|
| thumb3 | 9 | 35–43 | 0 | guitar/guitar |
| index3 | 1145 | 54–1200 | 721 | guitar/guitar |
| middle3 | 18 | 26–44 | 0 | guitar/G:fret4 |
| ring3 | 0 | 없음 | 0 | 없음 |
| pinky3 | 0 | 없음 | 0 | 없음 |

양의 raw lambda는 N 단위 힘 측정이 아니다. 이 표만으로 기하학적 비접촉, 해부학적 패드 위치, 자연스러운 손 모양 또는 지속 지지를 주장하지 않는다. 특히 middle3 기록은 step 44 뒤에 없고, index3의 기록은 2초 이후에도 이어진다.

아래는 새 진단 렌더가 아니라 직전 +0.008 rad native 실행에서 재사용한 실제 시작/종료 hands frame이다. 접촉 영역이나 finger-label overlay는 없다.

| 시작 frame | 5초 종료 frame |
|---|---|
| ![기존 plus008 native hands frame 00000 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00000.png) | ![기존 plus008 native hands frame 00150 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00150.png) |

## 다음 접촉 영역 시각화 설계

[접촉 영역 계획](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_REGION_PLAN.md:13)은 기타 local 좌표의 전면·후면·옆면 finite patch, 손가락 안쪽 후보 patch, 실제 접촉점을 서로 다른 색/표식으로 보여주는 관측 전용 설계다. 이는 이번 프레임에 그려지지 않았고 제어나 reward를 바꾸지 않는다. 나중에 간격·법선·자세를 평가하더라도 8월 19일/task 조건별 손 자세 참고를 쓰며 모든 손가락에 동시 접촉을 요구하지 않는다. 스트랩 LA는 고정하고 최종 66관절 제어권은 유지한다.

[저장 분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_curl_diagnosis_v1/analysis.json:1), [원본 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/initial_values.json:1), [실제 states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/states.jsonl:1), [목표 controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/controls.jsonl:1), [contacts](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/contacts.jsonl:1).
