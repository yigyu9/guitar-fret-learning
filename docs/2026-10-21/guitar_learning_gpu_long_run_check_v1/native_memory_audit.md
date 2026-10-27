# 네이티브 메모리 증가의 범위

독립 `gpu_backend_audit`가 읽기 전용으로 장면·SDK 텐서 수명·실제v4 메모리 이벤트를 조사했다. GPU를 추가 실행하거나 코드를 수정하지 않았다.

현재 코드에서는 상태/Jacobian/접촉 텐서를 장면 생성 때 한 번만 acquire하고 이후refresh한다. 제어 대상/힘은 영구 보관하고 reset 인덱스는 이름 있는 변수와 setter 후CUDA 동기화까지 유지한다. SDK가 경고하는 즉시 소멸 임시Tensor 패턴이나 Python의 GPU 텐서 누적을 확인하지 못했다. 이는네이티브 내부 누수 부재의 증명은 아니다.

- [장면 acquire](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:206)
- [reset 인덱스 수명](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:308)
- [제어 제출](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:336)
- [SDK unwrap 구현](/home/ajou/yigyu/3/isaacgym/python/isaacgym/gymtorch.py:97): data_ptr/shape descriptor, own_data=False, 자체GPU 할당/복사 없음
- [SDK tensor 수명 규칙](/home/ajou/yigyu/3/isaacgym/docs/programming/tensors.html:414), [setter/refresh 제한](/home/ajou/yigyu/3/isaacgym/docs/programming/tensors.html:433)

v4의 optimizer-boundary `free+Torch_reserved`를 이용해 Torch 캐시 증감을 제거하면, 첫 업데이트 대비 비Torch 추가 사용량은18–24회2,616MiB,25–31회4,292MiB,35–38회6,814MiB로 긴 plateau 후 크게 증가한다. 단순한 매step/reset 일정량 누적보다는 접촉/solver heap의 고수위 확장을 우선 의심한다. 비Torch 추정에는 다른CUDA 라이브러리/컨텍스트·전역GPU 사용도 포함하므로 PhysX 소유 메모리만 직접 측정한 것은 아니다.

v4의 첫 네이티브 오류는48MiB 할당 실패이며 직후GPU narrowphase contact compression 실패가 발생했다. 48MiB는설정된4,194,304 contact-pair 용량×12B와 같지만, 내부 구현을 볼 수 없어 같은 버퍼로 확정하지 않는다.

공식 [NVIDIA PhysX GPU 메모리 문서](https://nvidiagameworks.github.io/PhysX/4.1/documentation/physxguide/Manual/GPURigidBodies.html#tuning)는 초기heap을 초과하면 추가 할당하며 별도heap allocator를 사용한다고 설명한다. 관측과 일치하는 가설이지만 PhysX4.1 문서가 Isaac Gym Preview4 수정 분기를 그대로 설명한다고 단정하지 않는다. 간헐적 내부 누수도 완전히 배제하지 못했다.

접촉 버퍼 용량을 낮춰 충돌을 누락하거나 안전 기준을 완화하는 변경은 하지 않았다. 최종512환경 시험도 중간 plateau 이후 메모리가 다시 증가했다. 업데이트 후 GPU 여유는9.1709GiB에서1.8252GiB로 줄었고,94회 업데이트에서 SIGINT로 정상 중단했다.512환경에서 실제 OOM이 난 것은 아니지만, 환경 수 감소만으로 장기 실행 문제를 해결했다고 볼 수 없다.

공식 IsaacGymEnvs 저장소의 [미해결 사용자 보고](https://github.com/isaac-sim/IsaacGymEnvs/issues/225)에도 환경 수가 많을수록 VRAM 증가 후 오류까지 시간이 짧아지는 증상이 있다. NVIDIA가 현재 사례와 같은 원인이나 수정 방법을 확정한 자료는 아니다. [aggregate를 이용한 완화 사례](https://forums.developer.nvidia.com/t/weird-memory-allocation-possibly-memory-leak-during-simulation/221757/2)는 이번 단일 강체89형상 조건에서 검증하지 않았으므로 적용하지 않았다.

저장본94를 새 프로세스에서 불러와95회째 GPU 업데이트를 완료했지만, 프로세스 재시작으로 메모리가 초기화된 짧은 복구 검사다. 동일 프로세스의 장기 메모리 안정성을 입증하지 않는다. 최종 판정은 장기 학습 준비 미완료이며 권장 환경 수는 미확정이다.
