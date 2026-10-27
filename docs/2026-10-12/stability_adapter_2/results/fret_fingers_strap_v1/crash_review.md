# 스트랩 첫 native 실행 중단 검토

요약 판정: **수정 권장 — 1차 실행은 완료 검증 자료로 채택할 수 없음**. 특정 Python 코드 버그나 native 충돌 원인은 아직 확인하지 못했다.

Critical: 확인된 코드 결함 없음.

Warning:

- [native_crash_audit.json:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_crash_audit.json:2): 첫 실행은 exit139로 중단됐고 report·normal 입력 closure·controls·trace·terminal·strap_forces가 없다. **제안:** 첫 실행을 별도 실패 시도로 보존하고, 새 경로의 재실행에서 report·원본 done·물리/영상/입력 불변 검증을 확보한다. 부분 영상으로 안정화나 성공을 판정하지 않는다.

Suggestion: 없음.

## 확인된 범위

첫 실행은 초기값과 native/overlay 카메라58frame을 저장했다. 마지막 저장 camera는physicsstep456,1.900초이며 렌더 후 상태 보존 표식은true다. 마지막 저장 시각은 실제 fault 시각을 특정하지 않는다. handoff_values.json이 생성되지 않았고 source_actor_start_reached=False로 감사됐으므로 Fret 정책 연결까지 검증된 실행이 아니다. 소비1156 입력의 현재 SHA를 독립 재확인했고 모두 native inputs_before와 같다.

[native.log:16](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native.log:16): CPU PhysX/GPU pipeline disabled 및 CUDA·visualgeom 경고는 기록됐지만 Python fatal stack은 없다. 이런 경고만으로 segfault 원인을 GPU·화면·힘·접촉 중 하나로 단정할 수 없다.

읽기 검토한 native 호출 경계는 다음과 같다. [run_fret_fingers_strap.py:137](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_strap.py:137)의 contact 조회, refresh/native_state와 route의 body/DOF 상태 조회, [underneck_strap_environment.py:40](/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py:40)의13점 force 제출과 simulate/fetch, [gym_trial_recording.py:22](/home/ajou/yigyu/3/stability_adapter_2/gym_trial_recording.py:22)의 graphics/render/image 조회 및 [strap_trial_recording.py:58](/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py:58)의view/projection/depth 조회다. 이는 조사 가능한 경계 목록이며 어느 호출이 실제 fault를 일으켰다는 증거는 아니다.

두 번째 실행은 원본 소스와 물리 조건을 그대로 두고Python -Xfaulthandler만 추가해native_v2에 저장한다. root 중간 보고에서2.1초까지 진행돼 첫 저장 종료점1.9초를 통과했다. 이것이 faulthandler로 물리 오류가 고쳐졌다는 증거는 아니며 일시적 native fault 원인은 계속 미확정이다. 이 문서는 첫 사고의 진단 기록이고 두 번째 실행의 최종 검수/완료 판정은 별도 report와후속review에서 해야 한다.

## 검토 자료 SHA256

- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_crash_audit.json`: `2cbfcdf116a4f1956814ccbeae1d0fbc36a1d9172243e7f240e150d82037cabc`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/retry_plan.json`: `836a79d0d47cadcc7aaa0fda5a1cf02593e65c10d66ab674614ebb82cb5bc50c`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native.log`: `f1e5178ee776458095b904e7bc4368522848d7a3ec77a9f0cffb961bbe77ebae`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native/inputs_before.json`: `15e9e90716d5aa157db80fa9965b6ec021b27bf4e4ee3cc7d88c58d4921ad196`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native/data/images/capture.json`: `f0bec303f836ba073cb7f41072458ed4242fb4e055199f50677fc5f4ba963575`
- `/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_strap.py`: `a6533a1a7a8151eac1105ef75308cd737f927454c6beeea2a2c04f811d4c9064`
- `/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py`: `e60fe4d4f792254d5b95bd4c1fb689a1c11293c67663dcf67e2f12a0427dc88e`
- `/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py`: `a52a33eecdb943d0acbc7faffa51816ab47447c7a9c48d4036e8dd70fb7353f3`
