# 왼팔 지지 목표 유지 + 손가락 Fret 최종 검수

요약 판정: **문제없음 — 구현·제어권 분리·기록 검수 PASS**.

Critical: 없음. Warning: 없음. Suggestion: 없음.

이번 PASS는 기타 안정화 또는 음악 성공 판정이 아니다. 기타 초기 회전 유지와 운지 목표는 달성되지 않았다.

## 코드·실행 근거

- [run_fret_fingers_arm_hold.py:103](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:103): 2.000초 인계 직전 마지막으로 제출한 왼팔9 목표를 복사한다. PLAY655 control의 최종 제출 L9가 이 목표와 정확히 같다. 실제 L9 관절값은 인계 상태에서 최대0.040218rad 움직였으므로 물리적 고정으로 해석하지 않는다.
- [fret_finger_target_ownership.py:7](/home/ajou/yigyu/3/stability_adapter_2/fret_finger_target_ownership.py:7): 81축은 Fret21/준비L9/bounded hold15/초기36으로 중복 없이 나뉜다. source30 요청은 기록되고, L9는 native에 적용하지 않는다. LH21의 합성 요청은 source 요청과 같으며 최종 제출에는3.2rad/s·native한계가 적용된다.
- [run_fret_fingers_arm_hold.py:121](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:121): 실제 최종 제출 목표를 source pd_target/prev_action으로 회신한다. 기타·손 상태를 덮어쓰거나 외력을 적용하는 경로를 추가하지 않았다. runtime17개 검사에서 금지 쓰기 없음, root·하체 고정 및 actor 불변을 확인했다.
- [run_fret_fingers_arm_hold.py:133](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:133): 단일 owner가 control당4 physicsstep을 적분한다. source frame0~654 평가 뒤 최초 done에 즉시 종료했다. 최종 controls.source_info와 terminal_info가 같으며 done은 마지막에1회다. 원본 실패 기준을 완화하거나 terminal 후 HOLD를 추가하지 않았다.

## 원자료·영상·보존 검증

- 기존 Fret30 baseline과 최초120 PREP 제출 목표, t=0~2초61 native trace, 두 카메라61frame SHA가 정확히 같다. 실행은3100 physicsstep/12.916667초, actor655회다.
- native camera389frame에는 terminal physicsstep3100이 포함된다. 저장 trace와 camera step열이 같으며 렌더가 상태를 변경하지 않았다. 전체778PNG SHA 및 두 원본 MP4 SHA를 재확인했다. 각 영상389frame/30fps/12.966667초와 물리 시각의 차이는 표본 포함·frame 수로 설명된다. 두 모음 영상은 원본과 byte/SHA가 같다.
- native 입력1148개는 실행 중 불변이었다. 현재 변경된 main PLAN/README2개는 실행 후 진행 추가이며 native/source_before에 소비 SHA가 그대로 있다. 나머지 현재 입력 SHA와 분석14개 입력 SHA가 일치한다. source_final8파일은 해당 최종 원본 SHA와 일치한다.
- 기존 봉인된 baseline inventory1013개 artifact를 재해시해 모두 그대로임을 확인했다. wrapper가 기존 stability_adapter 전체를 해시했다고 주장하지 않으며 이번 변경 파일은 새 A/D 범위에 한정됐다.
- 분석23검사 및 root recording_audit31검사는 모두PASS. README26개·CHANGED_FILES24개 절대 링크와 실제 줄 번호가 유효하다. PREP actor OFF, 손가락 합성 요청/최종 제출 제한, 소비 leaf 보존·main 결과 기록 문구를 수정한 뒤 재대조했다.

## 물리 결과와 해석

[analysis/summary.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/summary.json:1): 같은2.766667초의 t=0 대비 G 변화는 baseline434.475mm/68.336°에서72.743mm/9.855°로 감소했다. 전체 새 실행의 최대 변화는73.190mm/50.248°이며 최종48.097mm/50.248°다. 초기 이탈 감소는 확인되지만 초기 회전 유지 성공으로 볼 수 없다.

