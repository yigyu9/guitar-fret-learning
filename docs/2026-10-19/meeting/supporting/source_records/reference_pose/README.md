# 현재 기타 연주 초기 자세 — 실용 V3

2026-10-17 기준. **front_facing_ready_v1의 기존 035 설정과 native v14 실행**을 모은 자료다. 하체 관절을 잠그지 않은 상태에서 다섯 개별 시험을 통과한 **실용 초기 자세 후보**이며, 전체 연속 수행이나 범용 제어기를 완성한 결과는 아니다.

## 자료 찾기

| 자료 | 내용 |
|---|---|
| [자세값·제어 설정](/home/ajou/yigyu/3/paper/initial_pose/current_v3/VALUES.md) | 출발 관절값, 준비 후 22초 실제 상태, 다섯 실행 설정, 제어 코드 |
| [정면 전신 60fps 영상](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/README.md) | 왼손 해제·오른손 타현·넥 재접촉, 저장 몸체 자세의 33초 편집 재생 |
| [이미지·영상](/home/ajou/yigyu/3/paper/initial_pose/current_v3/MEDIA.md) | 준비 자세의 세 시점, 다섯 실행의 전신·측면·발 영상과 관찰 구간 |
| [최신 요구조건](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/REQUIREMENTS_v3.md) | 유지한 필수 조건과 V3에서 완화한 조건 |
| [실제 결과 원문](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/practical_criteria_v3/RESULTS_v2.md) | 측정값·판정·출처·한계 |
| [최신 상태와 이전 기록](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/WORK_STATE.md) | 문서 맨 위가 최신이며 아래는 시간순 과거 기록 |
| [파일 출처 목록](/home/ajou/yigyu/3/paper/initial_pose/current_v3/manifest.json) | 원본 경로·SHA-256·사본과 영상 연결 경로 |
| [정리 검증](/home/ajou/yigyu/3/paper/initial_pose/current_v3/VERIFICATION.json) | 사본 일치·링크·선택 원본 불변·영상 확인 |

## 자세와 제어의 범위

Root만 고정하고 하체는 유한한 제어로 유지한다. 전체 105 입력 채널 중 원래 가동범위가 0이 아닌 축은 97개다. 나머지 8축의 원래 범위는 보존하며, 명목상 영범위가 실제 움직임까지 항상 0이라는 뜻은 아니다. 기타는 중력이 적용되는 자유 강체이고 스트랩은 사용하지 않는다.

가슴·오른쪽 상완·허벅지의 실제 접촉을 주요 지지로 사용한다. 기타를 직접 고정하거나 보조 힘으로 떠받치지 않는다. 인체의 자세 유지 제어는 사용하므로 수동 평형 자세로 설명하지 않는다. 타현 목표 변화는 오른팔꿈치·손목에 주고 오른손 파지 목표와 피크의 손 상대 배치는 유지한다.

[출발 candidate](/home/ajou/yigyu/3/paper/initial_pose/current_v3/pose/candidate.json) 하나만으로 준비가 끝나지 않는다. 기존 준비 보정과 **17–22초 정지 유지**를 포함한 설정·제어가 함께 필요하다. 최종 준비 상태를 확인하려면 [baseline의 22초 실제 상태](/home/ajou/yigyu/3/paper/initial_pose/current_v3/pose/prepared_state_baseline_v14_22s.json)를 참고한다. 이는 원자료에서 추출한 관측값이며 재시작 체크포인트가 아니다.

## 개별 시험 결과

| 시험 | 실제 실행 | 증거 구분 | V3 |
|---|---:|---|---|
| 정지 유지 | 28초 | 기존 v14 기록 재평가 | 통과 |
| 반복 타현 | 34초 | 기존 v14 기록 재평가 | 통과 |
| 왼손 완전 해제 | 40초 | V3 기준을 정한 뒤 새 실행 | 통과 |
| 해제 상태 타현 | 40초 | V3 기준을 정한 뒤 새 실행 | 통과 |
| 넥 재접촉·준비 복귀 | 49초 | V3 기준을 정한 뒤 새 실행 | 통과 |

다섯 실행 모두 준비 후 17–22초에 가슴·오른쪽 상완·허벅지의 동시 양성 지지 접촉이 100%였다. 일반 타현과 해제 상태 타현은 각각 세 왕복의 여섯 줄 기하 통과를 확인했다. 왼손 해제는 25–40초의 연속 15초로 평가했으며, 해제 상태 타현의 삼중 지지는 99.888920%였다.

재접촉 시험의 접근·닫기·정착·복귀 후 유지 구간에서 삼중 지지는 각각 100%였다. **왼손 손가락–넥 접촉은 별도 지표**다. 43–44초 정착에서는 32.780083%, 44–49초 준비 유지에서는 100%였다. 재접촉 전 과정의 손 접촉이 100%였다는 의미가 아니다.

V3 전환에서는 자세·제어·gain·모델·충돌 정책·의자를 바꾸지 않았다. Spine/Torso의 source 방향 평면 허용치를 1mm에서 2mm로 완화하고 1–2mm를 경고로 분리했다. 이전 1mm 기준에서 repeat/free_strike/regrasp가 각각 약 1.056287/1.048944/1.051203mm로 실패한 기록은 보존했다. 이 지표는 실제 PhysX 침투 깊이가 아니다.

## 장점과 남은 검증

현재 후보의 장점은 하체 유한 제어와 양발 접지를 유지하면서, 왼손·왼팔 접촉을 해제한 15초 동안 기타 지지와 타현을 각각 검증했다는 점이다. 실제 영상의 주요 프레임에서도 왼손의 이탈·복귀와 준비 자세의 유지를 확인할 수 있다. 접촉·하중·정밀 현 통과의 판정은 영상 외관이 아니라 원래 측정 결과를 따른다.

남은 검증은 다음과 같다.

1. 재접촉 후에도 왼손 하중에 의존하지 않는다는 직접 검증.
2. 전체 83초 동작의 같은 실행 내 연속 수행과 동일 조건 재시작 재현.
3. 관절 상태·목표·drive/limit 내부 좌표, 보고 속도와 자세 차분의 차이 원인 규명. 건강 예산은 통과했지만 엄밀 EPS0와 solver 원인 확정은 False다.
4. 실제 압현·타현 힘, 현 진동과 음향. 현재 타현 성공은 기하 검증이다.
5. 후속으로 미룬 추가 55형상 정밀 감사.

새 PPO, Root 자유 균형·보행, 사람 동작과의 유사성은 이 결과에서 검증하지 않았다. 미검증 gain 변경이나 척추 point 제어 제안을 채택한 결과도 아니다.

## 보존 방식

이 폴더의 작은 입력 파일과 이미지는 원본과 동일한 사본이고, `videos`는 기존 원본 MP4를 가리키는 상대 심볼릭 링크다. 실험 원본과 과거 자료는 [archive](/home/ajou/yigyu/3/paper/initial_pose/archive/README.md)에 모았다. 최신 설정이 참조하는 `lower_body_release_v1` 경로는 호환 링크로 유지하므로 기존 설정과 영상 연결은 그대로 동작한다. 설정 파일 내부의 절대 경로도 유지했으므로 이 폴더만 다른 컴퓨터로 복사해 실행할 수 있는 독립 패키지는 아니다. 이동 사항은 [경로 대응표](/home/ajou/yigyu/3/paper/initial_pose/archive/reorganization_20261017/PATH_MAP.json)와 [정리 검증](/home/ajou/yigyu/3/paper/initial_pose/archive/reorganization_20261017/VERIFICATION.json)에 기록했다.
