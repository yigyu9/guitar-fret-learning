# 전환 경로 장시간 학습

사용자 요청: 길게 학습을 진행해줘. 직전 구현한 첫 두 음 경로를 기준으로, 성공자료 확보→BC→교사 없는 실제 평가→fresh PPO 순서로 진행한다. 기존 봉인된 코드/결과/실패 기록은 보존하며 새 코드와 새 결과 디렉토리를 사용한다.

- [x] 실제 손/기타 좌표 및 접촉에 따른 접근 보정 교사, 기존 native probe 연결. 원 gain/bounds/rates/안전/성공 판정 유지.
- [x] CPU 검사·별도 검수·소스 봉인 후 단음 A/B 실제 도달·유지·해제 확인. A100%유지/해제통과, B0%실패보존. 새source30파일snapshot_v2, CPU추가10+6검사통과.
- [x] 성공자료 BC, 동일 task의 교사 없는 native 성공 평가4개 확보. 불성공 자료는 채택하지 않음. BC2kstep, 독립A4/4통과, 반복reset평가SIGFPE는제외.
- [x] 자원·처리량에 맞춰 최대4시간/128update를 우선 예산으로 장시간 PPO 실행, 중간 저장·진행 로그 확인. training_v3 N8/H240에서최소2update/3840전이committed/16episode안전완주. 코드/설정동일재시도이며장기완료는아직아님. startupv1보조XML분류오류수정, startupv2의JSON구간SIGFPE미재현/원인미확정은별도보존.
- [ ] 실행 설정/학습 여부/실제 결과/남은 제한을 정리. 진행 중인 실행은 완료로 보고하지 않음.

담당: contact_teacher와검사=solver worker; 자원/기존성공자료/장기설정read-only=learning worker; 새probe연결/실행/학습/문서=root; 별도change-reviewer. 서로의파일을되돌리지않는다. 새 소스는 native 실행 전에 동결하고, 이후 수정은 이전 내용을 archive/snapshot으로 먼저 보관하고 새 실행 디렉토리로 진행한다.

## 중간 평가에 따른 수정

- [x] training_v3 실제10update/19,200전이 반영 후 checkpoint8 결정론적 nativeclean0% 확인. SIGINT 정상 중단, 진행816전이 제외·원자료·모델 보존·입력변경없음 확인.
- [x] 고정 BC 참조 Actor와 latentmean0.0002 제한 정책 신규3파일/9CPU검사/별도검수/33소스봉인. 기존30변경0.
- [ ] 새 초기 정책의 교사 없는 native4회 검증 후 fresh PPO 재시작.
- [ ] 새 중간 모델 실제 평가를 통과하면 장기 학습 유지; 안정성/압현 퇴행은 따로 보고.

- [x] 새 정책 실제 초기 평가 v1/v2/v4/v7 모두 통과. v3/v5 SIGFPE는 제외. 관찰 wrapper v6는 진단용이므로 gate 제외.
- [ ] anchored_training_v2 동일설정 재시도 확인: v1은CPU JSON입력감사 SIGFPE/PPO0. GDB첫fatalstop·실제exitcode·매update저장으로 실행. 원인미확정, FPU/물리변경없음.

- [x] anchored_training_v2 actualPPO1/1,920committed/8안전episode 확인. 첫 actualcheckpoint 출력/포화 진단과4/8native평가 진행 중.

- [x] 첫actualcheckpoint 포화없음/selectedActor변경/frozenprior·RHS불변확인.
- [x] 4·8update 결정론적native 평가 모두 clean100%/해제/안전통과.
- [x] 실행·로그·제한·원자료보존 정리. 현재activev2 10update/19,200committed; 최대128/4h 장기 실행은 계속 중이며 완료로 표시하지 않는다.

## 최신 상태: 2026-10-19 08:39 UTC

- [x] 사용자 결과 질문에 따라 checkpoint20 새 실제 평가. clean81.6667%<90%, 약91.7ms 지연, 해제·물리 안전 통과.
- [x] 실패 확인 뒤 학습 부모에SIGINT만 전달,23update/44,160committed/96discarded/184안전episode로 종료. 학습 탐색 성공57/184. cleanup·입력변경0, 전체초기화sourceunchanged.
- [x] README 최신상태를 중단으로 갱신하고 원결과와 checkpoint4/8/20·BC·복구모델 모두 보존. 128update 완료로 주장하지 않는다.
- [ ] 후속 구현/재학습은 아직 진행하지 않았다. 권고: 탐색량별도조절, 음시작전 접촉준비/여유보상, 실제접촉기준 업데이트검증.
