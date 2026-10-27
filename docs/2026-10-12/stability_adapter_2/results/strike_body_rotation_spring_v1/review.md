# Body-rotation spring 최종 독립 검수

요약 판정: **문제없음 / 검수 PASS**. 실험은 **미채택**이다. 남은 Critical·Warning·Suggestion 없음.

- 실제 저장 자료는1,200 physics steps·300 controls·151 native trace/camera 표본, native24개 계약 모두 true다. PREPARE/PLAY/HOLD는49/251/0이며 source motor phase는0만 관측했다. Step196의 유일한 PD 전환은 R9 EFFORT/stiffness0 활성화와 baseline damping1.0이다. Phase1 quarter 전환은 발생하지 않았으며 `PD_switch_time_s=null`과 모순되지 않는다. Full81 requested/native properties 및 state 보존 기록이 맞는다.
- `run_strike_body_rotation_spring.py:125`의 요청1,004개(step196..1199)를 독립 재계산했다. 각 final logical goal은 같은4-step control의 전달 목표와 exact이고, `Exp(Bgoalq)rest`, 실제 relative quaternion, `log(actual⁻¹goal)` 기록 오차는0이다. B.T 계수의 float32 변환·original kp 곱·effort clipping 요청이 exact이며 R9 외72개 요소는0이다. 저장 trace와 같은 시점의125개 actual q 및 parent-relative body 회전도 일치한다. 이는 요청 식·저장 anchor의 검증이며 native force-dual 방향의 검증은 아니다.
- 기준 timed-wait-rebase의49개 PREPARE 선택 control 필드·25개 전체 native-state prefix·첫 actor observation/action exact를 독립 확인했다. 전체 PLAY/1,200-step state 동등성을 주장하지 않는다. Source policy+PI·finger21·대기 actual IK·RECOVER 이전 목표+2δ·clock/detector는 비교 기준 그대로이고 soft orientation5 cost는 포함하지 않았다.
- Raw target/physical/accepted/release/wrong은0, miss10, READY success 및 running F1은0이다. Minimum policy pick-to-READY 거리0.003836738474873432m는 성공이 아니다. 기타 위치 max/end46.353646/27.841216mm 및 SO(3) 회전 max/end46.986103/43.975283°를 재계산했고 playable region49/300 control·3/251 policy와 일치한다. Source terminal 없이5초 기록을 마쳤다.
- Native closure1,091개는 현재 파일1,089개와 exact `native/source_before` 사본2개로 해소된다. 별도 analysis7·spring audit8·native anchor5·pure math1 입력 SHA가 일치한다. 두 MP4 실제 SHA/ffprobe1280×720·151frames·30fps·5.033333초 및151×2 frame SHA/step coverage를 확인하고 종료 손 PNG를 직접 검토했다. README·CHANGED_FILES의 출처·수치·PD 전환 및 force-dual 한계 설명이 맞는다.

확인 SHA256: runner `42690ff938ab8defd2c64e9f1d78c9fbc5338ca1d4c10796bd33a503d0eff6c5`, wrapper `70d58625e22ccd158a96a0a0d7912a713fd3147585ede75d1a79525968669f48`, 분석 summary `39c9e0c21743ae888ca2e9a9282d7e5c14663ba90a7227a708cad3dc1401b76e`.

검수 중 추가 native 초기화·물리 실행은0회다. Child-Bv 동일 snapshot 근사 및 pure 회전 수학을 native effort 공액 좌표·물리 torque 방향·qdot/Jacobian·폐루프 안정성·지속 지지·전곡 연주 또는 source/native CPU/GPU 동등성 인증으로 확대하지 않는다. 후속 finger curl 및 root 최종 보존 감사의 완료를 대신하지 않는다.
