"""검증된 v1의 동일한5초 유지 검사를 새 초기 상태에 적용한다."""
import importlib.util
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]
SOURCE=OUT.parent/'초기자세_v1/tools/verify_native.py'


def main():
    spec=importlib.util.spec_from_file_location('neck_pose_native_hold',SOURCE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT=OUT
    module.main()


if __name__=='__main__':main()
