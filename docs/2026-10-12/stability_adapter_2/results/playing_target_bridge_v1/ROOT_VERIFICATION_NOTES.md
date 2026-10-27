# Root 검증 기록 — target/history CPU 하위계약

## 실제 검증과 범위

CPU checker는 session87558에서 exit0으로 끝났으며 재실행하지 않았다. 저장된10검사가 모두 true이고 입력30개 SHA 전후가 같다. 원본 Base.apply_actions AST80step×17batch와 residual0의 최대차는2.384185791015625e−7rad이며 bitwise 동등이 아니다. 최종 history 복원차는1.1920928955078125e−7rad다. Source60+Thorax6의 gradient와 held15 유지, 이름 permutation, 포화 및9개 거절 경계를 확인했다.

새 native 초기화/physics/actor 추론/학습은 모두0이다. 전체420/303 관측·task 후처리·normalization·event clock·actuator 연결은 아직 미구현이다. Source후처리 완료 action을 받는 target/history 하위계약만 검증했다. 현재 initial q와 유지 PD목표의 같은 LH6가 Fret 범위 밖이므로 warmstart를 거절하며 조용히 clip해서 actor를 연결하지 않는다.

## 평가와 해석

원자료와 계약에서 Fret47,000/.100098126,47,500/.073485598 F1을 대조했다. 둘 모두 sustain1/35이며47,000도 goal_pair/stalled다. Fret 평가 시 checkpoint 파일 SHA는 저장되어 있지 않아 현재 파일의 SHA로 당시 파일 동일성을 보증하지 않는다. Event34는 전체곡 순차 상태의15/19 target-frame 압현 기록이지 독립 reset 성공이 아니다. Strike10,000의64episode F1=1/timingp95=5.628202915ms는 현재 파일 SHA와 직접 연결되지만 single-pick 범위다.42event 영상 표본과 합치지 않는다. 네 source의 strictG0 qualification은 모두false다. 기존 자격 계약/체크포인트는 변경하지 않았다.

## 이미지 QA

Root가 playing_bridge_summary.png를 실제 열어 원자료 수치·단위를 대조했다. 왼쪽 두 Fret F1과 오른쪽 unsigned 최소 profile 이동량을 분리했고 label/범례가 막대·수치를 가리지 않는다. 도 단위 초기q/PD의 차이는 안정한 각도 제안이나 물리 반응이 아니다. 이 PNG는 CPU 저장자료의 과학적 요약이며 native render가 아니다.

결과 README와 VISUAL_REPORT의 hands 초기PNG·MP4는 이전 body9_strap_minus2mm_v1의 실제 Isaac Gym 기록을 명시적으로 재사용한다. 새 영상은 없고 모음128개를 유지한다. Luna가 생성 전 source/wrapper를 보존하고 producer를 한 번 실행했으며 입력 전후/출력SHA·명령·로그·exit0을 기록했다. Root는 artifact를 다시 생성하지 않았다.

## 다음 단계와 보존

다음 leaf 계획은 손6 초기각/유지목표만 유효 범위로 옮기고 fresh native 실제 형상에서 admission을 확인하는 새 trial이다. 기존18변수 FK 인증을 finger1 변경에 확대하지 않는다. 현재 source profile을 실제 PhysX hard limit로 교체하지 않았다. 현재 물리 유지 기준은 보존한다. 이 계획의 구현·물리 시험·연주 학습은 미실행이다.

독립 검수는 review.md에 기록한다. 이전 phase의 artifact 복구에서 원래 v1 manifest/log/metadata byte 동일성 미확인이라는 한계는 이전 기록 그대로 보존한다. 이번 phase에 그 한계를 해결했다고 주장하지 않는다. 최종 보존 감사와 입력/출력 봉인은 final_verification.json 및 artifact_inventory.json으로 기록한다.
