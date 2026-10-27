# 봉인 직전의 최종 운영 기록

실제학습2000회(유효1300+700)/65,536,000전이/64,000raw행,5고정평가,저장자세분석,선정500모델전신·손영상과전체decode/시각QA,임시RAM정리/Git2키원복,5문서최신화·변경전4원문보존·독립검수를모두완료했다. 모든native/GPU/GL세션과worker쓰기는종료했다. root만이기록뒤seal_results.py를실행한다. 최종완료근거는 result_manifest.json의존재와정규파일목록/bytes/SHA·별도externalmanifest/alias 검산이다. 이운영기록은그파일생성직전작성됐으며봉인후phase파일을추가/수정하지않는다.

결과:초기3.8408203125/safe1024;평가한학습모델중best500=5.4287109375/safe414;최종2000=.7451171875/safe961. full67성공0/단계0·관절/손가락편중미해결. 두영상은best500 env0safe4음이며전체610실패를대표하지않는다. 독립완료검수: independent_final_training_review.md, independent_fixed_evaluation_review.md, independent_pose_media_review.md, independent_final_document_review.md. 4currentdoc/보고서SHA는 current_documents.json. 별도copy1387파일/4,499,049,842bytes targetseal e221dfbee9a01a6f5cbac99cef0fe5eb336f00eb2348687c1b56ff4c907689aa. source436·옛3봉인실물전체SHA도보존검산PASS.

이하실행중각시점의원운영기록이다. 현재상태로재해석하지않는다.

# 현재: 실제 실행·평가·영상·자원 원복 완료, 최종 문서 검수/봉인 중

학습유효2000/65,536,000전이, 실제5×1024 평가/GDBexit0, posture_analysis와best500전신·손영상/전체decode·시각QA완료. best500평균5.4287109375/safe414,최종.7451171875/safe961,초기3.8408203125/safe1024. 단계0/full67성공0. root모든native/GPU/GL세션회수. media_qa.json/independent_fixed_evaluation_review.md 존재. posteriorpose/media독립리뷰작성중.

finish_temporary_storage.py exit0: 자체RAM cache3,644,790,537B정리, freshgitfsckconnectivityexit0, gc.auto/maintenance.auto두임시키previousabsent로복원. temporary_storage_final.json 참조. 외부copy1387파일별도seal e221dfbee9a01a6f5cbac99cef0fe5eb336f00eb2348687c1b56ff4c907689aa. 현재4문서+phaseREADME는backendworker가최종후보작성중,닫힘/SHA뒤독립검수·최종문서manifest/로컬phase봉인까지해야완료. source436/옛v6/v5/v4전체실물SHA preservation_final.json PASS.

# 현재: 학습 검산 완료·고정 평가 진행

유효1300+700=2000업데이트/65,536,000전이/64,000raw행 최종검산·analysis_final·독립검수 PASS. recovery_verification.json은 relocated manifest f543...사용. 실제5평가 native unifiedsession46672 진행중, 실행순서2000/0/500/1000/1500. combined recovery_checkpoint_evaluation.json 생성까지 기다린다. final2000 평균0.7451171875/safe961,initial0 평균3.8408203125/safe1024. 아직최고모델확정X. 이후CPU자세/OSMesa전신·손영상(root만native)·독립검수·5문서·RAM정리/키원복/별도봉인필수. backend worker는5문서쓰기준비만하며root신호전쓰기X.

# 학습 종료·최종검산 단계

active train_resume700_restart1/native1709267/session66574는2000optimizer에정상exit0. report completedtrue/stoppedupdates_complete/trans22937600/failureNone/cleanup_errors[]/changed_inputs[]/missing_import_pins[]/lifecycle_verifiedtrue/wall8175.392568s. oldvalid1300+new700=2000이며검증대상64,000행/65,536,000전이. 지금fullCPU verify_recovery session실행중, outfile recovery_verification.json/log. 원본old정상close/EOF는주장X.

다음: 새fullverificationPASS후새eval evaluate_recovery_checkpoints.py --prefix /home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/recovered_train2000_restart1 --resumed <phase>/train_resume700_restart1 --copy-manifest <phase>/recovery_copy_relocated_manifest.json --verification <phase>/recovery_verification.json --out <phase> --tag recovery. ROOT만GPU/GDB/Isaac先import. CPUanalyze_recovery동일old/new/copy + --verification fullJSON --plots --out <phase>/analysis_final. 이후pose분석/전신·손영상/독립검수·문서/자원원복·봉인해야완료.

