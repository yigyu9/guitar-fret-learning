# 표면 보상 학습: 첫 JSON 보호 후에도 중단

JSON쓰기의 FE_INEXACT만 가리는 첫 수정으로 global450부터 재개했다. 그러나 local369/global820회에서 동일 format_float_short+144/SIGFPE가 재발했다. 이 보호는 통제CPU시험에는 통과했지만 장기실행을 보호하지 못했으며 해결된 수정으로 해석하지 않는다. 일반CPU 원로그 검산도 같은 guarded JSON내에서1회 실패했고 GDB 검산재실행은통과했다. GPU물리만을원인으로단정하지않는다.

마지막 정상 checkpoint local349/global800회는 model56/actor optimizer54/value optimizer57 유한성·3331상태재생0오차·429동결소스와575입력SHA 검증을 통과했다. 총370update·11840원행·12,124,160전이·6159종료곡의 CRC/EOF·대응을검산했다. local369 metrics행만오류도중누락됐으며 report/final/정상GPUclose없음은실패실행으로보존한다. 모델경로에는 첫350회만 포함하고 마지막20회655,360전이는미저장실행으로별도보존한다.

접근기준충족과접촉단계전환,500/750회해석은시점별중간결과다. 최종2000회성과로확대하지않는다. 과거동일문제의 Dragon4직렬화우회를발견하여다음단계는 ../guitar_learning_surface_training_json_v2에서진행한다. 근본FP상태변경주체는미확인이다.
