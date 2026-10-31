# 실행 자산과 검증 원문

이 디렉토리는 현재 코드가 읽는 입력이다. 이름에 `archive`, `tab2body`, `stability_adapter_2`가 들어가더라도 과거 코드 보관 폴더로 판단해 옮기거나 삭제하지 않는다. 실제 Python 보관본은 상위 패키지의 [archive](../archive/)에 있다.

| 위치 | 역할 | 사용 범위 |
| --- | --- | --- |
| `prepared_reset_v1/` | 준비 상태·105축 기준과 GPU 왼손 v9 초기 자세 | 기본 학습·평가 초기화 |
| `gpu_rigid_guitar_v1/` | 현재 GPU 기타 XML·충돌/시각 메시·manifest | GPU 학습·평가·렌더 |
| `runtime_inputs/` | 과거 경로에서 내부로 옮긴 실제 설정·기하 입력 | 기본/공용 실행; 내부 archive도 필수 |
| `tab2body/`, `stability_adapter_2/` | 내부화한 인간·기타 메시와 공용 물리 자산 | 현재 공용 native/GPU 실행 |
| `historical_inputs/` | 과거 원본 바이트와 SHA별 CAS index | 검증 입력; 코드를 실행/import하는 위치가 아님 |
| `natural_press_v3/` | 특정 압현 준비 연구의 초기 분포·기하 catalog | 명시적 연구 전용; 기본 J 실행 입력과 구분 |
| `native_provenance.json`, `origin_manifest.json` | 현재 내부 자산과 원본 계보·SHA | 출처 검증 |

## 헷갈리기 쉬운 두 파일

- [support_candidate.json](runtime_inputs/paper/initial_pose/archive/experiment_records/lower_body_release_v1/front_facing_pose_v1/source_v9/support_candidate.json)은 현재 지지 기준을 구성하는 실행 입력이다.
- 전달용 [trace.npz](../../data/diagnostic_inputs/finger_fk_native_v1/trace.npz)는 과거 관절·몸체 기록이다. 기본 학습은 읽지 않고 FK/native 비교에 사용한다.

실행 자산의 이동·수정은 내부 경로, 현재 SHA와 원본 SHA, 메시 참조와 준비 상태 계약을 함께 검증해야 한다. 폴더 모양을 정리하기 위해 실제 입력을 재배치하지 않는다. 현재 실제 실행 입력 목록은 [입력 감사](../../docs/maintenance/self_contained_20261031/inputs_final.json), PC 이동·내부 실행은 [PORTABILITY](../../docs/PORTABILITY.md)를 따른다. JSON에 남은 과거 절대 경로 식별자를 외장 파일을 다시 읽으라는 지시로 해석하지 않는다.
