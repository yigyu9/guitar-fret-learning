# Tab2Body 이식성 작업 — 2026-10-29

사용자 승인 범위: 계획에 그치지 않고 수정 및 짧은 실행·저장·재개·평가를 수행한다. 기존 미커밋 직접 position 제어와 연구 조건을 유지한다.

- [x] README, CURRENT_STATUS, PROJECT_CONTEXT, guitar_learning/README와 현재 지침 확인
- [x] 초기 자세·native 자산·mesh·곡 번들 의존성 내부 완결, 원본 바이트/SHA 유지
- [x] 역사 식별자와 현행 파일 위치 분리, manifest와 resolver 이식
- [x] 새 checkpoint의 프로젝트 상대 식별자, strict identity와 이동 후 검증
- [x] Isaac Gym native 및 Torch 빌드의 PC 로컬 캐시·내용 검증 실행기
- [x] 다른 루트/다른 CWD CPU 검사, 필수 의존성·끊긴 링크 검사
- [ ] GPU 120step·소수 환경 학습·strict resume·별도 평가·가능시 영상
- [x] 독립 change-reviewer 검수, 문서/결과/제약 기록

작업 분담: native 입력/경로, checkpoint, 로컬 runtime을 독립 작업자로 진행하고 주 담당이 통합·검증·문서를 수행한다.

관찰: 시작 시 nvidia-smi가 NVIDIA driver 통신 실패를 반환했다. CUDA GPU 구동 가능 여부를 별도 확인하고, 실행 불가시 실제 검증 범위를 구분한다. 원시 과거 docs의 대량 링크는 보존하고 현행 필수 입력만 내부 사본으로 사용한다.

## 실제 완료·제약

- CPU125검사 통과. 실제 CPU 환경/정책/catalog/sampler의 루트 간 strict 복원과 변조 거부 포함.
- 외부 원래 트리 접근 금지 relocation 검증, 최종 복사본207입력 검사 통과.
- 로컬 Isaac Gym과 GymTorch 실제 빌드/import 통과.
- GPU probe와 최소 학습을 실제 시도했으나 이 PC의 NVIDIA 드라이버 부재/CUDA unavailable로 중단. GPU학습 저장본이 없어 GPU 재개·평가·영상은 선행조건 실패로 미실행이다. 해당 체크는 완료로 표시하지 않는다.
- 실제 SSHFS 마운트는 없어 원격 파일시스템 거부와 동시 캐시 생성만 검사했다.
- 상세 결과: docs/2026-10-29/portability_v1/README.md 및 summary.json.
