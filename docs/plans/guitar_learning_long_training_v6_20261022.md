# 보상v6/544상태·8슬롯 왼손 장기 학습

사용자가 긴 학습을 요청했다. 현재 검증된v6/436Python으로 large1024/H32/seed7 fresh2000업데이트(65,536,000전이)를 실행한다. 이전8회 smoke를 이어받지 않는다. 제어·물리·보상·PPO/std/초기035/v14·기존성공/안전조건을 고정한다. 낮은 음성과나 정상적인 episode 물리종료만으로 예산을 줄이지 않는다.

- [x] 실행전 소스·기존v6/v5/v4 봉인·자원·저장공간/입력 및 계획을 확인한다. 새외부로컬출력경로와 재현정보를 확정하고436Python을 동결한다.
- [x] 새v6 도구를 준비·CPU/독립검수한 뒤 실제GPU 학습·checkpoint100을 실행한다. 저장장치 복구 뒤 검증된1300+700=유효2000회 경로를 완료했다. 한GPU context만사용하고 root만실행한다. 도중소스/입력변경을금지하고 원시/episode/성분/자원/무결성·정상close를검증한다.
- [x] 초기/500/1000/1500/final checkpoint를 동일1024환경 첫곡으로 별도 고정평가한다. 전체/안전곡·각손가락/음·단계·자세/목표한계·물리종료를 분리분석한다. 실제비사용손가락/관절쏠림과v5개선prior·입력효과를혼동하지않는다.
- [x] 평가한 학습모델 중 전체1024 평균달성→안전완주수→최신순서로 선정하고 초기대비를별도보고한다. 좋은모델또는마지막의 실제GPU pose로전신·왼손영상과자세분석을 저장/QA한다.
- [x] 전체raw CRC/전이/3331/finite/model·Adam·source/입력/원본보존·nativeexit를독립검수하고 보고서·현재문서를갱신/보관·결과봉인 후사용자에게보고한다.

프로젝트SSD available약4.8GiB로부족하여 로컬보조디스크 `/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v6_long` 아래새학습결과를저장한다(여유약1.7TiB). 계획·도구·소스동결·통합분석은새docs phase에둔다. 외부출력은별도manifest로봉인/절대경로연결하며기존결과를삭제/변경하지않는다. 도중3GiB disk경고/2GiB중단floor,host4GiB 및postcache GPU1GiB기존floor·NaN/SDK에러/수집정지등기술문제는원자료보존후복구한다. JSON은기존localDragon4,Isaac先import,GDB신호추적을유지하고FPmask변경은하지않는다.

## 외부 저장 장치 EIO에 따른 복구 변경

첫 main restart1은1362 optimizer 후status.tmp EIO로 중단되어report/정상close가미확인이다. 원본은보존하고전체bytes/SHA복사본을로컬ext4에만든다. 검증된checkpoint1300과rawprefix1300을기반으로strictresume700을새출력에실행한다. 유효1300+700=2000/65,536,000전이를목표로하며이후62회/부분수집은lostbranch로분리한다. 물리상태는새곡reset이므로연속fresh실행으로표현하지않는다. 초기/500/1000은oldcopy,1500/2000은resumerun의actualoptimizerupdate로평가한다. 봉인은로컬복사·새resume·명시relocation증거를포함한다. 원본외부디스크의복구/재마운트/삭제는하지않는다. Git키2개최종원복의무유지.

추가운영복구: 첫local700이5업데이트후Git tmp4.69GB증가로diskguard중단. report/1305failure checkpoint보존·유효학습에합산X. 해당phase큰복사/학습/평가3디렉토리를.gitignore에추가하고고아tmp2파일RAM검증보관후unlink/Git연결성exit0확인. 새train_resume700_restart1에서1300부터700실행,정확restore확인. 디스크/메모리floor유지,완료후RAM캐시정리및Git임시키원복필수.

## 완료 검산

실제 학습·5고정평가·실제자세분석·선정500모델 전신/왼손 영상·문서 최신화·임시자원 원복을 완료했다. 독립 검수가 로컬1511파일/3,379,865,794bytes 전체SHA·활성/동결436소스·별도외부봉인/alias·현재문서pins를 확인했다. phase/result_manifest.json SHA `d80cb90248e0a7ce80d694879229a69dd5f946dc06e0cdaa67e156624c65757c`. 봉인 뒤 phase 추가/수정0이며 이 체크리스트만 phase 밖에서 완료 표시했다.
