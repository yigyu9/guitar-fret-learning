# 단일 목표 접촉·유지·이탈 측정

구현: [fretting_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/fretting_v1.py), 검사: [test_fretting_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/test_fretting_v1.py). 기존 환경·형상 helper·기록은 수정하지 않았다. 신규 native/GPU 실행과 PPO는 없다.

공개 API는 `FretTarget(string_number, musical_fret, finger=None)`, `FretContract(minimum_dwell_s, ...)`, `measure_sample(state, human_names, guitar_names, contact_row, target, contract)`, `FrettingTracker(contract, note_start_step, note_end_step).update(physics_step, measurement)`이다. 결과는 JSON으로 저장할 수 있는 사전이다.

물리 현 번호는1..6, 음악 프렛은0..22이다. 개방현0은 압현 목표가 없으며 합성 접촉·획득으로 통과시키지 않는다. 선택 손가락의 distal3 몸체 원점과 프렛 구간 중점 사이 거리는 접근 진단만 한다. 이 원점은 검증된 손끝 패드가 아니다. 이번 범위에서는 소스 손끝 mesh의 압력·접촉 형상을 추가 추정하지 않으며 해당 필드는 `None`으로 남긴다.

접촉 후보는 다음을 모두 요구한다.

- 선택한 index/middle/ring/pinky의 실제 `LH:<finger>2` 또는 `3` ↔ 기타 neck 루트 `guitar` 또는 정확한 목표 `G:fretN` 쌍이고 raw λ>0이어야 한다. thumb·다른 손가락·`_top`·프록시·기타 몸통·다른 프렛·λ=0은 통과시키지 않는다.
- 양쪽 `localPos`는 COM을 더하지 않고 몸체 원점 자세로 각각 world로 변환한다. 두 특징점 차이는0.1mm 이하이어야 한다. 기타 쪽 특징점을 현재 기타 루트 좌표계로 변환하며 입력 state/contact의 실제 스텝과 시간이 일치해야 한다.
- 특징점의 y에서 현재 여섯 유한 현의 x/z를 보간한다. 선택 현이 유일하게 가장 가까운 현이어야 하고 x 거리≤3mm, z 높이 차이의 절댓값≤3mm이어야 한다. 대상 프렛의 이전/현재 선 사이 y 구간에 양 끝 각각2mm의 고정 여유를 둔다. 접근 중점과 프렛선 경계의 접촉 허용 구간은 구분한다.

15mm 접근·3mm 측면·3mm 높이·2mm 프렛 여유·0.1mm 양측 좌표 잔차는 사전에 정한 진단 기준이다. 실제 현 압력·음정 정확도·소리 성공이나 N 단위 힘으로 보정된 기준이 아니다. 각 raw 항목의 식별자·finger2/3 이름·거리·거부 이유를 보존하며 중복 항목을 고유 접촉점 개수로 해석하지 않는다. post-fetch의 같은 스텝 query라는 사실과 CC_LAST_SUBSTEP 특징점의 정확한 내부 solver 시각 인증은 구분한다.

연속 유효 표본 N개의 dwell 시간은 `(N-1)/240`초이다. 50ms 획득 기준은 호출자가 선택한 별도 진단값이며 음악 노트의 필수 길이가 아니다. 노트 경계는 분수 스텝을 허용하고 반열린 구간을 사용한다. 인접 실제 표본 구간과 노트 구간의 교집합만 유지 시간에 더한다. 양 끝 유효·같은 목표인 구간의 누적 시간/노트 길이가 `note_contact_hold_fraction`이다. 전체 노트를 관찰하려면 시작·끝을 감싸는 표본이 필요하다. 23.2ms 노트는 유지 비율1.0이어도 50ms 획득을 만들지 않는다.

중복·역순 스텝과 잘못된 시간은 거부한다. 순방향 스텝 누락은 연속 획득을 초기화하고 관찰되지 않은 구간에 시간을 부여하지 않는다. 같은 목표의 연속 관찰에서 유효 후보가 소실될 때만 측정 RELEASE를 기록하며, 의도한 음악 종료 release라고 주장하지 않는다.

CPU9개 검사가 통과했다. 잘못된 손가락·현·프렛·프록시·λ=0, 움직이고 회전한 기타의 좌표 불변성, state 무수정, 시간·스텝·양측 witness 불일치, distal2/3 구분, 개방현0, 정확한 dwell, 분수 길이 단음, 샘플 누락·중복·목표 변경·별도 이탈을 확인했다. [실제 명령과 사전/사후 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/implementation/cpu_result_v1.json), [검사 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/implementation/cpu_fretting_v1.log)를 보존했다.
