# 원격 main 학습 의존성 검토

검토 기준: `origin/main` 커밋 `cdca74d921d25142af73caed326a6f19ae1fc27b`. 원격 주소의 실제 SHA 확인과 별도 복제·Git LFS 검증은 주 검토자가 별도로 수행한다. 이 문서는 현재 파일과 해당 Git 트리를 읽기 전용으로 대조한 결과다. 새 학습·GPU 실행·기존 입력 수정·커밋·push는 하지 않았다.

## 결론

- **기본 학습**: 활성 `guitar_learning` Python 295개가 모두 원격 트리에 있다. 기존 자체 포함 입력 감사 목록의 214개도 전부 원격 트리에 있다. 소스와 입력의 정적 존재 확인은 통과했다. 원격 복제에서의 실제 실행 결과와 동일한 의미는 아니다.
- **현재 중지 6→8 연구**: 아직 원격에 없는 새 목표 번들·실험 실행 코드·초기 기하 입력을 사용한다. 따라서 현재 push 파일만으로 이 실험을 그대로 실행하거나 현재 모델을 엄격 평가·재개할 수는 없다.
- Python 환경, NVIDIA 드라이버, C++ 컴파일러와 시스템 라이브러리는 각 PC에 설치해야 한다. 이는 프로젝트 데이터의 외부 파일 의존성과 구분한다.

## 기본 학습 입력

`docs/maintenance/self_contained_20261031/inputs.json`에 등록된 입력 214개가 모두 원격 트리에 있다. 이 목록은 기본 곡 `05_BN2-131-B_solo`, 67음과 준비 상태 105축을 검사한 기록이다. `guitar_learning/assets/native_provenance.json`과 `guitar_learning/native/paths.py`의 현재 바이트는 원격과 동일하다. 오래된 감사 목록에서 이 두 파일의 SHA가 다른 것은 그 목록 생성 뒤 변경된 현행 파일이 이미 push되었기 때문이다.

목록의 `data/song_bundles/05_BN2-131-B_solo/source/audio.wav`는 Git에 LFS 포인터로 기록되어 있다. 일반 Git 복제만으로 데이터 실체까지 받아졌다고 판단하면 안 된다. 원격 LFS 객체와 복제본의 실체 검사는 별도 결과를 따른다.

`native.paths.resolve_input_path`는 실제 입력이 프로젝트 밖으로 해석되면 거부하며, 이전 절대 경로를 내부 출처 사본에 매핑한다. JSON에 남은 과거 경로 문자열 전체를 실제 외부 파일 접근으로 간주하지 않았다. 기본 실행은 `train.py` → `training/launch.py` → `training/finger_skill_runner.py`다.

## 현재 6→8 체크포인트에 실제 봉인된 입력

표본: `docs/2026-11-02/압현실험/중지6에서8프렛_환경수비교_20261101/learning_v1/jobs/s17_t1245184_train/J/inputs_before.json`.

449개 입력 중 원격에 있는 436개는 모두 Git blob의 SHA-256이 실제 저장된 봉인과 일치했다. 이 436개에는 LFS 포인터가 없었다. 원격에 없는 13개는 다음과 같다.

| 구분 | 수 | 위치 |
| --- | ---: | --- |
| 새 6→8 목표 번들 | 8 | `data/song_bundles/virtual_middle_s3_f6_f8_AB_v1/`의 manifest, mapping 2개, audio, training 4개 |
| 초기 자세·출처 | 2 | 새 연구의 `geometry/initial_catalog.json`, `geometry/initial_provenance.json` |
| 전환 실행 구현 | 1 | 새 연구의 `tools/runtime.py` |
| 실행 설정 | 1 | 해당 출력의 `J/settings.json` |
| 재개 원본 모델 | 1 | 첫 블록 `s17_t622592_train/J/final.pt` |

마지막 두 개는 새 학습을 시작하기 위한 소스가 아니라 특정 저장본의 실행·재개 증거다. 모델 평가·재개를 공유하려면 그 모델과 요구되는 입력·출처도 함께 제공하고 기존 identity 검사를 유지해야 한다.

## 연구 자동 실행의 더 넓은 봉인

`learning_v1/progress.json`의 `source_seal`은 10,275개를 포함한다. 원격에 없는 9,802개 중 **9,770개는 `guitar_learning/archive/` 보관 파일**이다. 기본 모델 입력 수집은 `active_source_paths`에서 archive를 제외하지만 새 연구의 `tools/run_study.py:seal`은 `guitar_learning` 전체를 재귀 순회하여 이 보관 파일까지 자동 실행 봉인에 넣었다.

나머지 32개는 번들 8개, 새 연구 tools 16개, 초기·참조 geometry 5개, 기존 전환 연구 `tools/study.py` 1개, 벤치 진행·native 검증 보고 2개다. 따라서 자동 연구 전체를 현재 코드 그대로 재현하려면 이 봉인에 필요한 자료도 존재해야 한다. 그렇다고 9,802개 전부가 물리 학습 구현의 필수 파일이라는 의미는 아니다.

진행 중 연구의 봉인·실행 코드는 바꾸지 않았다. 향후 실험에서는 실행에 필요한 소스·입력과 보관 자료를 분리해 봉인하는 것이 적절하며, 현 저장본을 새 봉인으로 덮어쓰거나 검사를 우회해서는 안 된다.

## 실행 환경과 프로젝트 입력의 경계

`scripts/environment.rl38.yml`, 로컬 실행기, Isaac Gym Preview4 소스·native payload가 원격 트리에 있는지와 LFS 실체는 주 검토자의 별도 복제 결과로 확인한다. 각 PC에는 Linux x86_64, Python 3.8 환경과 Python 패키지, 호환 NVIDIA 드라이버, C++ 컴파일러·Linux C++/OpenGL 라이브러리가 필요하다. 영상에는 ffmpeg와 렌더링 환경도 필요하다.

`.runtime/`의 native 캐시와 Torch 확장은 원격에 올리는 입력이 아니라 추적된 Isaac Gym payload에서 생성하는 산출물이다. 캐시를 삭제해도 검증된 원본과 실행 환경이 있으면 재생성할 수 있어야 한다.
