# guitar_learning 구조 정리

2026-10-19. 사용자가 파일 역할 분석에서 권장한 순서의 정리를 승인했다. 기존 물리·관측·행동·보상·PPO·checkpoint 검증을 유지하며 코드 정리와 원자료 보존을 함께 수행한다.

1. [x] 실행 중인 native 작업과 작업 규칙을 확인하고 전체 CPU 검사 기준선을 기록한다. 변경 전 활성 소스·문서·설정·검사와 원래 경로/SHA를 보관한다.
2. [x] README/README_CURRENT/AGENTS/CODE_LINEAGE와 보관 색인을 정비하고 깨진 원구현 연결을 수정한다. 활성 캐시만 제거하며 기존 snapshot은 보존한다.
3. [x] runtime V1, 대체된 감사/평가 CLI, anchored 실험과 독립 curriculum을 관련 검사와 함께 보관한다. 현행 import와 안내에서 제거하고 과거 입력 SHA의 원문은 계속 검증 가능하게 한다.
4. [x] 재사용되는 의존성 판별·렌더 도우미·악보 compiler 공통부를 분리한다. 이동 가능한 진단 도구는 tool로 옮기고 현행 참조·경로 계산·입력 pin을 갱신한다. 공통 runner의 전체 재설계나 물리·보상 변경은 하지 않는다.
5. [x] 문법·CPU 회귀·입력/자산 SHA·보관 SHA·활성 import·문서 링크를 확인하고 독립 change-reviewer의 지적을 반영한다. 필요한 최소 native 연결 검증으로 현재 실행 가능성을 확인한다.

성공 조건: 활성 코드에서 archive import 없음, native/CAS 자산 보존, 보관 원문 SHA 일치, 이전 단계 및 현행 gate의 검증을 완화하지 않음, 정리 전후 동일 입력의 도구/관측/보상/제어 의미 유지, 문서가 현행 진입점과 보관 범위를 설명함. 여러 실행기가 공통으로 사용하는 song/transition/native/기본 환경/PPO는 통째로 보관하지 않는다. 기존 실행 결과는 덮어쓰지 않는다.

변경 기록과 검증은 docs/2026-10-19/guitar_learning_structure_cleanup_v1/에 남긴다.

기준선: 변경 전717개 검사 중716통과·1실패. 보상V2 runner 검사는 내부화된 물리 입력이 정확히 pin됐는데도 옛 경로가 pin에 남기를 요구했다. 단독 재현·경로 차이 진단을 남겼으며 생산 코드는 유지하고 검사 기대값을 현재 경로와 정확한 SHA 대조로 보완한다. 변경 전 native12스텝도 저장했다. 활성 캐시769개/6,597,476bytes 제거. 원문449개는 snapshot과 historical CAS에 정확한 원래 경로/SHA로 등록했다.

실행기/실험/관련 검사28파일(24Python)을 원문·inode 그대로 보관했다. 도구6개와 렌더helper를 tool에 두고 공통 의존성 판별은 기존recording 함수를 직접 재사용한다. score는 바이트 그대로 유지하고 tool이 공통14정의를 import해628줄을 제거했다. 초기 회귀에서 보관한 검사fixture를 현행joint/local 검사들이 재사용하던 참조를 발견해 quality_fixtures.py로 분리했다. 별도 임시 작업 공간에서 복원한 원fixture와 새fixture의 좌/우563계약이 정확히 같고 해당17개 검사가 통과했다. 초기 회귀 실패·중단과 fixture 대조 원자료는 보존한다. 최종 활성373Python 소스를 다시 고정하고 import 오류0을 확인한 뒤 전체 회귀를 재실행했다.

완료: 고정된373소스에서 최종680개 검사 모두 통과(635.948초). native12스텝 전후 JSON 모든 필드가 정확히 같고, 도구/계획 결과도 원형과 같다. 백업449·보관28·native190·tool18 파일 SHA와 CAS2,105객체를 검증했다. 기존 historical 버전/default 보존, 누락/미참조0, 활성 캐시0, 활성 안내 링크 오류0이다. 검수의 tool README SHA 지적을 수정하고 fixture 분리까지 재검수하여 남은 문제없음 판정을 받았다. [정리 결과](/home/ajou/yigyu/3/docs/2026-10-19/guitar_learning_structure_cleanup_v1/README.md) · [최종 검증](/home/ajou/yigyu/3/docs/2026-10-19/guitar_learning_structure_cleanup_v1/verification.json).
