# 학습 초기화: 손 준비 기본 2초

사용자 요청대로 학습 reset마다 기존 22초 준비·검증 스케줄을 재생하지 않는다. 현재 진입점은 [guitar_learning.environment](/home/ajou/yigyu/3/guitar_learning/environment.py)이며, 기본값은 **2초**, `preparation_seconds`로 1~2초 범위의 60Hz 제어 구간을 선택할 수 있다.

## 변경한 동작

기존에 실제 검증한 준비 완료 표본의 사람 관절 위치·속도와 기타 강체 상태, 최종 제출 목표를 reset 초기값으로 한 번 사용한다. 그 뒤 기존 유한 제어로 손 준비·안정화 2초를 수행하고 정책에 제어권을 넘긴다. 기존 원본의 10초·16초 보정을 생략한 채 단순히 시간을 자른 방식은 아니다.

원 native 생성자가 먼저 FK·발/지지 기준과 제어기를 구축한다. 이후 사람 DOF 상태 1회, 기타 강체 상태 1회, 초기 POSITION 목표 1회를 설치한다. 사람의 관절 연결 강체 전체를 직접 덮어쓰지 않는다. 초기화 구간은 항상 닫히며 이후 실제 물리가 시작된 뒤의 상태 덮어쓰기는 금지한다. 기타에 직접 보조 힘을 주지 않는다.

기존 Chest·hip·발·SO3 유지 제어의 시간별 ramp는 명시적으로 성숙한 제어 단계에서 평가한다. 제어 단계만 `5280 + actual_step`이고 실제 scene/native 시간은 **0부터 480(2초)**까지다. 이전 22초 물리를 숨겨 실행하거나 실제 경과 시간으로 더하지 않는다. 원 targets/Motion의 긴 스케줄은 호출하지 않는다.

준비 입력과 모델의 SHA 검사는 프로세스당 한 번 캐시하고 각 reset에는 독립된 초기값을 전달한다. 원 native 생성자의 자산 로딩과 입력 호환성 검사는 유지한다. 원본 소스·모델·22초 실험 기록은 보존했다.

## 현재 코드

- [environment_v4.py](/home/ajou/yigyu/3/guitar_learning/environment_v4.py): 기본 2초의 학습 초기화와 정책 인계.
- [prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py): 준비 상태 1회 초기화, 입력 캐시, 실제 시간과 제어 단계 분리.
- [fretting_environment_v2.py](/home/ajou/yigyu/3/guitar_learning/fretting_environment_v2.py): 새 환경의 240Hz 실제 접촉 측정.
- [run_fretting_probe_v3.py](/home/ajou/yigyu/3/guitar_learning/run_fretting_probe_v3.py): 이번 연결 확인용 실행기. 학습 reset에서 매번 실행하는 검증이 아니다.

`environment_v3.py`, `fretting_environment_v1.py`, `run_fretting_probe_v2.py` 및 `run_smoke_v7.py`는 이전 22초 방식의 재현용이다. 새 학습에서는 현재 진입점을 사용한다.

## 확인한 결과

CPU 검사 **59개 통과**. 실제 연결 시험은 **준비 2초 + 행동 0 유지 1초**, 총 3초를 한 번 수행했다. 실제 표본 번호는 초기 0 → 준비 완료 480 → 최종 720이며 원래 5280 단계 준비를 반복하지 않았다. 종료 코드 0, import 소스 pin 누락과 원본 소스 대조 오류가 없었고 실행 입력은 불변이었다.

| 지표 | 결과 |
| --- | ---: |
| 준비 후 실제 측정 표본 | 241개 |
| 가슴·오른상완·오른허벅지 동시 양성 지지 | 241/241 |
| 기존 진단 목표(현1/프렛5/검지) 접촉 후보 | 241/241 |
| 유지 1초의 접촉 후보 유지율 | 1.0 |
| 초기화 직후 → 2초 준비 종료 기타 이동/회전 | 0.489881mm / 0.067657° |
| 준비 종료 대비 유지 1초의 최대 기타 이동/회전 | 0.040842mm / 0.005892° |

초기 관절 위치·속도 readback 차는 0이었다. 사람 강체 자세는 native 관절 운동학으로 재구성되므로 저장된 모든 강체 좌표와 완전히 같은 checkpoint라고 주장하지 않는다. 이번 초기 readback의 최대 위치 차는 약 15.41µm, 회전 차는 약 0.01735°였다. PhysX 접촉/solver 내부 상태를 저장·복원한 결과도 아니다.

이 결과는 짧은 초기화와 제어 인계의 연결 확인이다. 장시간 V3 검증, 새로운 압현 동작의 학습, 실제 현 압력·진동·음향 성과가 아니다. 1초 옵션은 CPU로 검사했고 실제 시험은 2초 기본값으로 수행했다. 새 PPO 업데이트는 0이다.

## 기록

- [전체 CPU 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/cpu_tests.log)
- [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/preflight_review.md)
- [실제 실행 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/native_v1/report.json)
- [원자료 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/native_analysis.json)

![실제 준비 2초와 유지 1초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/native_v1/media/whole_body.mp4)

영상은 원 native 카메라의 5fps 16프레임이며, 시작 프레임을 포함해 파일 길이는 3.2초다. 실제 물리 경과 시간은 3초다.