필수원복/정리: RAMsnapshot2 cachebackup /dev/shm/guitar_learning_orphan_git_backup_20261022_snapshot2 내onlytmp_pack_TPNfCE3,644,790,537bytes를Gitconnectivityexit0/SHA확인후마지막에정리. gc.auto/maintenance.auto는임시0/false인경우이전없음으로localunset;나머지config안건드림. copy원자료outside4.5GB는별도manifest로봉인(1387파일집합안에파일추가금지),localphase는symlinktarget포함오해없이별도봉인. source436/기존v6/v5/v4봉인검증/4maindocs갱신·독립검수필요.

# 저장 경로 최종 변경(활성 학습은 유지)

mainPID1709267/session66574,감시25777 그대로global1471이상진행. 중간복구analysis_prefix1400 검산/분석PASS(45,875,200전이)·원결과불변. 자동Git snapshot이이미캡처한oldcopy를재독하여새tmp_pack_TPNfCE를만든것을lsof실제PID1718504(parentCodexapp8138)에서확인했다. PID는자연종료했고kill실행없음.

oldcopy만같은SSD의 durable **/home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/recovered_train2000_restart1** 로atomicrename(lsof0/sameFS/동일inode)·원project경로symlink유지·1387파일4,499,049,842bytes SHA재검증했다. active train_resume700_restart1은옮기지않음. active기존checkpoint alias핀SHA동일확인(alias_preservation_check.json). 원manifest/reports유지, 새 **recovery_copy_relocated_manifest.json** SHA f543902c7b267271d6b22bc0f4ed84b3629f66bfd6c595c693c6af6138ba3306/parent원manifestSHA포함.

앞으로 verify/analyze --old-run,eval --prefix는위durableoldcopy절대경로, **--copy-manifest recovery_copy_relocated_manifest.json** 명시. --run/--resumed는현재active새run. 기존proof는옛경로/SHA이므로자동재사용X,새--out proof를만든다. 외부prefix데이터는별도manifest로최종봉인(immutable복사본안에새파일추가X)하고localphase봉인은symlinktarget파일을포함했다고오해하지않게분리한다.

RAM first2cache6,833,319,766bytes는SHA재확인+Gitconnectivityexit0기록후정리(ram_git_backup_released_1.json). 새closedTPN캐시1개를RAM검증보관후원tmp만제거해현재로컬6.7GiB/native중MemAvailable12.7GiB확보. ram_git_backup_snapshot2_manifest.json과사전unlink기록보존. 최종정리필수RAM경로 **/dev/shm/guitar_learning_orphan_git_backup_20261022_snapshot2** (onlytmp_pack_TPNfCE,실제훈련자료아님). 새연결성검사후마지막정리. .gitignore copyalias의끝slash를제거해symlink도정확히제외했다. 유효git객체/refs/index수정X. 이전RAM상태문구는이맨위상태가우선한다. 최종git자동설정키2원복의무그대로.

# 활성 실행: train_resume700_restart1

GPU nativePID1709267/unifiedsession66574,감시session25777. 새로컬run `train_resume700_restart1`, native log `train_resume700_restart1_gdb.log`,watch log `watch_training_resume700_restart1.log`. 전체모델/RNG/optimizer/3331을oldcheckpoint1300과metadata제외정확복원함(resume_restart1_restore_check.json),재개6회이상실제GPU업데이트진행. 소스436/물리/보상/PPO·std불변. 기록전체유효1300+새700=2000. 실제최신값은progress.jsonl에서 **run이train_resume700_restart1인행만** 읽고optimizer_updates는이미global이다.

프로젝트free약7.2GiB/native중RAMavailable약9.9GiB,기존host4GiB/GPU1GiB/디스크2GiBfloor유지. RAM에고아캐시6.83GB가있으므로이전프로세스RAMfree16GiB와차이를native누수로해석하지않는다. .gitignore3pattern적용/연결성검사exit0기록 git_connectivity_check.json.

완료후필수: actualGPU700정상close/새report+raw/3331/restore검산→5고정평가(0,500,1000oldcopy/1500새local199/2000새final)→전신·손영상/자세분석→독립검수·4문서갱신→RAM고아캐시백업정리(실제자료X)와gc.auto/maintenance.auto두임시키원복→로컬결과봉인/모든파일SHA확인. 최종평가명령의--resumed,verify/analyze의--run은위새run절대경로명시. 첫13/old62/첫resume5(총80optimizer업데이트)와partialraw는보존하고유효2000에합산X. 이전문구보다이맨위상태가우선한다.

