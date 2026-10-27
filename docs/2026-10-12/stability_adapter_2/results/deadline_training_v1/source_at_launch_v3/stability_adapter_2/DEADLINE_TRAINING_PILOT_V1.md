# 정오 마감 시험 학습 — 2026-10-12

사용자 승인: 한국시간 정오12시 마감, 등록된 Fret035000/Strike010000,30분 간격 checkpoint와 평가 영상. 별도 승인 없이 필요한 결정을 진행한다는 기존 지시를 적용한다. 이전 구현·실험·메인 계획서는 보존한다.

## 범위와 중요한 결정

- GPU 드라이버580.178.04/RTX4070Ti12GB는 정상이다. 격리 실행에서는 장치가 숨겨지며 GPU 접근 실행에서 PyTorch CUDA와 독립 Isaac GPU PhysX가 실제 통과했다. 사용자 재설치/재부팅은 필요 없다.
- 기존 LearningScene은 CPU PhysX scalar API로 검증됐다. 이번 마감 경로는 **CPU PhysX 유지 + CUDA 정책/최적화**다. GPU PhysX vector환경으로 전환하면 scalar native snapshot/접촉/초기화 계약도 바뀌므로 이번 실험에 섞지 않는다.
- 자유 기타, 스트랩OFF, root/하체 물리 고정, self-collision, 동일 초기q/p/q/PD. 몸통9관절 초기±5°와 기존 rate/bounds를 유지한다. 상체81 출력, Actor/Critic 각각512→256. 기타/손 상태를 덮어쓰거나 인위적인 기타 지지 힘을 주지 않는다.
- 두 원본 baseline은 동결하고 실제로 관측→목표를 요청한다. 하나의 owner가 명목 목표와 학습 정책의 bounded absolute-anchor 보정을 합친 최종81 목표를 제출한다. 동적 anchor는 현재 baseline 요청이며 준비2초의 anchor는 검증된 preload1.0이다. 관측739에 명목81 목표를 추가한820D 새 ABI다.
- 이번은 **deadline_pilot_v1**, 정식 rewardv4/v5 학습 준비 완료가 아니다. 미인증항목을 0으로 위장하거나 기존 require_native_training_ready를 해제하지 않는다. SO(3) membership은 정확히 검사하되 밖의 거리에는 인증되지 않은 feasible upper/lower proxy를 기록한다.
- 시험 보상은 실제 허용 위치/회전 이탈, 실제 sounding fret, 현재 기타 기준 손가락 접근/피크 접근, 공동 실제 crossing/event, 실제 몸통 변화·최종 목표 변화율을 사용한다. 미세 떨림/범위 내부 초기점 복귀 비용은 없다. 가상 압현·가상 crossing 점수를 만들지 않는다. gaze/완전 distal-pad/유지dropout/치명정산 전체계약은 후속이며 시험 성공과 정식연주 성공을 구분한다.
- 고정 score horizon(준비2초+곡 전체)을 유지한다. source Fret의 이전 손목실패를 공동 물리종료로 복제하지 않는다. 측정/API/비유한값/금지호출/고정하체 변화는 실행오류로 중단하고 부분 결과를 보존한다. 조기 physical fatal의 할인 정산이 닫히지 않았으므로 이번 학습은 유한상태의 고정 horizon 시험만 대상으로 한다.

## 계획 → 구현 → 검증 → 검토

1. [x] baseline 경로/입력 계약, 마감·간격, GPU 재확인.
2. [x] SO(3) CPU 포함/특이점/거리상하한 반례 검증. v1/v2 실패 보존, v3사용.
3. [ ] 새 native 연결/명시적 시험 reward, CUDA PPO/RNG checkpoint 구현. 새 파일만 사용.
4. [ ] CPU 반례·독립 코드 검수·짧은 native/PPO 실제 갱신 검증.
5. [ ] 시작 전 전체영상, 실제 학습 실행,30분마다 checkpoint 평가 전체영상. 마지막 평가 시간을 확보하도록11:40학습 종료 예약.
6. [ ] 원시 로그·초기값·실제 Isaac 이미지/전체·손 영상과 한글 설명을 docs 아래 새 phase에 보존. 실패도 보존. 메인 기록은 native 입력 closure가 읽고 있지 않을 때 추가.

## 출력

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/`

실행 소스/leaf 입력은 소비 후 수정하지 않는다. 재시도는 새 버전/새 경로, 기존 입력SHA와 보존목록을 대조한다. 현재 계획은 정책학습/음악 성공을 주장하지 않는다.
