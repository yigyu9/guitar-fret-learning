# 짧은 준비 환경 사전 검수

**요약 판정: 문제없음.** 준비2초와 행동0 유지1초로 구성된 최소 native 연결 시험을 진행할 수 있다. 실제 reset setter·관절 속도/질량 행렬 일관성·접촉 안정성은 이 시험의 결과로 확인해야 하며 사전 통과로 간주하지 않는다.

검수 범위: `environment.py`, `environment_v4.py`, `fretting_environment_v2.py`, `prepared_reset_v1.py`, `run_fretting_probe_v3.py`, 관련 신규 테스트와 기존 native 최종 제출·발 유지·Chest/hip/SO3 effort 경로. 코드·원본은 수정하지 않았고 물리/학습 실행이나 CPU 전체 검사 반복도 하지 않았다.

- 기본 준비 시간은 실제2초이며1–2초 범위의60Hz 제어 tick만 허용한다. 실제 scene step은0에서 시작하고, 기본 준비 종료는480, 유지1초 종료는720이다. 접촉 tracker의 목표 구간도480–720이다.
- 기존 constructor가 원래 FK·지지점·발 기준·hip-load·SO3 참조를 생성한 뒤 저장된 준비22초의 human DOF pos/vel, 기타 RB 상태 및 최종 목표를 reset 초기화로 한 번 적용한다. 인간 articulated RB setter는 호출하지 않는다.
- `_restore_once`는 실제 물리 step0, 원 이름/순서·자산·의자·PD속성·gain·범위·고정 root/의자 조건을 검사한다. 초기화 guard는 finally로 복원하고 DOF 및 기타 pose/velocity를 읽어 확인한다. 인간 link pose 오차는 기록하되 전체 simulator checkpoint exact를 주장하지 않는다.
- 기존 controller의 `s`에만 mature phase view를 적용한다. 발 유지 apply, Chest·hip-load·distal SO3 effort의 시간 ramp는 준비 이후 값으로 평가한다. `native()` 등 bound method와 실제 scene 시간은 원 scene을 사용한다. 진단의 실제 step과 control-phase step도 별도 기록한다.
- 준비 tick은 저장 목표를 원 최종 제출 경로로 넘기며 기존22초 `targets()`/음악 스케줄러/play_latch를 호출하지 않는다. 그 때문에10초 latch 시각/과거 target_rows를 요구하는 원 targets의 전제와 충돌하지 않는다. 원 effort를 유지하여 별도 PD를 중복 추가하지 않는다.
- 원 snapshot/config/초기설정/과거 pin 파일의 고정 SHA 및 선언 모델 mesh SHA를 검증하고 process 내 cache를 사용한다. reset마다 전달하는 state/target은 private copy다. 실행기에는 reset 입력이 사전 pin으로 추가되며 새 개발 의존성과 원 native runtime/assets의 감사 구분은 유지된다.
- 기록된 CPU59개 통과를 확인했다. 주요5개 소스의 현재 SHA가 CPU 사전 pin과 모두 일치한다. 테스트는 guard 실패 시 복원, 인간 RB setter 제외, private copy, phase/실제 clock 분리, 원 targets 미호출,1초·2초 길이와 접촉 표본 시각을 다룬다.

## 검수 SHA256

| 파일 | SHA256 |
| --- | --- |
| environment.py | `92a0eb347e5d99e131b517a291eb90d0642ba072600bc00593539945f23add04` |
| environment_v4.py | `b0fc351209ca2088e0eebe858105bebe9b21713227c829d1de5618036cc064da` |
| fretting_environment_v2.py | `2731e8e5deca8cacadbe4a95f37525321d74674a6cb1c564f059d0749fe7a41a` |
| prepared_reset_v1.py | `2518037412db0e2d41c7507f32cb845a9f609ad3aaffc318e0cef6d0359dd973` |
| run_fretting_probe_v3.py | `34ef2118f7ebf983df1bf8d4586c334b30ae6f78b2bb14076a623f32f5fe293f` |

이 변경은 reset 시 초기조건 설정과 짧은 유한 제어 정착이며 매step 상태 주입이나 기타 보조 힘이 아니다. 저장된 상태를 solver 내부 상태까지 복원하는 checkpoint로 해석하면 안 된다. 이후 결과에서도 새3초 연결 시험과 과거 전체V3 결과, 음악 수행/PPO를 구별해야 한다.