# 운영 변경2: 로컬 저장 공간 복구 완료·새700 준비

현재GPU학습없음. 첫local train_resume700은GPUstrictload+5업데이트(optimizer1305)후diskguard로중단됐으며report정상기록/completedfalse/cleanup_errors[]/journal160rows·163840전이closed/미반영0/failure_last_valid.pt1305보존. first_resume_restore_check.json에서old1300→initial1300 metadata제외모델·두optimizer·RNG·cur3331전체exact일치확인. 이5업데이트는별도중단분기보존하고최종유효집계에합산하지않는다.

복사raw가Gitignore되지않아같은시각에새4.69GB tmp_pack가생성되어SSD가883MiB로급감했다. .gitignore에해당phase recovered_train2000_restart1/train_resume*/evaluation_*_1024 세경로만추가/이전원문보관/check-ignorePASS. 사용중아닌tmp_pack_LiHwdn와lcis9h두개(총6,833,319,766bytes)를RAM(/dev/shm/guitar_learning_orphan_git_backup_20261022)에전체source재독/backupSHA/fsync/lsof2회/inode-size-mtime불변검증백업후원tmp만제거했다. 유효Gitpack/idx/keep/refs/index는변경X. ram_git_backup_manifest.json/사전unlink기록과도구/독립검수보존. RAM백업은휘발성캐시사본이며실제학습원자료의영구백업이아니다. native없는현재MemAvailable약14.3GiB/로컬SSD여유약7.3GiB. 끝난뒤Git연결성검사결과를확인하고RAM고아캐시사본정리의무.

새활성예정경로 train_resume700_restart1, 동일검증oldcheckpoint1300→새700으로1300+700=2000을완료한다. native/보상/source436변경없음. 모든복구분석·평가도구는 --run/--resumed로새경로를명시한다. 기존62·첫13·이번5분기는보존/유효2000에합산금지. 학습종료후Git임시gc.auto/maintenance.auto두키원복필수(아래기록).

이하이전기록:

# 운영 변경: 외부 디스크 EIO 복구 중

활성 학습은 현재 없다. main session61406/PID1554441은 optimizer1362 후 다음 수집의 monitor status.json.tmp EIO로 exit1. 최종report 없음/정상close 미확인. 감시46632도 외부파일 stat EIO로 종료. 원로그를 보존한다. GPU compute process가 없음을 확인했다. 외부 FUSE/NTFS는 ro이며 하드웨어 원인은 확정하지 않는다. 재마운트·수리·원본변경은 하지 않는다.

source436/원학습입력조건은 그대로다. 전체 원run을 이 phase/recovered_train2000_restart1로 bytes/SHA/fsync 검증 복사 중(session35350/recover_copy.py/recovery_copy.log, 최종 recovery_copy_manifest.json). 로컬 ext4 여유 약11.5GiB를 사용한다. checkpoint_001299.pt(actual1300)를검증한 뒤 새 train_resume700에 strictresume하여 유효1300+700=2000·65,536,000전이를 완료한다. 원본1300뒤62업데이트와부분수집은lost branch로별도보존/합산금지(정확raw수는후속검산). 물리상태/부분곡은새준비자세에서다시시작하므로연속fresh2000이라고주장하지않는다.

root만실제GPU/GL/CPU분석main. backendworker는새verify_recovery/analyze_recovery/test, controllerworker는새evaluate_recovery_checkpoints/test와renderer최소schema, reviewer는독립검수. 기존도구/결과는사본보존후새버전. 현재source/원pins를수정하지않고copymanifest로검증된역사run파일만명시relocate하여읽는다.

아래는 이전 운영 기록(현재 진행 중이라는 문구는 위 상태로 대체):

# 보상 v6 장기 학습 운영 상태

## 진행 중

- 승인된 예산: 현재 v6, large1024/H32/seed7, fresh2000 업데이트(65,536,000전이), checkpoint100. 학습 중 소스·입력·보상·물리 조건 변경 금지.
- 활성 실행: `/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v6_long/train2000_restart1`
- GPU 학습 unified session61406 / native Python PID1554441. 로그 `train2000_restart1_gdb.log`. 현재1000회 완료(중간 표본); 최종값은 실행 원자료를 확인한다.
- 감시 unified session46632 / `watch_training_restart1_final.log`, 기록 `progress.jsonl`. PID 시작시각·실행 경로 확인 후 로컬/외부 디스크 중 하나라도2GiB 미만이면 해당 학습에 SIGINT 한 번. 새 guard 기록은 실행명별 파일로 분리한다. 정상 실행은2000회까지 유지한다.
-436Python 동결: `training_source_manifest.json`, 사본 `source_training/`. 실행 전 기존 봉인 검증은 `before_manifest.json` 참고. 실제GPU/GL은root만 실행한다.

