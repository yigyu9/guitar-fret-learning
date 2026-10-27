# GPU 재확인 결과

2026-10-12 약03:55–04:00 한국시간. 최초 격리 실행의 nvidia-smi 실패를 드라이버 고장으로 해석한 설명을 정정한다.

| 검사 | 격리 실행 | GPU 접근 실행 |
|---|---|---|
| 장치 노드 | nvidia0/nvidiactl/nvidia-uvm 접근 불가 | 모두 존재 |
| nvidia-smi | 드라이버 통신 실패 | RTX4070Ti,580.178.04,12282MiB |
| PyTorch2.4.1+cu121 | CUDAFalse,0device | CUDATrue,512×512행렬 곱 유한값 |
| 독립 Isaac Gym GPU PhysX | 검사 대상 아님 | cuda:0 root tensor,유한값,물리step 후Z=0.9997445344924927m |

독립 물리 검사는1m 높이의10cm상자에 중력을 적용한1step(1/240초)이다. GPU Pipeline/PhysXuse_gpu가 모두True다. humanoid·기타 환경이 GPU PhysX로 전환되었다는 뜻은 아니다. 일부 가져오기 시도는segmentation fault로 종료됐으며, 기존 제한스레드 실행 조건(OPENBLAS_NUM_THREADS=1,OMP_NUM_THREADS=1)을 적용한 최종 시험은 정상 종료했다. 정확한 crash근본원인까지 인증한 것은 아니다.

사용자가 수행할 재설치·재부팅·sudo조치는 없다. 기존 scalar native 장면은 CPU PhysX 전용이며, 새 마감 실행은 CPU PhysX/학습CUDA를 분리한다. 기존 CPU검증 소스는 수정하지 않는다.
