# 후속 연구 전용. 원연구와 기본 실행 설정은 변경하지 않는다.
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
# Torch 스레드 고정 대체도 필요: 아래 래퍼로 연구 CLI 실행
# python /home/ajou/yigyu/3/docs/2026-11-02/수정사항/연구환경효율검증/thread_runtime.py 1 train --out NEW ...