## 중단된 첫 시도: 성과에 합산하지 않음

- 외부 `train2000`, `train2000_gdb.log`, `disk_guard_event.json`, `progress_interrupted_attempt1.jsonl` 보존.
- 오래된 임시 git pack 증가로 프로젝트 SSD 부족, disk guard SIGINT. optimizer13/committed425984, 수집했으나 PPO 중단된32768전이는 discarded. `initial.pt`만 유효하고 resume 미검증이므로 새 실행을 처음부터 시작했다. 물리·수치 실패로 분류하지 않는다.
- `analysis_interrupted_prefix13`은 progress 실행 경로 필터 수정 전 결과라 디스크 통계가 다른 실행과 섞일 수 있다. 보존하되 후속 `_v2`로 대체하고 장기 성과에 합산하지 않는다.

## 저장 공간 복구와 반드시 할 원복

- 미사용·미개방 오래된 `.git/objects/pack/tmp_pack_*`8개를 외부 `orphan_git_tmp_pack_backup/`에 복사/fsync/SHA 검증 후 임시 원본만 제거했다. 총12,615,505,504bytes. 유효 Git object/refs는 변경하지 않았다. `storage_recovery.json` 및 외부 backup manifest 참고.
- 프로젝트 여유 약12GiB, 외부 약1.7TiB. 실제 여유는 `progress.jsonl` 최신 표본으로 확인한다.
- **완료 전 필수 원복:** `git_maintenance_before.json`에 저장한 키만 복원한다. 이전 `gc.auto`와 `maintenance.auto`는 모두 없음; 임시값은 각각 `0`, `false`. 여전히 임시값일 때에만 해당 local key를 unset하고 검증·기록한다. 전체 `.git/config`를 덮어쓰지 않는다.

감시 보완: GPU 조회 timeout10초, 기록 실패와 무관한 diskfloor 신호 처리를 독립 mock4경로로 검수했다. 이전 감시만 PID1556310 확인 후 SIGINT로 교체했다. 학습 PID1554441은 유지했다. 이전 감시 session8933은 종료됐다.

## 남은 작업

1.2000회 GPU 학습 정상 완료·raw/전이/checkpoint/종료·자원 검증. 검수 완료 CPU 분석 도구로 prefix와 최종 분석. 필터 수정본 analyzer SHA8560e8950f0d6f052e1e28c8509910a07c738969132cfb89ba7e5a658b6d856a.
2.초기/500/1000/1500/2000을 동일1024환경 첫 곡으로 고정 평가. 초기 포함 각 모델 env0..7의 실제 pose 저장.
3.평가한 학습 모델 중 전체 평균 달성음→안전 완주 수→최신순 선정. 전신/손 영상·실제 MCP/PIP/DIP 및 대기 손가락 자세 분석. 초기 모델은 별도 기준값.
4.원자료/영상/결과 독립 검수, 미리 보관한4개 현재 문서 갱신, 임시 Git 키 원복, 외부·로컬 결과 봉인 및 무결성 확인.

계획: `docs/plans/guitar_learning_long_training_v6_20261022.md`. 낮은 점수나 자연스러운 episode 이탈만으로 학습 예산을 줄이지 않는다. 소스/기존 봉인 결과는 수정하지 않는다.

운영 후속: 이전monitor23471은 생성 중 update JSON을읽다JSONDecodeError로종료했으나 main학습은지속했다. 최신완성update역순fallback+tmp크기조회시삭제race(None처리)를독립mock4+2경로검수했다. 중간monitor17893/PID1573134만교체하고최종watcher SHA007eeedfb965fd1235eab5a67d26dd6c844536e0dce7295a320fa2e938c71ce4를사용한다. 이전모든로그/사본/검수기록보존.

첫100(3,276,800전이)/250(8,192,000전이) prefix검산PASS,100독립검수PASS.500체크포인트저장·검산진행중. 최종2000완료아님. 최신실측은progress.jsonl.

500(16,384,000전이)/750(24,576,000전이)prefix검산PASS.1000체크포인트저장·검산진행중. mainPID/session변경없음,보상·source436동결유지.
