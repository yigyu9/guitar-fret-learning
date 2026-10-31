# v9 초기 자세의 손가락별 압현 실험

## 현재 진행: 실제 PPO 단일음 학습

기존 기하 후보 재생과 별개로, 실제 J33 학습 환경에서 가상 단일음 16개를 각각 새 정책으로 학습 중이다. 각 목표는 large·64환경·H32·100회이며 보상·물리·제어·종료 조건을 유지한다. 목표는 준비 3초 후 2.5초 동안 지정 손가락·줄·프렛을 누르는 것이며, 기존 연속 clean 1초 기준으로 달성을 판정한다.

- [실시간 진행](process/learning/progress.md): 실행 단계와 완료한 목표 수
- [평가 수치](analysis/learning/summary.json): 목표마다 초기·최종 모델의 동일 16환경 평가가 끝나면 누적 기록
- [실행·목표·원본 고정 정보](process/learning/run_manifest.json)
- 학습 영상: `video/learning/`, 과정과 로그: `process/learning/`, 최종 해설: `analysis/learning/RESULTS.md`에 자동 저장

아래는 앞서 완료한 기하 후보 재생 검사다. 아래 성공 5/16은 실제 PPO 학습 성과가 아니다.

## 앞선 기하 후보 재생 검사


기존 줄·프렛 압현 실험249파일(약1.03GiB)을 제거하고 새로 검사했다. 초기자세 개발 자료는 initial_pose/로 모아 보존했다. 새초기자세에서16목표를 자유기타3조건×2회, 총96개실행으로 확인했다.

반복 검증 성공은 **5/16개 목표**다. 검지1/4, 중지0/4, 약지0/4, 소지4/4다. 기본제어와관절오차보정은3/16, 실시간손목보정은5/16이며 물리안전실패는96개실행중0건이었다.

[결과 해석과 다음 검사 제안](analysis/INTERPRETATION.md) · [전체96개 결과](analysis/RESULTS.md) · [원목표16개](TARGETS.md) · [수치CSV](analysis/analysis.csv)

성공 영상에서도 활성손가락의 실제 굽힘 변화는 작고 팔·손목 이동 비중이 컸다. 이번5개를 자연스러운 손가락 능동압현의 성공으로 해석하지 않는다. 구체 수치는 결과 해석에 기록했다.

![손가락별 반복 성공](analysis/finger_summary.png)

| 반복 성공 목표 | 연속 접촉 | 손 확대 영상 | 전신 영상 |
|---|---:|---|---|
| 검지 3줄·4프렛 | 6.733초 | [손 확대](video/free_open/index_s3_f4_hand.mp4) | [전신](video/free_open/index_s3_f4_full.mp4) |
| 소지 3줄·9프렛 | 6.654초 | [손 확대](video/free_open/pinky_s3_f9_hand.mp4) | [전신](video/free_open/pinky_s3_f9_full.mp4) |
| 소지 2줄·10프렛 | 6.912초 | [손 확대](video/free_open/pinky_s2_f10_hand.mp4) | [전신](video/free_open/pinky_s2_f10_full.mp4) |
| 소지 4줄·11프렛 | 6.421초 | [손 확대](video/free_live/pinky_s4_f11_hand.mp4) | [전신](video/free_live/pinky_s4_f11_full.mp4) |
| 소지 4줄·12프렛 | 5.750초 | [손 확대](video/free_live/pinky_s4_f12_hand.mp4) | [전신](video/free_live/pinky_s4_f12_full.mp4) |

| 디렉토리 | 저장 내용 |
|---|---|
| video/ | 성공 목표의 손 확대·전신 MP410개만 |
| analysis/ | 해석·전체 결과·CSV·JSON·그래프 |
| process/ | 실행 도구·기하 후보·물리 기록·로그·렌더 증거·캐시·검수 |
| initial_pose/ | 초기 자세 개발·적용 기록 |

[초기 자세 자료](initial_pose/README.md) · [실험 상태](process/status.json) · [삭제·이동 목록](process/cleanup.json) · [독립 검수](process/final_result_review.json) · [영상 검사](process/media_qa.json)

성공 기준은 두 독립 실행 모두 유효패드 기하·방향·distal순접촉합력≥0.01N·오압현 제외를 만족하는 연속100ms와 물리실패 없음이다. 접촉쌍·실제줄압력·음향성공은인증하지않으며 곡시계의손목안내/J종료는이번정적진단에적용하지않았다. 정책의 곡 수행 성공과 구분한다.
