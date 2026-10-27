# 표면 보상 학습 첫 복구: SIGFPE 중단

원래300회 저장본에서 재개해185회 업데이트를 기록했으나 global485회에서 다시 SIGFPE로 종료했다. 정상 report/final/cleanup은 없으며 완료한1700회 실행으로 해석하지 않는다. 마지막 정상 checkpoint는 local149/global450회다. 이 파일에서 모델56·actor optimizer54·value optimizer57 tensor 유한성,3331 curriculum 재생오차0,573입력pin과427동결source일치를 검증했다.

원로그5920행/6,062,080전이와3080종료episode의 CRC/EOF·update 대응을 통과했다. 마지막local184의 metrics 행은 쓰기 도중 오류로 누락됐다. 복구 모델 경로에는 첫150회/4,915,200전이만 포함하며, 미저장35회/1,146,880전이는 실제 실행 이력으로 보존한다. 상세는 crash_audit.json이다.

GDB/Python스택은 물리 계산이 아닌 gpu_runner의 learning_metrics JSON float 변환(format_float_short)에서 si_code6/FPE_FLTRES를 확인했다. 기존 FP환경을 변경한 native 호출은 아직 미확인이다. JSON쓰기 범위의 FE_INEXACT 보호와 새429source를 동결한 다음 복구는 ../guitar_learning_surface_training_logging_fix_v1에서 진행한다.
