# 장시간 GPU 학습 전 점검 결과

2026-10-21. **점검은 완료했지만, 현재 장기 학습 시작은 권하지 않는다.** 사용자가 허용한 자연스러운 기타 이탈과 별개로, 실제 학습 중 네이티브/비Torch GPU 메모리 증가가 남았다.1024환경은 실제 메모리 부족으로 중단됐고512환경도 후반 여유가 계속 줄어 시험을 정상 중단했다. 현재 장기 학습 권장 환경 수는 미확정이다.

왼손·기본67음 곡·최대 모델large·H32·seed7·GPU PhysX/CUDA 경로를 검사했다. 기록과PPO 평가의 메모리 문제를 수정했지만, 환경 수를 줄이는 것만으로 남은 문제를 해결했다고 판단하지 않는다. 긴 학습용 명령은 발행하지 않았다.

## 실제 실행 결과

| 실행/변경 단계 | 반영된 업데이트 | 결과 |
| --- | ---: | --- |
| train1024_large_70 |26|다음 수집 중GPU free1GiB 보호 기준으로 중단. 복구 모델26 저장 |
| train1024_large_64_cache_v2 |추가22,누적48|PhysX200MiB 할당 실패→CUDA 오류. 오류 직전 저장 실패, 주기저장46 보존 |
| train1024_large_64_cache_v3 |28|다음PPO의 전체rollout forward에서1GiB 임시텐서 할당 실패. 주기저장20 보존 |
| train1024_large_64_batched_v4 |39|다음 수집 중PhysX48MiB 할당 실패→CUDA 오류. 주기저장30 보존 |
| train512_large_128_v5 |94|128회 예산으로 시작했으나후반 메모리 증가를 확인해SIGINT로정상중단. 복구 모델94 저장 |
| resume512_after_inspection |추가1,누적95|모델94를strict load한 뒤 실제GPU 업데이트와final.pt 저장 통과 |

앞선1024실패4개는 그대로 보존했다.512시험은 **메모리 부족으로 자동 종료된 실행이 아니며**, 계획한128회/두 곡 길이까지 완료한 실행도 아니다. SIGINT 요청은`intentional_stop.json`, 실제 중단은`report.json`에 기록한다. 처음 비권한 프로세스에서의 신호 요청은PID namespace 차이로 전달되지 않았으며, 같은 호스트 실행 권한에서 보낸 요청만 실제 적용됐다(`stop_request_first_attempt.json`).

## 반영한 최소 수정

1. **기록의RAM 누적 제거:** GPU runner가 모든 종료episode 객체를 계속 보유하던 부분을counter로 바꿨다. 상세 기록은기존`episodes.jsonl`에 유지한다. GPU`song_report.json`은v2이며`episode_counts`와`episodes_path`를 제공한다.
2. **Torch와PhysX의 메모리 경쟁 완화:** PPO 지표 계산 후 더 이상 필요 없는rollout buffer를 해제하고, 최적화 경계에서 유휴CUDA 캐시를 반환한다. 여유가1GiB 미만일 때도 반환 후 같은1GiB 기준으로 다시 검사한다. 반환 전후free/current allocated/current reserved·이유·횟수를기록한다. 실제 살아 있는Tensor나안전 하한을없애지 않았다.
3. **전체평가의 메모리 피크 제한:** 전체rollout KL와최종진단의forward를최대4096표본씩나눠계산한다. 결과를원래순서로합친뒤기존전체KL/평균을계산한다. 전체표본·매actor갱신후KL 검사·임계값·rollback·실제학습minibatch/shuffle·PPO 목적은유지했다. 작은rollout은기존단일forward다. 큰GPU GEMM의batch가달라미세한부동소수점차이는가능하며GPU 비트동일성을주장하지않는다.
4. **저장간격 지정:** `--checkpoint-every N`을추가했다. 기본5는유지하고양의정수만허용한다. large checkpoint는약67MiB여서기본간격으로1만업데이트를하면모델파일만약130GiB다. 기존저장본은자동삭제/덮어쓰지않는다.

이번수정은6개기존Python파일에한정된다: training/gpu_runner.py, training/start.py, training/ppo.py, training/ppo_diagnostics.py, tests/test_gpu_training.py, tests/test_ppo_logging.py. 기존물리·자세·보상·접촉·힘/관절한계·종료기준·소리성공의의미를바꾸지않았다. 기타직접힘·부착·진행중자세주입도추가하지않았다.

