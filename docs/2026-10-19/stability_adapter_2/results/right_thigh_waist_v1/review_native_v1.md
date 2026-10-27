# 실제 정지·팔꿈치 시험 독립 검수

요약 판정: **문제없음 — 기록·명령·영역 분류의 검수 범위에서 승인**. Critical 0 / Warning 3 / Suggestion 0. 기타의 원래 자세 유지, 무왼손 지지, 지속적인 두 블록 지지나 연주 성공을 인증하는 판정은 아니다.

## 확인한 범위

- `native_static_v2`와 `native_elbow5_v1`은 각각 5초·1,200 physics step·300 control tick을 완료했다. 전체 초기 상태와 2.5초까지의 trace가 정확히 같으며, 팔꿈치 목표만 ±5°로 다르다. 실제 native scalar 각의 왕복 범위는 10.09574359°이고 정지 조건 대비 같은 시각의 추가 기타 바디 중심 변화/회전은 최대 0.154754mm/0.148812°다. [비교 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:182)
- 정지 조건의 종료 바디 중심 이동 11.637343mm·SO3 회전 5.145395°, 최대 11.830772mm·6.094686°, 2→5초 순변화 1.012942mm·0.384579°를 raw trace에서 재계산했다. 동작 조건의 종료값은 11.660411mm·5.216609°다. 바디 중심은 기타 root나 COM과 구분한다. [계산 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:138)
- 두 조건의 2,400개 명령 행에서 목표/속도, 점 힘 요청 제한, Jᵀ 토크, 이전 task 감산·교체, 저장된 COM Jacobian 기반 몸통 중력보상·PD, 모델 제한, 최종 33 EFFORT/48 POSITION 범위 및 tracking 최종 벡터를 대조했다. 몸통 요청 재계산 오차는 최대 7.11e−15Nm였다. 왼팔 내부 항 전체를 이번에 별도로 다시 유도한 것은 아니며, 최종 합산 벡터와 기존 보존된 제어 경로를 확인했다. [최종 명령 검사](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:94)
- 실제 G:body 원점의 접촉 localPos를 endpoint 세계 pose로 옮긴 뒤 기타 root frame으로 변환하는 waist 분류를 대조했다. 두 조건 모두 1,198/1,200 표본에 waist 접촉 및 양의 raw λ가 있고 마지막 120개는 모두 해당한다. 정지 조건 양쪽 접촉 feature의 세계 위치 차이는 최대 1.77e−7m다. 이 값은 좌표 변환 검증이며 힘 인증이 아니다. [분류 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:25)
- canonical 분석과 직접 raw 입력 SHA를 대조했다. 과거 전체 inventory 재감사와 최종 그림·문서·보존 봉인은 이번 범위 밖이며 root의 후속 작업이다. 새 물리·학습 실행과 다른 파일 수정은 하지 않았다.

## Warning

1. **왼손 및 지지 부위 해석 제한.** 두 조건 모두 왼손 접촉 1,189개, 후기 120개가 양의 raw λ를 포함한다. 실제 부위는 `LH:middle2/index2/pinky3`이며 엄지가 아니다. Thorax는 presence 72/positive 33이지만 후기 0이고, 상완은 1,189/positive 1,178·후기 120이다. 따라서 무왼손 유지나 지속적인 Thorax–상완 두 지지를 주장하지 말고, 소비된 이전 엄지 표기는 최종 설명에서 정정해야 한다. [후기 접촉 집계](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:168)
2. **waist 접촉과 성공 범위 제한.** 판정 구간은 +15mm flank이며 좁은 +5mm core와 다르다. raw λ>0은 Newton 단위 접촉력이나 각 부위 힘·모멘트 기여가 아니다. 240Hz endpoint 표본은 solver 내부 전 시간 인증이 아니며, 5초와 팔꿈치 한 주기의 결과를 장기·범용 운동·연주 성과로 확대할 수 없다. [분류 범위](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:35)
3. **실패·이력의 범위 유지.** 이전 `native_static_v1`은 4.783333초/1,148 step에 기타 root 이동 0.20m guard로 중단했다. 바디 중심 95.136mm와 root 이동을 혼동하거나 회전 35° guard 실패라고 부르면 안 된다. 해당 영상 145/30=4.833333초는 물리 시간과 다르다. source1의 human mesh 35개 사전 핀 누락은 소급 보완 인증할 수 없으며, 이후 37개 핀과 실제 초기 감사는 별도 근거다. 잘못된 box helper1/source3은 fitting에 투입되지 않은 보존 이력으로 구분한다. [부분 실행 감사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/partial_analysis_v1.json:1)

## 확인 기준 SHA-256

- canonical `analysis_final_v1/analysis.json`: `e18820a56e4e896bdd27454c4b62d0b86a0fcd61ee3056e9eaea9cc133ad47b4`
- `analysis_final_v1/support_command_audit.json`: `ebc7a8093570c4f94c2859e18528303586402e3c45a173fc1c2bd055e8d04902`
- `analyze_right_thigh_waist_v1.py`: `bf19142a757641c22b099c7cadf1b87b50f78945f183489ade7f28802ac52569`
- 실행 runner `run_right_thigh_waist_v3.py`: `69e75bbe8ea30aa26e52e75b7227e1f9dde3d9d92ab7f0571bda1d46aaf06a18`
