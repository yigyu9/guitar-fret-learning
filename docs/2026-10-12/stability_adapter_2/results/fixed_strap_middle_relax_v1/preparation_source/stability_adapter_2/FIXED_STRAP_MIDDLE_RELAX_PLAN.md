# 고정 스트랩·중지 끝 관절 목표 완화 실제 비교

직전 자연 허용 구역 재평가는26검사와 실제 저장 그림 검수를 완료해 초기 미세오차 축소보다 손가락 자세를 우선할 근거를 얻은 progress다. 질문 재설명은 새 실험 진행이 아니며 지금 다음 실제 관절 비교를 수행한다.

## 이번 한 후보

`joint_only_fixed_strap_v1/native`의 초기81관절각·기타 초기world p/q·몸통9 PD×2·고정root/하체·self-collision·물리/접촉/손목±.005rad1Hz를 그대로 유지한다. 절대LA1.1018469719600776m를 바꾸거나 초기route에 재설정하지 않는다. 사용자 지칭 다른 환경의 출처는 확인 중이며 현재 값을 모든환경공통길이로 단정하지 않는다.

LH:middle3 유지목표 offset만−0.05rad(약2.865°) 바꾼다. 기존 약60.684°에서57.820°로 목표를 펴되 초기각은 약60.146° 그대로다. 중지2·다른 손가락·어깨를 동시에 바꾸지 않는다. Float32 최종목표·모델 경계·기존relative offset±.3rad와 손목파형 두 극값을 먼저 검산한다. 변경되지 않은80관절의 실제1200목표·명령시계를 기준과 exact 대조한다.

초기 배치와 접촉 필터가 같은지 fresh native14 admission/1188 source self pair 검사 후 기존 frozen run_palm_witness_initial_diagnostic를 수정 없이 재사용한다. Source 검사와 PhysX cooked 관통·해부학적 패드 인증을 구분한다. Gate를 통과하면 한 초기화/1200step·실제0~5초·전신/손151frame 영상에 passive 스트랩 경로를 표시한다. 실패/중단은partial을 보존하고 정상완료로 표시하지 않는다.

## 검증과 다음 판단

- [ ] 새 trial/proposal·입력 closure·초기값 보존·float32 목표 검산/검수
- [ ] Fresh 초기형상/하체root·몸통목표·PD 대조 및 실제5초/두영상
- [ ] 중지3 실제각/목표오차·중지2 보존·모델한계·palm상향·접촉/self-contact 비교
- [ ] 초기30mm/5° 임시구역과2~5초의121개 완전1초창5mm/1° 평가
- [ ] 이전2초기준값과새1초창을구별한그림·초기/종료실제이미지·영상모음 추가·독립검수

임시구역 통과는 자연성/실제 fret·strike 성공이 아니다. 손가락 길이 때문에 기존 굽힘이 필수라고 가정하지 않는다. Raw λ는 접촉N으로 부르지 않으며 접촉행 수만으로 지지력을 판단하지 않는다. 8월19일 p01~p99는 soft 참고로 유지하고 공용 hard limit을 바꾸지 않는다. 개선이 없으면 현재후보를 채택하지 않고 더 큰 완화 또는 중지2와의 조합을 새단위로 결정한다.

소스/trial은 stability_adapter_2에, 로그/원자료/이미지/영상은 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1에 둔다. 실행 전 producer/helper/leaf/invocation과SHA를 보존하며 로그·명령·환경·exit와입출력 전후SHA를 남긴다. 기존 실험/공용 자산은 수정하지 않는다. 최종66 연주권한·몸통목표·자유기타를 유지하고 기타고정/손부착/지속pose덮어쓰기를 금지한다. 새controller/reward/actor/학습은 이번에 하지 않는다.
