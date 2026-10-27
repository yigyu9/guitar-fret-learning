# upright 몸통·오른 근위팔 감싸기 사전 검수 V1

요약 판정: **문제없음**. 현재 수정본 기준 **Critical: 0 / Warning: 0 / Suggestion: 0**. CPU Source 탐색으로 진행 가능하다. 계획·검색·새 Chest 기록 runner·새 분석기만 검수했으며 source/native 실행은 수행하지 않았다.

## Critical / Warning / Suggestion

현재 미해결 항목 없음. 검수 중 지적한 고정 Chest 상수 잔차와 새 wrapper의 기존 native setup patch 누락은 미실행 코드에서 root가 수정했고 재확인했다. 원본 consumed 파일은 수정하지 않았다.

## 확인 근거

- [search_right_arm_wrap_upright_v1.py:62](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v1.py:62): 최신 `native_add8_static`의 실제 초기값과 source q/name이 exact하다. baseline Chest proxy53.412322814°에서 world human 오른 수평축 양의 회전12/20/24°는41.412322814/33.412322814/29.412322814°로 감소하는 올바른 부호다. Torso/Spine/Chest 누적 .65/.85/1과 body±.25/양팔±.6/head±.5rad 모델 교집합이 계획과 같다.
- [search_right_arm_wrap_upright_v1.py:82](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v1.py:82): body9 fit 후 body를 고정하고 right12만 맞춘다. Thorax/근위 상완0.8mm 선호가 복원됐고 elbow 현재 origin은400의 부드러운 선호다. 최적화에서 상수였던 Chest query/잔차는 제거됐으며 최종 Chest30mm gate는 유지된다.
- [search_right_arm_wrap_upright_v1.py:114](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v1.py:114): Chest≥30mm·Thorax/근위0~30% 상완0.05~4mm·두 witness G_X<−.05m·전완>12mm·full source clear·waist·natural elbow·head/왼손목·finger42·joint limits와±5° elbow 여유를 검사한다. 현재 기타 회전에서 G−X의 world 수직 성분은+0.996132이므로 고정 G_X 음수 영역은 기타 위쪽 영역이라는 좌표 정의와 부합한다. 이 좌표/간격 조건을 actual 끼움이나 해부학적 겨드랑이 인증으로 확대하지 않는 계획도 적절하다.
- [search_right_arm_wrap_upright_v1.py:26](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v1.py:26): 발견 전 anchor/guitar XML SHA, 전체 pin 후 contract/FK/형상 구축, 종료 재검사는 유지된다. 고유755개 입력 경로가 존재하고 human37개·guitar XML69개·XML/manifest union70개 mesh와 새 runner/분석기 Python이 포함된다. fixed G/root·하체/finger42/형상·질량 조건은 유지하고 수락 config는 기존 finite controller/PD/cap을 승계한다. 후보는3개·정지 amplitude0이며 선택1개 파동은 별도 후속 설정이다.
- [run_right_arm_wrap_upright_v1.py:30](/home/ajou/yigyu/3/stability_adapter_2/run_right_arm_wrap_upright_v1.py:30): 수정본은 원래 runner의 `__main__` 전용 factory/ArmEffortGuard/LearningScene 생성/녹화4개 patch를 동일하게 적용한 뒤 ChestRecording만 추가한다. 기존33EFFORT+48POSITION setup이 import한 `runner.main()` 호출에서도 연결된다. 새 callback은 기존 after_physics를 먼저 실행하고 Chest–guitar endpoint raw만 추가하며 native state 전후 exact를 확인한다. 기존 runner SHA는 불변이다.
- [analyze_right_arm_wrap_upright_v1.py:28](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_upright_v1.py:28): original waist/직전 upright와 actual initial/final/report·1200 endpoint raw·self/helper를 before/after pin한다. 실제 이름 순서·완료·G39 허용차를 확인하고 proxy/parent-relative/G39 및 Chest presence/positive raw lambda를 분리한다. missing Chest field를0으로 대체하지 않고 필수 필드로 요구한다. raw lambda를 힘N으로 해석하지 않는다.

## 검증과 제한

검색/runner/분석기 AST 통과. 기존 native setup4개 patch의 표현과 적용 대상이 원본과 같음을 대조했다. 검수 시 새 phase에 source/native 출력은 없었다. 실제 fitting 수렴·전체 형상 수락·cooked 접촉·정지5초·선택 파동은 후속 단계에서 검증한다. 기존 실제 Thorax/상완 finite task를 바꾼 구현으로 해석하지 않는다.

검수 SHA256:

- Plan: `bf8c1d274d990e1d2078d0364d24c25e33085a8e59a37939329f63ec83f18f88`
- Source: `164945ef095c695e099e54d9713aa4b5c95e6653033360343de46e018751a9e0`
- 새 runner: `0cd511087ba0db3bb64fea9c9a5be605474dda2cce57753a7afcb5cb2358fc0a`
- 새 분석기: `7ca656055697469e3b8945e3a2f5b5a7f498d46c1194e52a673d5ee4b89e7600`
- 원본 runner: `420f8fffd4b9d87087c2fe2d6019485e5d34bb5d52b929d60bec0bc74525ad72`

지정된 이 검수 기록만 생성했다. 다른 담당자의 파일은 수정하거나 되돌리지 않았다.
