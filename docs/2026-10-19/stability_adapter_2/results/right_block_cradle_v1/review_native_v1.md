# 오른쪽 두 블록 받침 native 독립 검수

요약 판정: **기록·명령 검증은 문제없음. 제한된 관측 결과로 승인.** Critical 0건, Warning 3건, Suggestion 0건. 접촉 힘의 기여 분리·수동 집게·무왼손 유지·연주 성공을 인증하는 판정은 아니다.

## 검수 범위와 증거

권위 결과는 [native_analysis_final_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_analysis_final_v1.json)이다. 완료 정지9회와 팔꿈치2회, 각1200 physics/300 control/5초를 확인했다. 별도 고강도 몸통 실패1회는 5 physics/1 control/0.020833초이며 완료 케이스에 합산하지 않는다. source 결과6개 버전의 총14행은 거절12/수락2(source3/source7)였다. source6은 미실행 보존본이다.

[analyzer7 변경](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:168)은 후기/동작 구간 positive 집계6개와 [전체 초기 상태 exact 정지 짝 선택](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:182)이다. 기존 정지8개/팔꿈치 출력의 공통 필드가 권위 결과와 일치한다. 핵심 raw report·initial·trace·endpoint·POSITION 기록66개의 SHA를 권위 입력 목록과 직접 대조했다. 과거 전체 inventory 감사나 최종 봉인은 수행하지 않았다.

원자료에서 기타 collision BB 중심 `[0,−.4,−.055937985]`의 world 이동, normalized SO3 회전, 팔꿈치 범위·접촉 통계를 독립 재계산했다. T40 동작1200행의 목표 파형·posture·점힘·Jᵀ·body9 중력/PD·최종 모델 clipping/33권한 합성은 일치했다(몸통 요청 최대 산술 오차 7.11e−15Nm). 두 close 조건도 각각1200행의 현재G 목표/COM속도·human 점/속도·Jᵀ·body9 합성과 최종33 제출이 일치했고 point Jacobian 속도 오차 최대0.000380623m/s<0.01이었다. POSITION48 readback/상태 검사300행도 통과했다. 중력 재계산은 기록된 COM Jacobian 성분을 이용한 산술 검증이며 새 모델/물리 인증은 아니다.

최신 조건은 body9+양팔24의 **33 EFFORT/48 POSITION**이다. 초기4조건의 body POSITION/24 EFFORT를 이 범위와 혼동하지 않는다. 현재 권위 최종 vector는 body_effort_rows와 업데이트된 tracking이며 two_block vector는 body9 추가 전이다. 단일81 effort, root/하체 고정·free 기타·strap OFF·기타 외력 금지와 보고된 금지 호출0을 유지한다.

## 실제 비교 결과

| 동일 초기 상태 비교 | 실제 EL_y 왕복(2.5~5초) | 같은 시간 기타 중심 최대 추가 차이 | 같은 시간 SO3 최대 추가 차이 |
|---|---:|---:|---:|
| source3 T40 정지↔동작 | 10.123112° | 1.684942mm | 0.699958° |
| source7 close 정지↔동작 | 10.114130° | 0.071023mm | 0.031521° |

두 짝의 전체 초기 자료와 0~2.5초 trace가 각각 exact였다. source3 T40은 Thorax presence557/positive5, 동시 positive3/1200이며 후기 Thorax0이었다. 그 이전 완료 정지 조건들도 후기 Thorax0으로 지속 두 접촉 성공이 아니었다.

source7 close의 정지/동작 최종 중심 변화는 각각4.093496/4.102109mm, SO3는3.995343/3.997036°였다. 두 조건 모두 body scalar 최대0.013276711rad(0.760700°)<0.08rad, 오른 전완/distal/Head 접촉0/1200이었다. 근위 상완 raw/clamped0~30% presence1176/positive1170은 동일하며 실제 fraction은0.05699~0.06335였다. 후기 두 부위 presence는 모두120/120, 팔꿈치 파형 구간 presence는 모두480/480이었다. **동시 raw λ 양수는 정지/동작 후기88/56, 파형 구간298/223**으로 presence와 구분된다.

## Warning

- [analyzer7:117](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:117), [같은 파일:172](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:172): presence와 positive를 혼동하지 않는다. raw λ는 Newton 접촉력이 아니며 240Hz endpoint는 연속시간/solver 내부 전체 접촉 인증이 아니다. 위 counts로 지속 힘 수반 집게나 부위별 힘/모멘트 기여를 확정하지 않는다.
- [권위 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_analysis_final_v1.json): close 두 조건 모두 왼팔/손 접촉1072(positive1069), 허벅지1197(positive1196)이며 후기에는 양수120표본씩 남는다. 따라서 무왼손 또는 두 블록만의 지지로 주장하지 않는다. source7은 초기 body/right 및 보상 각도도 조정했으므로 source3 대비 변화의 원인을 Thorax 간격 하나로 분리할 수 없다. 반복 시험·임의 팔꿈치/몸통 동작·Fret/Strike·학습은 미검증이다.
- [failure_audit_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/failure_audit_v2.json): body K600/D60 실패의 실제 원인은 point Jacobian 속도 불일치다. 마지막 qdot17.159695rad/s<50이므로 50rad/s 안전 종료라고 설명하지 않는다. 부분 영상은2frame/0.066667초이며 5초 완주 영상이 아니다. NumPy bool 직렬화로 잘린 low_v1 JSON은 불완전 실패 원본이고 low_v2가 완료 재시도다. 완료 영상은151frame/30fps=5.033333초로 물리5초와 구분한다.

## 검수 SHA-256

| 파일 | SHA-256 |
|---|---|
| native_analysis_final_v1.json | f74f490846d8c2837cf4e28bad19b641a5c4fb7787ee538de6e17ce7450cf1a3 |
| native_analysis_static_all_v1.json | 3155e41305110070c0f83f1b5c4c5676f66606cda2fd678090f4bfe174fb390c |
| native_analysis_elbow_v1.json | 06610a093fc8b5e5bf72a73632fa4dde2274abb0b12d6b60a278df50adcbf4c1 |
| failure_audit_v2.json | cd17c06477416b6fc5003c722ac165b740fe33a798ed8a445a76b3da221236ee |
| analyze_right_block_cradle_v7.py | d05028ada74a9c5e4b9c854a4ed8536900742e86f5ae4ee28b4e57ccfb612c87 |

새 native 실행·정책 추론/학습·다른 파일 수정은 하지 않았다. 최종 문서·그림·보존 봉인은 후속 검수 범위이며 이 기록으로 선인증하지 않는다.
