# 원래 연구 복구 검수

요약 판정: **문제없음**.

검수 범위는 recovery의 복원 소스·입력, namespace 실행, 재개/진행 추적 도구다. 현재 학습 코드의 별도 변경은 검수·수정하지 않았다. 초기 검수에서 발견한 실행환경 오류 및 도구 봉인·전체 입력 검사·재시도 재사용 항목은 최종 검수에서 해소됐다.

## 확인한 근거

- 원래 봉인된 Python 287개를 복원 사본과 독립적으로 SHA256 대조했으며 모두 일치했다.
- 완료된 baseline_s7, lr_s7, exploration_s7, separate_s7의 입력 봉인 각각 432개를 namespace의 실제 사본 매핑으로 대조했으며 모두 일치했다.
- 재구성한 ppo.py SHA256은 원래 봉인의 `8d9296072f1f048b5d4e566894b1564fcf2713051de5b131858ef1f62f31ebb6`와 일치한다.
- 기본 학습 패키지를 호스트에서 덮어쓰지 않고 연구 프로세스에서만 원래 절대 경로로 사본을 마운트한다. 기존 입력·체크포인트 검증을 완화하지 않았다.
- 실패한 preparation 실행의 체크포인트를 이어받지 않고 새 폴더에서 200업데이트를 다시 수행하며 완료 네 조건은 보존한다. 완료된 `_r2` 등 재시도도 재사용한다.
- resume_study.py의 check_sources가 각 명령 전후에 네 완료 조건의 전체 입력 432개와 활성 Python 집합·SHA를 검사한다. 읽기전용 bind가 호스트 수정을 막지 못하는 한계를 이 검사로 감지한다.
- 신규 복구 파일 5개 봉인을 독립 SHA 대조해 모두 일치했다. 원래 두 연구 도구 봉인 검사도 유지한다.
- check_frozen.py, progress.py, resume_study.py 문법 파싱을 통과했다.
- progress.py는 20초 주기로 현재 조건, 학습 업데이트 상태, 완료 개수, 8개 1차 및 최대 11개 조건의 조건부 ETA를 기록한다. ETA는 결과에 따른 선택 조건과 처리속도에 의존한다.

## 실제 GPU 재평가

`gpu_baseline_evaluation_verified/report.json`을 독립 확인했다.

- 원래 baseline 체크포인트의 엄격한 재로드와 GPU 전곡 4환경 평가 완료.
- `completed=true`, `episodes=4`, `failure=null`.
- `changed_inputs=[]`, `missing_import_pins=[]`, `cleanup_errors=[]`.
- `lifecycle_verified=true`, scene `closed=true`.
- 장치 `cuda:0`, PhysX GPU와 GPU pipeline 활성, DOF/root/body/contact/jacobian/force tensor 모두 CUDA.
- 4환경 모두 timeline 완료, 물리/손목 실패 0. 평균 달성 8.25/67은 복구 작동 확인용 소규모 평가이며 원래 128환경 성과를 대체하지 않는다.
- 보고서 SHA256: `93ca146e0cd873bbb2ad31b5420b409ba1f3b2da42a60013b2cda42274abd0b2`.

초기 v1~v5의 namespace 장치 노출, 읽기전용 확장 캐시, locale 오류 로그는 보존됐다. /proc·/sys·/dev 노출, 연구용 쓰기 가능한 확장 캐시, UTF-8 실행 환경으로 해결했으며 Python 학습 소스·입력 봉인은 바꾸지 않았다.

## Critical / Warning / Suggestion

현재 변경 범위에서 남은 지적 사항 없음.

복구 및 짧은 평가의 정상 동작을 확인한 판정이다. 남은 조건의 연구 결과, 1024환경 장시간 실행 안정성, 학습 성능 향상은 실제 후속 실행과 분석으로 확인해야 한다. 이 검수에서 별도 GPU 실행은 중복 수행하지 않았고 루트 작업이 생성한 실제 GPU 보고서와 입력 근거를 확인했다.
