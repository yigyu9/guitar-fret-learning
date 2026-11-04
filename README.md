# Tab2Body — 자유 기타 연주 제어 연구

오디오에서 구성한 연주 목표를 휴머노이드와 자유 기타의 물리적 상호작용으로 실행하는 연구다. 논문 작업 제목은 **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**다.

새 압현 학습의 기준은 **V5**다. 상태464차원, 목표26차원×8슬롯을 독립 상태·목표 인코더에 넣고, 33축 Actor와 별도 보상·비용 Critic을 PPO로 학습한다. 손가락은 목표각 직접 지정 방식을 사용한다. 자유 기타·중력 ON·스트랩 OFF, v9 초기 자세·root 고정·유한 지지 제어를 유지한다.

| 필요한 정보 | 대표 문서 |
| --- | --- |
| 현재 연구 상태 | [CURRENT_STATUS](CURRENT_STATUS.md) |
| 압현 학습·재개·평가·영상 | [V5 실행 안내](guitar_learning/README.md) |
| C1~C6 합성 목표 | [연속 목표 실행 안내](docs/2026-11-09/압현_v5_합성목표연결_v1/README.md) |
| 코드 읽는 순서·상세 설명 | [코드 지도](guitar_learning/docs/CODE_STRUCTURE.md) · [코드 해설](docs/2026-11-02/코드해설/README.md) |
| 학습 효율 분석 | [현재 V5 분석](docs/2026-11-09/압현_v5_학습효율분석_v1/README.md) |
| 타현27·전신37 | [타현27](guitar_learning/tool/experiments/right27/README.md) · [전신 학습](guitar_learning/docs/WHOLE_BODY_TRAINING.md) |
| 다른 PC와 입력 공유 | [이식성](docs/PORTABILITY.md) · [로컬 실행기](scripts/README.md) · [팀원 전달](docs/TEAM_HANDOFF.md) |
| 오디오·운지 전처리 | [tab2fingermapping](tab2fingermapping/README.md) |
| 논문·실험 근거 | [논문 안내](paper/README.md) · [근거 색인](paper/evidence_index.md) |
| 이전 압현 구조·정리 기록 | [간단한 이력](docs/history/press_before_v5.md) · [이번 정리](docs/maintenance/v5_project_cleanup_20261104/) |

## 디렉토리별 역할

| 위치 | 역할 |
| --- | --- |
| `guitar_learning/` | 압현 V5, 타현·전신 정책, 공용 물리·접촉·학습·도구 |
| `guitar_learning/assets/` | 프로젝트 내부 실행 입력과 필요한 출처 검증 자료 |
| `data/song_bundles/` | 실제 곡·합성 압현 목표 번들 |
| `data/diagnostic_inputs/` | 공유하는 진단 자료; 일반 학습 입력과 구분 |
| `scripts/`, `isaacgym/` | 로컬 실행기와 native 런타임 |
| `docs/` | 현재 문서, 실험 결과, 봉인된 실행과 역사 근거 |
| `tab2fingermapping/` | 오디오·운지 전처리 |
| `paper/` | 논문 원고·그림·주장 근거 |
| `.runtime/`, `runs/` | 로컬 캐시와 실행 출력 |

현재 안내는 V5를 기준으로 한다. 과거 구현·관측 차원·실험 명령은 당시 계약의 기록이다. 입력 SHA·checkpoint·봉인 runtime이 참조하는 원문과 자산은 보존하며, 오래됐다는 이유로 삭제하지 않는다.
