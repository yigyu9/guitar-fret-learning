# 검지→중지 전환 연구 독립 변경 검수

검수 대상은 이 로컬 연구의 `도구/runtime.py`, `reference_motion.py`, `finalize_geometry.py`, `reference_gpu.py`, `analyze.py`, `study.py`, 관련 CPU 검사와 `문서/PLAN.md`다. 별도 change-reviewer가 읽기 검수와 CPU 검사만 수행했다. 공유 원본, 다른 PC 학습, GPU·물리·정책 학습은 실행하거나 변경하지 않았다.

## 최종 판단

현재 확인한 범위에서 **기준군 시작 전에 반드시 수정해야 할 오류는 남아 있지 않다.** 이 판단은 실행·집계 계약의 검수 결과이며, 정책의 전환 성공이나 자연스러움에 대한 판정이 아니다. 이 문서는 생산 알고리즘이나 기본 실행 설정의 변경을 승인하지 않는다.

최종 독립 CPU 검사 7개가 1.308초에 모두 통과했다. 두 손가락의 head·활성 축·탐색 하한·확률 계산, E4 초기 목표와 미래 목표, 선택 reset, 진단 상태, 부분 기록 행, 최적화 실행 거부와 실제 CPU 자식 프로세스 회수가 포함된다.

보존 `source_snapshot.json`과 활성 `guitar_learning/**/*.py`를 대조한 결과, archive를 제외한 295개 파일의 변경과 누락은 없었다. 검수 중 생성한 파일은 이 보고서뿐이며 생산 코드는 수정하지 않았다.

## 확인한 구현 계약

- 활성 축은 팔 12개와 검지·중지 각 4개, 총 20개다. 두 finger head는 학습 가능하고 약지·소지 head는 동결되어 있다. 비활성 축은 표본화와 log probability·entropy·KL의 활성 마스크에서 제외된다.
- base/narrow/broad의 변경은 두 손가락 8축의 초기 표준편차와 하한이다. 팔 표준편차, mean·value 계산, 보상·초기 분포·물리 제어를 바꾸는 분기는 없다. base의 기존 forward 동일성 산출물은 연구 측 검증이며, 독립 검수에서는 현재 CPU 검사와 코드를 확인했다.
- 단계용 목표는 `TransitionEnvironment.selected_target()`에서 현행 `_focus(False)`를 사용한다. E4의 첫 음은 초기부터 관측되며, 단계 전환이 두 손가락의 행동을 잠그거나 음별 원장·손목 종료 상태·물리 상태를 초기화하지 않는다.
- CPU 초기 자세는 새 FK 및 현행 패드 입력으로 생성되고 catalog/provenance SHA를 확인한다. 과거 native 성공을 상속하지 않는다. 확인 시 4개 CPU 후보의 기하 유효성, 생성 입력 SHA, catalog/provenance 연결이 일치했다.
- 240Hz 진단은 두 distal 패드 표면 표본의 근접, 각 몸체의 native 합력 최대와 손가락 21축의 native 범위 1% 체류를 기록한다. 접촉 쌍이나 압력을 측정하지 않으며, 충돌 없음의 인증으로 사용하지 않는다.
- 분석은 최초 32/128환경별 첫 episode를 사용하고 실패를 분모에 포함한다. 연속 달성·누적 clean·전체 유지·정시 시작·이전 음 끝 유지·해제 proxy를 구분하고, 대상 episode의 240Hz 추적 연속성과 끝 도달을 검사한다.
- 실행기는 소스·입력 파일 집합과 SHA를 각 단계 전후 확인하고 두 seed의 100→200→300회 학습과 mean/sample 평가를 순차 실행한다. 후속 조건은 기준군 두 seed의 최종 평가와 사전 분기 기준을 요구하고 최대 한 프로파일로 제한한다.

## 지적과 수정 확인

|항목|확인한 수정|
|---|---|
|E4 첫 1초의 단계 선택이 priority 관측과 불일치|`_focus(False)` 재사용, 0초·0.5초 CPU 사례 추가|
|참조 재생의 실패 episode도 단순 완료로 표시 가능|완료와 `passed` 분리, 안전 완주·전체 유지·정시·초기 상태·FK 문턱 및 실패 종료 코드 추가|
|초기 자세·활성 축에 과거 중지/16축 설명 잔존|새 검지 초기 자세·20축 설명으로 정정|
|모니터 오류·중단 시 학습 자식이 계속 실행 가능|`try/finally`에서 자기 process group에 SIGTERM, wait, 필요 시 SIGKILL과 wait; CPU 자식 회수 재현 통과|
|기록 중인 마지막 JSON 행을 읽어 중단 가능|줄바꿈까지 완성된 행만 모니터에서 파싱|
|후속 조건의 순서·예산 계약 미강제|기준군 완료·두 seed 최종 평가·분기 predicate·기존 후속 결과 제한 추가|
|Python 최적화 실행에서 assert 검증 생략 가능|study/analyze 시작 시 `not __debug__`를 명시 예외로 거부|

### 검수자의 앞선 지적 정정

`all_env_candidate`를 오압현 제거 전 원시 positive로 읽어 동시 후보 검사가 잘못됐다고 전달한 지적은 철회했다. `gpu/environment.py`의 `_contacts()` 최종 반환은 `positive & ~wrong, wrong`이다. `contact_loaded_target`도 같은 함수에서 distal `pad['positive']`로 재지정된다. 따라서 현재 `all_env_candidate`는 effective 후보이고 `all_env_raw_candidate`는 담당 loaded distal pad의 원시 positive다. 현재 동시 effective 후보 모순 검사와 해제 proxy의 원시 신호 선택은 이 계약과 일치한다. 과거 전체 표면 후보와 혼동하지 않는다.

## 기존 실행 산출물 확인과 한계

독립 검수에서는 이미 생성된 최종 보고서만 읽었다. fresh 2업데이트/4,096전이, strict resume 1업데이트/2,048전이, 최초 32 episode 평가와 렌더 보고서가 완료 및 lifecycle 검증을 기록하며 failure는 없다. 해당 GPU 실행을 독립 재실행하거나 영상의 움직임을 독립 시각 판정하지 않았다.

이전 reference v1의 B clean 1.35/1.5초는 전체 유지·정시 성공으로 인정하지 않는 처리와 일치한다. native 참조 성공과 학습 정책 성공은 별개다. 특히 높은 프렛의 미리 누름은 낮은 음을 차단하며, 반대 방향에서 낮은 프렛 잔류는 높은 음의 달성을 막지 않을 수 있다. 두 음 달성만으로 해제나 자연스러운 전환을 주장하지 않는다. 실패를 포함한 최종 정책 평가와 예정된 반대 방향 검증이 실제 성능 판단의 근거가 되어야 한다.

CPU 재현은 프로젝트 루트를 PYTHONPATH로 하고 CUDA를 숨긴 뒤 rl38 Python의 unittest discover로 이 연구 `tests/`의 `test_*.py`를 실행했다. 새 학습·GPU 작업은 실행하지 않았다.
