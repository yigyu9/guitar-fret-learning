# GPU 왼손 손목 영역 보상 v9 구현·검증

2026-10-23. 합의한 넓은 손목 영역을 실제 GPU 왼손 학습에 적용했다. 이번 실행은 연결·저장·재개 검증이며, 장기 학습이나 연주 성능 개선을 확인한 결과는 아니다.

## 적용 내용

| 방향 | 기준 | 허용 범위 |
|---|---|---|
| 넥 길이 Gy | 악보 `allowed_fret_range` 양끝 셀의 실제 경계 중점 | ±6cm |
| 높이 Gx | anchor 프렛 셀 중심의 실제 넥 아래 테두리 | 아래로1~8cm |
| 깊이 Gz | 지판 압현면 | 연주자 쪽 뒤로2~11cm |

영역은 기타 로컬 좌표에 있으며 기타와 함께 움직인다. 지판면과 아래 테두리는 pin을 검증한 실제 넥 source hull에서 구하고, 원곡60Hz 작업 범위로 만든 경계를 물리 표본 시각에 선형 보간한다. 정책 준비3초를 차감한 곡 시각을 쓰며 트랙 시작 전/끝 뒤에는 양끝 범위를 유지한다.

영역 안·경계에서는 위치 패널티0이다. 밖에서는 `e=clamp(wrist,lower,upper)-wrist`, `q=sum((e/[.02,.03,.03])²)`, `rate=-q/(1+q)`를 계산하고 매240Hz 표본에서 `rate/240`을 누적한다. 단계별 계수0.2/0.1/0.05는 유지한다. 준비3초·음 사이·곡 말미에도 적용하며 기존 음 준비창 gate를 제거했다. 손목 항은 안전 cost가 아니라 기존 `song_wrist_position` reward에 음수로 기록된다.

정책의 위치 안내는 최근접 영역점까지의 벡터이며 영역 안에서는0이다. 회전 안내3열은0이고 `ready`는 회전 조건 없이 영역 안인지로 결정한다. 초기 손목 위치나 회전을 따라가게 하지 않는다. 관측544·priority8·손가락별 Actor·3331 커리큘럼 이력·손가락 움직임 비용0·PPO 설정·접촉/성공 판정·물리 안전과 CPU 왼손/오른손 경로를 유지했다.

현재 보상 계약은 `guitar_learning.gpu_tensor_song_reward.v9`다. v8 이하 checkpoint의 strict resume는 거부하며 새 학습으로 시작한다. 같은 v9라도 전체 입력/보상/제어/정책 계약이 같아야 재개한다. 전체 허용 부피의 자연스러운 압현 자세·손가락 도달성은 아직 검증하지 않았다.

## 검증 결과

- 관련 CPU19모듈 **174개 검사 통과**. 경계·6방향 이탈·전후 시간 clamp·보간·프리롤 감점·회전 자유·기타 프레임·부분reset·실제 관측·v8거부·v9복구를 포함한다. 메타데이터 설명을 최종 정합하게 한 뒤 관련35개를 재검사했다.
- 독립 change-reviewer가 코드·수식·버전 분기와 보관 원문23개의 SHA를 확인했다.
- 별도 확장 검사 `test_left_curriculum_runtime`는7개 중6개 통과,1개 실패다. `test_left512_rejects_legacy500_before_mutation_and_right500_stays_compatible`이 기본GPU의544를 과거512로 기대하는 기존 불일치다. 변경 전에도 이미544였으며 이 작업에서 그 검사는 수정하지 않았다. [원문 로그](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_wrist_region_v1/legacy_left_curriculum_runtime.log).

최종 소스의 실제 GPU 검증은 RTX4070Ti, **large·1024환경·H32·seed7**로 실행했다.

| 실행 | PPO 업데이트 | 반영 전이 | 정상 종료 | 원시 기록 CRC/EOF |
|---|---:|---:|---|---:|
| `gpu_fresh_final` | 새2회 |65,536|통과|64행 통과|
| `gpu_resume_final` | 누적2→3회 |32,768|통과|32행 통과|

모델·Actor Adam·Value Adam·3331이력·업데이트 수·cost weight·Python/NumPy/Torch/CUDA RNG가 fresh 최종과 resume 초기에서 정확히 일치했다. 모델과 두 optimizer의 tensor는 모두 유한하며 각각586/587개 입력SHA가 유지됐다. 물리·CUDA pipeline·자원 해제와 로그 정상 close도 확인했다. 최저 관측 GPU 여유는 fresh 약6.57GiB, resume 약6.68GiB다.

GPU 로그의 단계0 손목 reward 평균은 업데이트별 -0.0014903 / -0.0015098, 재개에서는 -0.0014339/전이다. 정책 준비 구간에서도 영역 밖 감점이 실제 반영된 것이다. 음별 성과를 평가하기 전의 짧은 실행으로, 완료된 곡은0개다. 재개 시에는 PPO 상태를 복원하고 물리·곡은 합의한 초기 자세로 새로 시작한다.

처음 빌드 도구 Ninja가 PATH에 없어 시작하지 못한 시도(`gpu_fresh`)와, 단계 가중치 적용 범위의 메타데이터 설명을 고치기 전 짧은 실행(`gpu_fresh_retry`,2회)은 별도로 보존했다. 후자의441개 소스는 `gpu_fresh_retry_sources`와 SHA 목록에 보관했다. 위 표의 최종 검증 전이에는 이 두 시도를 합산하지 않았다. native 로그의 기존 시각 mesh 로드 경고는 남아 있으며 이번 검증은 영상 렌더 검증이 아니다.

## 실행과 코드

새 학습 명령·흐름은 [현행 학습 안내](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md), 상세 수식은 [손목 보상 설명](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/03_접근접촉유지보상.md:30)을 따른다. 기존 v8 checkpoint를 이 실행의 재개 입력으로 사용하지 않는다.

- [영역 로드·기하·GPU 측정](/home/ajou/yigyu/3/guitar_learning/gpu/wrist_region.py)
- [환경·관측·보상 통합](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py)
- [정책 버전 분기](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py)
- [단계 상태 연결](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py)
- [검증 수치](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_wrist_region_v1/verification.json)

변경 전 원문은 [archive manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261023_before_wrist_region_v1/manifest.json)에 보존했다. 기존 v8 장기 실행의 동결438소스와 시각화 봉인 자료는 그대로 유지했다. 현행 소스를 과거438소스와 같다고 주장하지 않는다.
