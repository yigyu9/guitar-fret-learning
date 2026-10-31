"""원래 경로가 보이는 읽기 전용 사본에서 완료 실행의 입력 봉인을 확인한다."""
import hashlib
import json
from pathlib import Path
root = Path('/home/ajou/yigyu/3')
base = root/'docs/2026-11-02/수정사항/개별비교연구'
seal = json.loads((base/'active_sources_sealed.json').read_text())
actual = {str(p.relative_to(root)) for p in (root/'guitar_learning').rglob('*.py')
          if 'archive' not in p.relative_to(root/'guitar_learning').parts}
assert actual == set(seal), (sorted(actual-set(seal)), sorted(set(seal)-actual))
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest() == h for p,h in seal.items())
for name in ('baseline_s7','lr_s7','exploration_s7','separate_s7'):
    pins = json.loads((base/'runs'/name/'train/J/inputs_before.json').read_text())
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in pins.items()), name
print('287 sources and all four completed-run input seals match in frozen namespace')