## 남은GPU 메모리 문제

v4는Torch 최고allocated약1.69GiB/reserved약2.26GiB까지줄었고캐시반환161회도실제실행됐지만PhysX 할당실패가재발했다. v5의최적화후free는첫약9.17GiB에서마지막약1.83GiB로감소했다. 중간에긴plateau가있다가크게증가해, 짧은구간에서안정돼보인것만으로장기준비를판정할수없었다.

비Torch 증가에는PhysX 외CUDA 라이브러리/컨텍스트·전역GPU 사용도포함한다. 접촉heap의고수위확장인지내부누수인지아직확정하지못했다. Python Tensor acquire/unwrap/setter수명에서확인가능한API 위반은독립감사로발견하지못했다. 자세한근거와버전차이의한계는[네이티브메모리감사](native_memory_audit.md)를따른다.

공식IsaacGymEnvs 저장소에환경수가늘면더빨리VRAM이증가하다같은오류로멈춘다는[미해결사용자보고](https://github.com/isaac-sim/IsaacGymEnvs/issues/225)가있다. 현재와동일원인으로확정된NVIDIA 진단/수정은아니다. [환경별aggregate완화보고](https://forums.developer.nvidia.com/t/weird-memory-allocation-possibly-memory-leak-during-simulation/221757/2)도있으나사용자우회사례이며, 이번단일강체89형상의장기조건에서검증하지않아현행에반영하지않았다. GPU 접촉버퍼를줄여충돌을누락시키거나안전기준을완화하는대안도채택하지않았다.

## 정상중단·저장·재개 검증

v5는94회업데이트·1,540,096전이를PPO에반영했다. 중단한수집의3,584전이는폐기했고원로그를수정하지않았다. 반영된종료episode는1,802개이며곡시간축완료254개·물리실패1,548개·음악단계성공0개다. 아직position단계(progress0)이며보상진급/음악수렴을검증한결과가아니다.

counter는성공적으로PPO에반영된수집기준이다. 오류/중단때`episodes.jsonl`에는미반영수집의종료기록도남을수있으므로journal의committed/discarded와구분한다. v5의원자료/반영episode범위와counter일치를`verify_inspection.py`로검사했다.

`train512_large_128_v5/failure_last_valid.pt`의정책·두optimizer·RNG·보상단계가`resume512_after_inspection/initial.pt`에정확히복원됨을확인했다. 실제CUDA 학습1회후`final.pt`의누적업데이트95·변경된모델·유한한모델/optimizer도검증했다. 입력변경/import누락/정리오류0이었다. 물리는새준비자세의에피소드로시작하며중단한궤적을이어받지않는다.

단기재개통과가장기메모리문제해결을뜻하지않는다. CUDA 문맥손상이나PPO 중간실패뒤에는즉시복구저장을보장하지않으며, 각실행의실제로발행된checkpoint만복구근거로사용한다. 디스크여유를자동보호하는기능도없다. 이번에는긴학습용템플릿을삭제하고실제로실행한유한점검/재개명령만보존했다.

## 검사와원문보존

관련CPU 검사60개가통과했다: GPU/PPO48개(`tests_batched_v4.log`), 공용모방/정밀화경로12개(`tests_shared_ppo_dependents.log`). 새검사는불완전chunk·출력/전체KL/진단의동등성·no-grad·RNG/모델불변과저장간격검증을포함한다. 기존소규모검사에서는보관본과3역할의weights/optimizer/RNG/기존metric 정확일치도유지했다. 전체CPU 회귀검사와오른손지속학습은이번범위가아니다.

수정전원문은`guitar_learning/archive/20261021_before_gpu_long_run_check_v1/`와`20261021_before_ppo_batched_diagnostics_v1/`에보존했다. 실패1/2/3의실제Python원문은각각`source_before_cuda_cache_release/`, `source_before_optimizer_cache_release/`, `source_before_batched_ppo_evaluation/`에있다. 실패4와v5/재개는같은최종활성코드를사용했다. 과거sealed 결과·native/자산·protected3파일은수정하지않았다.

`verification.json`의completed는**점검기록검증완료**이며long_training_ready는false다. `source_manifest.json`은과거시도별정확한원문/입력SHA와최종소스를식별하고, `artifact_sha256.json`은결과파일을봉인한다. `source_final/`은최종활성Python/문서의사본이다. 학습중에는실행에묶인Python/자산/활성곡파일을수정하지않는다.
