"""후속 속도 검증 프로세스에서만 Torch 스레드 고정을 명시적으로 대체한다."""
import runpy
import sys


def main():
    threads = int(sys.argv[1])
    if threads not in (1, 2, 4):
        raise ValueError('expected benchmark threads 1, 2 or 4')
    import isaacgym  # Torch보다 먼저 native 확장 초기화
    import torch
    original = torch.set_num_threads

    def selected_threads(requested):
        original(threads)
        if torch.get_num_threads() != threads:
            raise RuntimeError('Torch thread selection failed')

    selected_threads(threads)
    torch.set_num_threads = selected_threads
    print('[efficiency] torch_intraop_threads=%d; process-scoped override' % torch.get_num_threads(), flush=True)
    sys.argv = ['guitar_learning.tool.experiments.finger_ablation']+sys.argv[2:]
    try:
        runpy.run_module('guitar_learning.tool.experiments.finger_ablation', run_name='__main__')
    finally:
        torch.set_num_threads = original


if __name__ == '__main__':
    main()
