# 직립 지지 자세 실행 결과 체크리스트

## 완료

- [x] 인계 및 원본105/97/명목0축8·Root/기타조건 확인, 기존 성공·실패 자료 보존
- [x] 새 자세와 유한 제어를 버전별 계산·실행하고 실제 첫step 이후 관측 기록
- [x] source14 전체 초기 형상·원범위·손 도달 검사
- [x] 몸통 목표·상태·실제native좌표를 240Hz FK로 대조
- [x] 정지5초: Chest/Torso total5°/옆3° 및 Chest/오른상완 실제 동시 접촉 통과
- [x] 새해제코드의정지재현 확인: V16/V17 전체 물리/명령행 exact
- [x] 왼손15초시험을시도하고두실패와첫목표전환원인을보존
- [x] 독립 change-reviewer 검수 및 영상/상세 실패 인계

## 미완료

- [ ] 왼손 완전 해제와5초 후 무접촉
- [ ] Chest/오른상완·허벅지만으로15초 동적 지지
- [ ] 자유 기타 연주·다중조건/외란 평가

현재 판정: **정지 자세 후보 검증 완료, 최종 전신/해제 자세 채택 보류.** 단순히gain을높이거나작은외부PD제안을정답으로채택하지않는다. 후속은손가락변경/팔목표전환/실제이격방향과왼손하중제거를분리한작은시험이다. 새PPO학습은진행하지않는다.

상세 결과·원자료·재현 진입점은 [최종 설명](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/README.md), [영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/media_index.md)을 따른다. 이전의모든leaf계획은실행입력으로봉인돼수정하지않았으며이결과파일이완료/미완료체크상태를갱신한다.
