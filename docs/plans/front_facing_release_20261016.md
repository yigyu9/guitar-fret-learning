# 새 정면 자세의 왼손 완전 이탈15초: 조건부 실행 계획과 API

현재 단계는 계획뿐이다. Python 초안·해제 source 출력·native 실행·인증 파일을 만들지 않는다. 새 정면 source9는 아직 실제 준비 후 정지5초와 동일 반복의 성공 reference가 없다. 두 실제 검증이 완료된 뒤 root의 구현 지시로 진행한다. 과거 grounded 자세의 정지·연주4case·해제15초 성공은 새 자세에 상속하지 않는다.

기존 자료와 저장공간 정리 audit는 동결한다. 예정 구현 소유권은 `stability_adapter_2/front_facing_pose_v1/release_prepare_v1.py`, `release_runtime_v1.py`, `release_run_v1.py`, `release_analyze_v1.py` 네 새 파일뿐이다. 아직 존재하지 않는 경로이며 현재 native/analyzer의 package glob이 미완성 코드를 소비하지 않도록 구현 시점을 root와 맞춘다. source/runtime/recording 등 기존 소비 파일을 수정하지 않는다.

## 1. 선행 의존성과 실행 순서

1. 새 candidate와 그 실제 config로 준비0..5초·정지5..10초를 통과한다. 실제 정면 heading·기타·몸통·가슴/상완·발·발바닥·유한 제어·원물성·입력SHA 기준을 모두 유지한다.
2. 같은 설정으로 별도 실제 반복을 통과한다. 두 실행의 상태/접촉/노력/목표4종 raw SHA가 exact이며 두 실제 분석의 모든 gate가 참임을 확인한다. 새 phase의 정지 반복 인증은 이 두 실행과 실제 분석, candidate/config SHA, 입력SHA를 연결한다. 과거23개 gate 개수나 옛 reference 이름으로 대체하지 않는다.
3. 이 두 실제10초 상태를 입력으로 새 해제 preflight를 만든다. 41점 source 도달 검증을 통과한 뒤 독립 검수를 받는다.
4. 새28초 실행을 새 출력 경로에서 수행한다. 통과 뒤에도 독립 초기화한 해제 시험이라는 범위를 유지한다. 새 정면 자세의 압현/타현 또는 연주 종료 상태에서 바로 해제하는 연속 수행의 성공은 별도 검증 사항이다.

새 정지/반복의 실제 경로와 인증 schema는 root가 확정한다. producer는 config/reference/repeat/certificate 경로를 명시적 입력으로 받아 연결을 검사한다. `source9`라는 이름 자체를 성공 근거로 삼지 않으며 실제 검증된 candidate SHA가 일치해야 한다. 아직 유효한 reference가 없으므로 실제 경로·SHA나 개방 active 축 수를 이 문서에서 만들어 넣지 않는다.

## 2. 예정 producer API와 사전검사

예정 API는 `release_prepare_v1.main(config, reference, repeat, repeat_certificate, out)`이다. 별도 출력 디렉토리에 `release_spec.json`, `report.json`, `inputs_before.json`과 새 해제 config를 생성하는 구성을 검수한다. producer의 source-only eligibility는 actual 해제 성공과 구분한다.

기존 `grounded_guitar_release_v1.prepare_v1`의 실제10초 상태/FK replay/41점 solve와 개방축 선정 절차를 새 reference로 재계산한다. 기존 prepare_v2는 옛41점을 복사해 끝점만 늘리는 도구이므로 새 자세에 사용하지 않는다. 다음 정보를 새로 계산한다.

- 실제10초 `L_Wrist` world 위치·회전, 실제10초 기타 회전으로 변환한 `[0.08,0,0]m` world 이동. 경로는 한 번 world로 고정하고 기타를 따라붙이지 않는다.
- 10..13초41점의 왼팔12축 IK. 원범위·q_ref±0.8rad·principal160°·float32 엄격 범위, 위치2mm/회전0.02rad의 source gate를 유지한다. 실제10초 전체 FK 재현 오차도 기록하고 기존 좌표 한계로 실패하면 숨기거나 허용오차를 늘리지 않는다.
- 원 가중치로 손가락14축을0.3rad 개방하고 원범위로 clip한 float32 최종 목표. 새 실제2396step 최종 명령과의 차이가0.02rad 이상인 축을 active로 사전 선정한다. 제외 축과 이유도 공개한다. 옛11개 active 축 목록을 복사하지 않는다.
- 개방 판정은 실제10초 대비 signed 변화가 `min(0.10rad, 기대 명령 개방량의50%)` 이상인지13..28초의 모든 표본에서 확인하도록 사전 고정한다.

원 `motion_v1.solve_wrist`, `smoothstep`, `WEIGHTS`와 parameterized Motion의 실제10초 포착 논리는 재사용할 수 있다. 하지만 spec의 실제 좌표·참조SHA·41점 근거는 전부 새로 만든다. 실제10초의 영범위8축 등 solver drift는 별도 진단으로 보존하고 clamp/reset/사후 epsilon으로 없애지 않는다. 새 명령26축의 엄격 범위 검사는 별도 유지한다. source 손목 도달과 손가락 scalar 개방은 손끝 mesh 무접촉 인증이 아니다.

