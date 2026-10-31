"""분석·렌더 프로세스에서 읽은 NPZ 배열을 재사용한다. 원자료는 수정하지 않는다."""
import hashlib
from pathlib import Path
import runpy
import sys


def install_cache():
    import numpy as np
    original=np.lib.npyio.NpzFile.__getitem__
    def cached(archive,key):
        arrays=archive.__dict__.setdefault('_press_diagnostic_array_cache',{})
        if key not in arrays:
            arrays[key]=original(archive,key)
        return arrays[key]
    np.lib.npyio.NpzFile.__getitem__=cached
    return original


def main():
    import numpy as np
    if len(sys.argv)<2:raise ValueError('분석/렌더 스크립트와 인자 필요')
    script=Path(sys.argv[1]).resolve()
    allowed={'analyze.py','render_summary.py','plot_analysis.py','audit_wrist_region.py','audit_finger_joints.py'}
    if script.parent!=Path(__file__).resolve().parent or script.name not in allowed:
        raise ValueError('같은 디렉토리의 승인된 읽기 전용 분석/렌더 도구만 실행')
    print('[npz cache] source sha256 '+hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),flush=True)
    original=install_cache()
    sys.argv=[str(script)]+sys.argv[2:]
    try:runpy.run_path(str(script),run_name='__main__')
    finally:np.lib.npyio.NpzFile.__getitem__=original


if __name__=='__main__':main()