원본 index finger_back 실패로12.916667초에 종료됐다. press0%, sustain0/27, goal_finished=False다. 실제 초기·2초·종료 native frame과 문서 설명을 대조했고 이미지가 접촉/관통 또는 음악 성공을 입증한다고 주장하지 않는다. CPU PhysX/lavapipe와 체크포인트 자산·구현 차이도 문서에 표시됐다. 다음 단계의 작은 기타 기준 왼팔 보정은 후속 실험이며 이번 성공으로 보고하지 않는다.

## 검수 대상 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/FRET_FINGERS_ARM_HOLD_PLAN.md`: `a2b77ecaf7bb473816d316cb872df610175bbd282fc4488cb4de318c149482d8`
- `/home/ajou/yigyu/3/stability_adapter_2/fret_finger_target_ownership.py`: `5b6d0f8408f3c92ad7104e5b309120dc89f12e54195bf2ce56c182fdfbf71dff`
- `/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py`: `1345e98dfef9246c1e93b49ae6f4cabfc7f54921ee92b373d9c16890c6f5232a`
- `/home/ajou/yigyu/3/stability_adapter_2/fret_fingers_arm_hold_preserved_run.py`: `7baa7f562b6e44e760dc4af0e729bd96b20958280aecd944d73e52c32013364a`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_arm_hold.py`: `239177eae5d7cc5b91c13a4a4a5047987d8de3f35b28e016a2f361000a0d4fd4`
- `/home/ajou/yigyu/3/stability_adapter_2/PLAN.md`: `44513dafd76fe8a599489a411c4dfb6c71f5d5f4584968bf4b5940ced7f372f2`
- `/home/ajou/yigyu/3/stability_adapter_2/README.md`: `c7b38979d3d5b038e18bc05f5b34540a8d10fde4853ca22db9319c6373bdcd17`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md`: `735b91ba198521159d23fc8b446ef3e5f25aeaf1d4df11e65023a0ca0053819d`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/CHANGED_FILES.md`: `9836702a670317ab399ad7d8f75f6fd13f5cba842af7a643c08e1def6e4d597d`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/pre_review.md`: `8898da717306c6eee848725bea5cfe175a454f867f151c4f19699e7076f0249b`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/ownership_preflight.json`: `6eb127c244f2c5de55059b1507d1fa140c2ef06d579f8888eb08353969759402`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/recording_audit.json`: `bcf0b8c0c26b7def0022927783d434d2bff721c7244a4c13b9b49ba4d1065fa7`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/source_preservation.json`: `5b9d5bc7044aa0fcaa00fcc0f8b5732e1aa06b1cb38e6b0af0b223569edb7c45`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/summary.json`: `7172c84ad5f66875be635391a7a1ba1a40d3447aca489700425c01bcc64b363a`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/inputs.json`: `f716c18698a85e13882305d9933805fe78aa85646279a3bbe02ab26ed94a6464`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/inputs_before.json`: `b466a9ed5805bdfa1ab162f55261bfcbe50c8e765f3e77c7811946848d11f733`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/inputs_after.json`: `2112cdb8a0e6a0ca19d9ba9fce4418959f0c4b0085f763d321d0bf50a5fb250a`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/report.json`: `7abc04243d4438a939199d6fa90ef062e0748bf847ba41752b6bd82e3769d587`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/terminal_info.json`: `4a0a95bb60d326f7f256cce2c3af15c5a933e261fac71687c1d7b57dc1436464`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/handoff_values.json`: `625da2fae0bc8853c9d9d93e692d3698287ccae6b528e11e82ed4df9b46877f2`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/controls.json`: `268676b5c1e9a0f711acff8f2dc6f2202c66f634e9eefce1f003fe9129c58792`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/trace.json`: `576449e5d7739eac5a3b588d5df167ab0d27aa894d5ff219c86021c00ac69fb6`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/capture.json`: `8cdaf7c6b348c23b98d35316c970533573befdfd555252ee9adad9408952411f`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_fret_arm_hold.md`: `bced7f387253904673f59b1c28cc2b163665f8cc964810561c680515ee7ef2fd`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_COLLECTION_fret_arm_hold.json`: `7c9afffa1fa4c257807eddd02ed49c04d97f7a40809e84184635f0eb2bad8b0e`
