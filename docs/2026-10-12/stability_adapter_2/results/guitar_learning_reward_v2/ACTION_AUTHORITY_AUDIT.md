# 보상 외 병목 후보: 전곡 동작 범위와 탐색

별도 에이전트 `/root/reward_v2_warmstart`가 현재 소스를 읽기 전용으로 확인했다. 이번 학습의 관측·행동·범위·gain은 변경하지 않았다. 아래는 물리 도달성 검증 결과가 아니라 정적 계약과 탐색 규모의 진단이다.

현재 39행동은 reset reference에 대한 절대 관절 목표 offset이다. 명령을 반복해도 누적 이동으로 허용 범위를 벗어나지 않는다. [control.py:77](/home/ajou/yigyu/3/guitar_learning/control.py:77), [control.py:118](/home/ajou/yigyu/3/guitar_learning/control.py:118).

| 역할 | 축 수 | reset 기준 설정 범위 |
|---|---:|---:|
| LH 팔: Thorax/Shoulder/Elbow/Wrist | 12 | ±0.35rad, 약20.05° |
| LH 손가락 | 21 | ±0.5rad, 약28.65° |
| RH Elbow/Wrist | 6 | ±0.25rad, 약14.32° |

원래 관절 제한으로 다시 잘린다. [원설정](/home/ajou/yigyu/3/guitar_learning/training_environment.py:26)과 [기존 전곡 저장 계약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/training_contract.json) 기준 `L_Shoulder_z` 증가 여유는 약1.622°, `L_Wrist_y` 감소 여유는 약0.012°다. `LH:ring2` 목표는 약60.68~90°, `LH:pinky1_x`는 약60.88~90°다. 다른 관절과의 조합으로 보완할 수 있으므로 이 수치만으로 특정 음의 도달 불가능을 뜻하지 않는다.

67음은4~12프렛·1~4번현·검지~소지를 사용한다. 기존 단음 성공은7프렛·2번현·약지 중심이었다. 별도 고정 정책 평가의 첫240Hz 표본에서 지정 손가락 distal-origin proxy와 전곡 목표의 거리는 약15.05~97.85mm였고, 검지가 맡는4~9프렛 목표의 기타 좌표 y 범위는 약127.39mm였다. 실제 접촉 패드 거리나 IK 도달성 결과는 아니다.

목표각 변화율은 팔/RH3rad/s, LH손가락1.5rad/s이고60Hz smoothing alpha=.2가 추가된다. 이것은 실제 관절 속도 제한과 구분한다. [native_session.py:8](/home/ajou/yigyu/3/guitar_learning/native_session.py:8), [control.py:121](/home/ajou/yigyu/3/guitar_learning/control.py:121). 23.3ms·81.3ms 전환은 필요한 관절 이동량과 접촉을 별도 확인해야 한다.

초기화 원본은 기존 전곡 `training_v2/final.pt`, SHA256 `f75f4ff1add887c37b7738708eec5040b4be564a65a42980a455d12f4337c817`다. latent std는 양손 모두 약.02다. 비포화·대칭 구간의 근사에서 requested target 탐색1σ는 LH팔약.40°, LH손가락약.57°, RH약.29°이고, 첫 smoothing 적용은 그1/5 수준이다. 정책 평균은 학습으로 전체 허용 범위에 이동할 수 있으므로 이 노이즈를 정책 전체 출력 범위로 해석하면 안 된다. [specialist_policy.py:117](/home/ajou/yigyu/3/guitar_learning/specialist_policy.py:117).

다음 확인 순서는 각 실제 목표의 현재 범위 내 안정적 도달·해제 가능성 검사, 여러 목표와 연속 두 음의 성공 궤적 확보, 목표 조건에 따른 손별 전환 학습, 이후 전곡 결합이다. 범위 확장은 필요성과 안전성을 확인한 경우에만 별도 버전으로 검증한다. 단순 보상 계수 증폭이나 무조건적인 범위 확대를 검증된 해법으로 제시하지 않는다.