## 3. 예정 runtime와 wrapper 계약

예정 protocol은 `front_facing_prepare5_hold5_withdraw3_free15_v1`, 총28초다. 준비0..5초·정지5..10초·개방10..11초·손목 이동11..13초·완전 이탈13..28초를 사용한다. 해제 동작은10초에 시작하지만 완전히 떠난 뒤의 검증15초는13..28초다.

`release_runtime_v1.Scene.command`는 Motion으로 왼팔12/손가락14 목표를 적용한 뒤 FootScene.command를 한 번만 호출한다. 오른팔 world12 IK/material task·Chest task·Hip bias와 새 front 발 heading IK는 계속 실행한다. 타현용 오른팔 latch는 추가하지 않는다. 현재 front runtime1의 protocol 고정 init을 그대로 호출하거나 옛 release runtime2의 grounded Controller로 돌아가면 안 된다. 새 release Controller는 runtime18의 동일 유한 제어 초기화를 호출하고 front의 heading 기준/초기값을 명시적으로 설정하며 기존 front `apply`를 재사용하는 구성을 우선 검수한다. 기존 클래스를 수정하거나 protocol을 몰래 바꾸어 인증을 우회하지 않는다.

`release_run_v1.main(config,out)`은 새 source/target/right-goal/Hip-bias 보고서와 spec을 candidate SHA에 연결하고 새 정지·반복 인증과 해제 preflight를 요구한다. 옛 `play_verification_v1.json`은 실행 조건이나 새 자세 성공 근거로 사용하지 않는다. 대신 이 새 계획에 따른 정지+반복 통과를 선행 조건으로 명시한다. 현재 모든 원 gain/cap/rate와 유한 명령·원105채널/영범위8축을 유지한다.

새 front의 실제5fps String→Gym 두 층 recorder와 compact raw JSON을 재사용한다. 물리240Hz·목표60Hz·카메라 행렬30Hz와 모든 수치/필드/배열 순서는 유지한다. 재생 프레임 끝점 길이와 실제28초를 구분한다. wrapper/provenance는 새 front phase에만 저장한다. 실제 읽는 모든 코드/config/보고서/spec/입력 map/정지와 반복 raw/원 XML 및 모든 선언 mesh를 사전·사후 SHA로 닫는다.

## 4. 예정 분석과 통과 기준

`release_analyze_v1.main(run,out)`은 새 실제 정지 reference와 첫10초의 상태/접촉2401행·노력2400행·목표600행을 exact 비교한다. 2400step의 첫 해제 명령은 목표 prefix에서 제외한다. 실제 전체6,721상태·6,720노력·1,680목표가 연속이어야 한다.

새 front `analyze_v1.lower_math`의 실제 q/qd/목표/질량·원 관절별K/D를 이용한 stable-PD 재구성을 모든6,720행에 적용한다. 옛 native12의 q_ref/config exact 가정을 가져오지 않는다. 일반 right-goal 산술·Chest 산술 helper는 실제 모든 행을 평가하고, 기존10초 duration predicate는 원 결과를 남긴 채 새28초 길이 검사로 명시적으로 대체한다. 원 cap/zero8/POSITION48 명시 노력0·원물성·Root/좌석 고정·금지 호출0·cleanup 오류0·입력 불변을 검사한다.

전체 기타 이동30mm/회전5°·넥3°·좌우20mm, 몸통5°/오른3°·Spine5°를 유지한다. 가슴+오른상완 동시 지지는5..10초와10..28초 각각95% 이상, 양발은1..28/5..10/10..28초 각각95% 이상이어야 한다. 마지막1초 네 발바닥의 기존 전체 높이/기울기/속도/미끄럼 기준도 유지한다. 새 정면 기준의 실제 발4/Torso/Spine/Chest/Head heading은5..28초5° 이내, 초기/제출 목표2° 기준을 유지하도록 새 분석에서 명시한다.

완전 이탈13..28초의3,601개 표본 모두 왼팔/왼손 모든 named body와 실제 물리 기타의 양의 접촉이0이어야 한다. 실제 손목은10초 대비 매 표본60mm 이상 이동해야 하며 새 사전 선정 active 손가락 축은 signed 개방 기준을 매 표본 만족해야 한다. 비활성 충돌쌍의 무접촉을 전체 source 형상 비겹침으로 설명하지 않는다. body/관절 상태와 실제 접촉을 검사하며 source-only 도달·요청 목표로 성공을 대체하지 않는다.

Root만 고정하고 하체는 유한 제어다. 기타는 자유 강체·중력ON·스트랩OFF를 유지한다. 기타 직접힘·고정·강제부착·매step 상태 덮어쓰기·새 PPO는 사용하지 않는다. 실패 시 기존 입력/코드/출력을 그대로 보존하고 새 버전으로 원인을 분리한다. 현재 이 단계의 실제 성공이나 source eligibility를 주장하지 않는다.

- [ ] 새 정지와 반복 actual 인증 확보
- [ ] 새41점/개방 선정 producer와 명시적 입력 계약 검수
- [ ] 새 runtime/wrapper/28초 분석 구현 및 CPU 검사
- [ ] 실제28초 해제·13..28초 완전 이탈15초 검증
- [ ] 독립 검수·영상·실패/한계·보존 감사
