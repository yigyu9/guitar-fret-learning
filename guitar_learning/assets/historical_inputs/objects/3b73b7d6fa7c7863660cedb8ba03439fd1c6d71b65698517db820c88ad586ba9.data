"""Preserve existing checkpoint numerics while adding reviewed collector sources."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import torch
from stability_adapter_2.deadline_graphics_migration_v1 import migrate_payload
ADDED_FILES=('parallel_cpu_env_v1.py','parallel_collect_v1.py','parallel_migration_v1.py',
             'run_parallel_training_v1.py','test_parallel_collect_v1.py','run_parallel_probe_v1.py')

def adopt(path,trainer,output):
    path=Path(path);before=hashlib.sha256(path.read_bytes()).hexdigest()
    original=torch.load(path,map_location='cpu',weights_only=True)
    additions=[str(Path(__file__).resolve().parent/name) for name in ADDED_FILES]
    result=migrate_payload(original,trainer.abi,asdict(trainer.config),additions)
    result['resume_scope']='model/Adam/RMS/RNG/counters retained; reviewed parallel collector; fresh independent episodes, not single-scene sample replay'
    with Path(output).open('xb') as f:torch.save(result,f)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    return {'source':str(path),'source_sha256':before,'output':str(output),
        'output_sha256':hashlib.sha256(Path(output).read_bytes()).hexdigest(),
        'updates':original['updates'],'transitions':original['transitions'],'added_sources':additions,
        'scope':result['resume_scope']}
