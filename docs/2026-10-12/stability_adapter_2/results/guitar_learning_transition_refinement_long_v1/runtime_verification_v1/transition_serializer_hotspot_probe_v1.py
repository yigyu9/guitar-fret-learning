import ctypes
import json
import os
import random
import struct
import math
from pathlib import Path
from guitar_learning.transition_refinement_runtime import serialization
source=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_v1/training_contract.json')
value=json.loads(source.read_text())
rng=random.Random(735)
raw=[struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0] for _ in range(1000)]
value['roundtrip_probe']=[v for v in raw if math.isfinite(v)]
library=ctypes.CDLL('/tmp/transition_serializer_hotspot_marker_v1.so')
old=serialization.install()
library.transition_serializer_hotspot_marker()
for _ in range(10):
    actual=json.loads(json.dumps(value,allow_nan=False))
assert all(struct.pack('>d',a)==struct.pack('>d',b) for a,b in zip(value['roundtrip_probe'],actual['roundtrip_probe']))
os.write(1,b'CHECKED_JSON_PATH_PASS\n')
os._exit(0)
