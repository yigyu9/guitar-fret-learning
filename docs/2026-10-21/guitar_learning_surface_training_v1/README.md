# 첫 새학습 시도: SIGFPE 중단

이2000회시도는완료되지않았다. 프로세스854545가2026-10-21 05:08 UTC부근네이티브SIGFPE(exit136)로종료했고정상report/song_report가없다. 원인은미확정이다.

308개update파일과원본gzip9856행/10,092,544전이의CRC/EOF·episode대응을확인했다. episodes5127건은시간축완주4982+물리실패145이며전곡과제성공0이다. learning_metrics는index0..306의307행만있어마지막307행누락을명시한다.

마지막checkpoint_000299.pt는optimizer300·9,830,400전이경계의저장본이다. model56+actoroptimizer54+valueoptimizer57 tensor finite,3331이력재생오차0,572입력/427소스SHA가일치했다. 저장되지않은8회/262,144전이는후속최종모델경로에서제외한다. CPU로그감사첫시도에도SIGFPE가한번관찰됐으나재시도는통과했고정확한원인단정은하지않는다.

[중단 감사](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_v1/crash_audit.json)와원로그·snapshot·주기checkpoint·100/250회중간분석을보존한다. [복구·최종결과](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_recovery_v1/README.md)는별도phase에서진행하며이중단시도를무중단성공으로바꾸지않는다.

결과SHA목록은result_manifest.json이며이후새결과는별도경로에쓴다.
