# 동일 PALM_RATE의 DOF force 계측

2026-10-07. 목표–실제 좌표 차이의 후속 계측이다. 제어·초기 자세·길이·물리 조건을
바꾸지 않고 센서만 추가한다. 승인된 반복 검증 안의 관측이며 PD 변경 시험이 아니다.

- [x] 계획/코드 검수: 기존 runner와 환경을 재사용하고 센서 enable/read만 추가한다.
- [ ] 실제 실행: PALM_RATE fresh 1회·120steps. 기존 0.5초의 7개 원자료 배열을 대조한다.
- [ ] 분석/기록: 센서 지원·유한값·읽기 불변성·DOF type/단위·동일 움직임 여부를 검수하고
  Luna가 이미지·설명·변경 파일 줄 번호를 남긴다.

초기 q/기타 +5mm 초기 p/q/고정 LA/PD·effort·solver/몸통9·손가락42·C02 하체 목표와
주요66 연결을 유지한다. 자유 기타·fixed human root 조건과 기존 PALM_RATE 계산,
±0.15rad 보정/기준±0.3rad box/0.02rad update 제한을 그대로 둔다.
환경의 scene 생성 후 prepare_sim 전에 enable_actor_dof_force_sensors를 호출한다.
추가 초기화 step·매 step pose/state 재주입·제어 보정·기타 복원력은 없다.

매 완료 physics step에서 get_actor_dof_forces의 float32 값을 복사한다. Step0은 측정하지
않으며 null/미측정으로 구별한다. 원자료 시점은 완료 step1..120이고 target은 직전 제출값이다.
읽기 전후 human/guitar body·DOF state, 목표와 PD properties가 같은지 확인한다.
지원 false/형상 오류/nonfinite 값은 실패로 보존·중단하고 다른 actuator로 전환하지 않는다.
모든 센서값이 0인 결과도 가능하므로, nonzero를 성공 gate로 요구하지 않는다.

[설치 SDK 설명](/home/ajou/yigyu/3/isaacgym/docs/programming/forcesensors.html:174)은
총 DOF force다. [API 단위 설명](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:1723)을
따라 native DOF type과 함께 기록한다. 회전 DOF는 Nm, 선형 DOF는 N이며 모터 토크·접촉력만을
분리한 값으로 부르지 않는다. AssetOptions의 문서상 sensor mode 필드는 현재 바인딩에 없다.
실제 effort cap에 가까운 값이어도 actuator 포화/PD 부족의 증거로 단정하지 않는다.

기존 환경/runner 파일을 수정하지 않고 관측 전용 subclass를 이번 독립 CLI에서만 사용한다.
Runner의 환경 생성 참조를 잠시 바꾸고 finally에서 복구하며, 재사용 제어 코드는 그대로다.
Subclass·원래 runner·설정·기준 데이터의 SHA와 실제 명령/로그를 별도로 저장한다.
결과는 docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1에 둔다.
이번 관측 뒤 새로운 PD/effort/제어권 변경은 사용자 확인 전 적용하지 않는다.
