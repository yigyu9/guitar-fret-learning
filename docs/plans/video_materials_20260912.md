# 2026-09-12 설명 자료용 영상 발굴·반영 계획

## 목표

저장소에 이미 있는 영상을 검토해 프로젝트 구조와 현재 검증 상태를 설명하는 데 실제로 도움이 되는 자료만 골라 `docs/2026-09-12/`에서 찾기 쉽게 연결한다.

## 범위와 가정

- 원본 영상은 이동·복사·재인코딩하지 않고, 원래 실험 경로를 문서에서 상대 링크로 참조한다.
- 영상만 보고 성능을 단정하지 않는다. 관련 report/metrics를 함께 확인하고 미완성·실패·제한 범위를 캡션에 표시한다.
- 새 시뮬레이션이나 학습은 실행하지 않는다.
- `current`와 `remembered`는 Strike 문서의 정의에 따라 카메라 이름으로 설명하고, 서로 다른 checkpoint 비교라고 쓰지 않는다.

## 조사 결과 및 우선 후보

프로젝트 전체에서 MP4/WebM/MOV/AVI/GIF 계열 286개를 찾았다. 반복 checkpoint 영상은 생략하고 다음 후보를 우선 검토했다.

| 주제 | 후보 | 확인한 근거와 설명 시 주의점 |
|---|---|---|
| Fret 왼손 | `fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/videos/fret_035500_rollout.mp4` | 최신 full-song deterministic 녹화. F1 0.212, sustain 성공 1/35. `goal_finished`는 시간축 완료이지 연주 성공이 아님을 함께 설명한다. |
| Strike 오른손 | `strike/training/runs/20260911_2235_02_Jazz1-200-B_solo/videos/strike_012000_full_song_{current,remembered}.mp4` | 선택된 best full-song 결과. 계획 event 42/42 완료, traversal F1 1.0, FP/FN·blocked/wrong crossing 0, timing abs p95 4.94 ms, grip 평가 통과. 단일 곡의 오른손 policy 평가이며 전체 전신 시스템 일반화의 증거는 아니다. |
| 하체 지지 | `lower_body/training/runs/20260908_physical_contact_final/videos/final_rollout.mp4` | 10초 rollout, 최대 자세 오차 4.29°, 평균 pose quality 0.972, 조기 reset 0. 하체 seated-pose 선행 검증이며 자유 기타 안정화 성공과는 구분한다. |
| Strap 비교 | `strap_sim/_output/simulation.mp4` | strap 없음/있음 물리 결과를 나란히 보여 주는 6초 비교 영상. 낙하 억제와 위치 drift 감소를 설명하되, 연주 자세·회전 유지에는 실패했다는 결과도 명시한다. |
| Strap 렌더링 | `strap_sim/_output/isaacgym_multiview.mp4` | Isaac Gym RGB 네 시점 녹화. 물리 경로를 depth-aware로 겹쳐 보인 것이며 strap 자체가 collision mesh라는 뜻은 아니다. |
| G0 결합 | `docs/2026-09-07/synchronizer/synchronizer_dual_hand_preview_incomplete.mp4` | 파일 자체가 incomplete preview로 표시한다. 구조를 상상하는 보조 그림으로만 쓰고 실제 one-simulator 물리 통합의 증거로 제시하지 않는다. |
| 자유 기타 복귀 | `stability_adapter/02_world_recovery/output/settle_then_recover_v2.mp4` | WAIT→RECOVER 전환을 보여 주는 pilot 진단. report상 복귀 성공 0회이므로 성공 사례가 아니라 현재 검증 경계 설명에만 쓴다. |

## 반영 단계

- [x] 저장소 안내와 날짜별 설명 문서를 읽고 영상 파일을 전수 검색한다.
- [x] 대표 후보의 화면, 길이·해상도, 관련 JSON/결과 문서를 대조한다.
- [ ] `docs/2026-09-12/09_영상_자료_가이드.md`에 용도·관찰 포인트·근거·주의점을 정리한다.
- [ ] 목차와 Fret/Strike/G0/안정화 설명에서 필요한 위치에 영상 가이드를 연결한다.
- [ ] 모든 상대 링크와 수치 근거를 검수하고 용어·차원 계약(105 slots / 97 movable DOF)을 보존한다.

## 완료 기준

- 각 추천 영상의 링크가 실제 파일을 가리킨다.
- 각 영상이 무엇을 설명하는지, 무엇을 입증하지는 않는지 독자가 알 수 있다.
- 주요 장별 문서에서 해당 영상 가이드로 쉽게 이동할 수 있다.
- 영상 원본과 실험 산출물은 변경되지 않는다.
