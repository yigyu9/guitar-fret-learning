# 검지 source7 단일 평행이동 reference

root 승인 범위: 이 새 폴더의 CPU 준비만 수행한다. 원 source/teacher/reference/기존 결과와 실행 중인 B 비용초기화1267봉인은 수정하지 않는다. GPU/native는 root가 현재 학습+평가 종료 후 별도로 결정한다. 새 grid·추가 자세·학습·checkpoint 이식은 없다.

## 유일한 도달 가설

A는 source4/physical3현4fret, B는 source7/physical2현5fret/finger1이다. A112의 선택4 각도·arm12·손목 quaternion·2초 ramp를 exact 보존하고, 손목 위치만 두 원 목표 셀 중심의 `B−A`만큼 기타 로컬 좌표에서 평행이동한다. 이는 B native 실제 자세나 성공 사례가 아닌 미검증 가설이다. 새 teacher는 필수 v2 필드와 `borrowed_A_provenance`만 기록하며 A source_row/readback/success를 B 실제 기록처럼 복사하지 않는다.

셀 중심은 현 보상과 같은 press-plane에 원 `project_press_strings`로 문자열을 Gz 투영한 뒤, 원 `core.geometry_v1.fret_target`의 해당 프렛 구간 중점으로 정의한다. `load_press_surface([2,1],[4,5])`가 원 자산 SHA와 inward2mm 유한 구간/hull을 검증한다. 축은 +Gx=physical6→1현, +Gy=bridge→nut, 단위m이다. 독립 NumPy 계산으로 문자열 보간·프렛 경계·평면 투영을 재검산한다.

- A 중심 `[0.0038968968394714363,0.10297650648698872,0.0093]`m.
- B 중심 `[0.011590029626966706,0.07447299393782575,0.0093]`m.
- ΔG `[0.00769313278749527,-0.028503512549162974,0]`m, 크기29.523457mm.

유한 셀 내부·평면·각도 native/action bounds를 검사한다. Cartesian 손목 도달이나 collision feasibility를 증명하지 않으며 새 wrist bounds/clip을 발명하지 않는다.

## 원곡 의미·시계

원 `make_task`와 `spec.subset/diagnostic_spec`를 직접 사용한다. source7 audio press3.2817/onset3.4017/end4.1796, 공유 release5.1548s이다. B7의 end는 원 sustain/release 최소값4.1796이며 release로 늘리지 않는다. 단음 local press2.88/onset3/end3.7779s·음중0.7779s·257control/1028physics 상한을 보존한다. SongTask 시계는 원 audio+3s이며 trace의 `source_time_s=local+score_offset(3.4017)`임을 명시한다. 원 A의0.1703초를 복사하지 않는다.

## 최소 재사용과 검증

원 prelearning `execute/_evaluate/trajectory/cap.verify_native4`를 그대로 호출한다. `HERE/INPUTS`는 새 teacher/reference/settings만 scoped 연결하며 finally에 원 객체를 복원한다. 기존출력/상위symlink를 native보다 먼저 거부하고 exclusive 출력의 dev/inode를 확인한다. 원 cap loader/105속성·controller caps·엄지/다른89축·K/D·4rad/s·범위·90pairs·correct wristv3·보상·실패/첫4분모·장면종료/전후pin을 보존한다.

새 CPU `ShortEnvironment`로 expected B 환경 계약을 만들고 native pool의 `environment.contract`와 exact 비교한다. A full contract 동일성이나 새20Nm B 실행을 주장하지 않는다. B cost 초기화 tag/모델은 이 noNN 실행에 포함하지 않는다. B의 task/view/catalog와 target7 의미·시계를 별도 기록한다.

CPU에서는 두 기하 계산·원 A 각도/arm/quat 보존·새 teacher/ref 원 reader·B expected task·원4 native/evaluator 오류회귀·scope 복원을 검증한다. 실제 실행 후에는 원4분모/9보상/acceptance를 보존하고 env0 저장60Hz 목표/rate/nativebounds/score clock 및 wrist goal을 추가 검산한다(t0 목표·다른3환경 상세시계열은 추정하지 않음). 추가보고서만 쓰며 원 보고서를 덮어쓰지 않는다. native4 도달/성공은 현재0회이다.

독립 CPU 준비 검수와 새 입력 봉인 후 root에 인계한다. 실패 시 B 불가능으로 결론내리지 않고 실제 gate/손목오차를 보고 다음 범위를 정한다. 성공해도 A→B→B 전환·정책학습·자유 기타/J33·전곡·자연성·생산채택은 미완료이다.
