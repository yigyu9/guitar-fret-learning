# Tab2Body — 자유 기타 연주 제어 연구

오디오에서 구성한 연주 목표를 휴머노이드와 자유 기타의 물리적 상호작용으로 실행하는 연구다. 논문 작업 제목은 **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**다.

현재 기본은 GPU 왼손 finger-skill v3의 J33 공동 학습이다. 손가락은 목표각 직접 지정(position)을 사용하고 v9 초기 자세에서 시작한다. 기타는 자유 강체·중력 ON·스트랩 OFF이며 Root 고정과 하체 유한 제어를 사용한다. 현재 연구는 지정 손가락의 압현을 학습·평가하는 단계이며 곡 연주 성공을 선언하지 않는다.

| 필요한 정보 | 대표 문서 |
| --- | --- |
| 지금 진행하는 작업과 확인된 결과 | [현재 상태](CURRENT_STATUS.md) |
| 학습 실행·재개·평가·영상 | [학습 안내](guitar_learning/README.md) |
| 학습 코드 읽기 | [코드 해설](docs/2026-11-02/코드해설/README.md) |
| 보상과 조기 종료 | [현재 보상 구조](docs/2026-10-26/왼손보상구조/README.md) |
| 다른 PC·SSHFS 설치와 실행 | [이식성 안내](docs/PORTABILITY.md) |
| 현재 압현 실험 | [실험 안내](docs/2026-11-02/압현성공/README.md) |
| 오디오·운지 전처리 | [전처리 안내](tab2fingermapping/README.md) · [설치](tab2fingermapping/SETUP.md) |
| 논문과 근거 | [논문 안내](paper/README.md) · [근거 색인](paper/evidence_index.md) |
| 나머지 문서·과거 실험 | [문서 색인](docs/DOCUMENT_INDEX.md) |

물리 학습에는 Isaac Gym Preview4를 사용할 수 있는 Python 환경이 필요하다. 프로젝트 루트에서 [로컬 실행기](scripts/README.md)를 준비하고 학습 안내의 명령을 실행한다. 현재 실행 설정과 수치는 위 대표 문서를 기준으로 읽고, 날짜별 실험 기록의 과거 명령·성능을 현행 구현에 그대로 적용하지 않는다.
