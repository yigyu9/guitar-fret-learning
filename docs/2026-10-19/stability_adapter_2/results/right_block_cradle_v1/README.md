# 오른쪽 두 블록으로 받치는 초기 자세

몸통과 오른 Thorax/Shoulder 초기각을 조정해 기타 바디가 Thorax–Shoulder / Shoulder–Elbow 두 구간에 가까이 놓이는 자세를 만들었다. 초기 기타 p/q·root/하체·손가락42를 유지하고 왼손은 기존 넥 근처 배치를 유지했다. 스트랩 없이 실제 Isaac Gym/PhysX에서 정지5초와 오른팔꿈치 움직임5초를 비교했다.

선택한 근접 후보에서 R_Elbow_y 실제 관절각은10.114° 범위로 움직였고 기타가 빠지지 않았다. 같은 시점의 정지 조건 대비 추가 변화는 최대 **0.071mm·0.032°**였다. 팔꿈치 운동2.5–4.5초 동안 두 블록 contact 존재는480/480step, 양쪽 모두 양의 raw lambda인 step은223/480이었다. 후기0.5초에도 두 부위 접촉 존재가120/120step 유지됐다. raw lambda를 접촉력 N으로 해석하지 않는다.

초기 대비 기타 바디 중심의 최대 이동은5.329mm, 최대 SO3 회전은4.495°였고 종료 시4.102mm·3.997°였다. 몸통9 실제 관절각 편차는 최대0.761°였다. 오른 전완·손/머리 접촉은0이다. **왼엄지와 오른 허벅지 접촉도 남아 있으므로 오른쪽 두 블록만으로 유지된 것은 아직 확인하지 않았다.**

## 확인할 파일

- [설계·제어·상세 비교·다음 단계](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_COMPLETION_V1.md:1)
- [선택 후보: 전체81 초기각·기타 p/q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/search_v7/seed0/candidate.json:1)
- [팔꿈치 시험 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/config_v1/elbow5_close.json:1)
- [실제 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_elbow5_close/initial_values.json:1)
- [완료11조건의 분석과 명령식 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_analysis_final_v1.json:1)
- [짧은 물리 중단과 불완전 분석 파일 보존 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/failure_audit_v2.json:1)

## 실제 전신 영상

0–2.5초 준비,2.5–4.5초 팔꿈치 목표±5° 한 주기,4.5–5초 관찰이다. 물리 경과는5초, t0와마지막frame을 포함한 영상은151frame/30fps/5.033초다. 기타는 자유 상태이고 사람 관절에 유한한 보정 토크를 준다. 수동 고정·강제 부착·기타 상태 덮어쓰기를 사용하지 않았다. Fret/Strike 연결과 학습은 이번 진단에 수행하지 않았다.

![근접 후보의 팔꿈치 움직임 실제 Isaac Gym 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_elbow5_close/media/whole_body.mp4)

## 초기 옆면

![기타와 오른쪽 두 블록의 초기 배치 실제 Isaac Gym 옆면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_elbow5_close/media/initial_support_side.png)

기타 바디 위쪽에 오른 Thorax와 상완 근위부가 가까이 놓인다. 그림 자체가 접촉 인증은 아니며 위 접촉 집계는 native physics 원자료에서 얻었다. source 초기 간격은 Thorax0.3001mm·상완1.9999mm·전완33.1523mm다.

## 시도 범위와 남은 검증

CPU 완료 후보14개 중2개를 초기 후보로 통과시켰다. native12회 중11회가5초 완료했고1회는5physics step에 Jacobian 속도 guard로 중단됐다. 짧은 실패 영상도 보존했다. 첫 반대면 감싸기 후보들은 통과하지 못했다. 실행에 소비된 소스/leaf 계획/설정/원자료와 기존 실험은 보존한다.

왼엄지 기여를 분리한 유지 시험과 다른 팔꿈치·손목 방향의 작은 움직임을 다음에 검사한다. 한 축/한 주기의5초 결과이므로 모든 팔 운동·연주 완주·반복 재현성이 확인된 것은 아니다. 메인 계획과 학습 구조를 이 진단 결과로 대체하지 않는다.
