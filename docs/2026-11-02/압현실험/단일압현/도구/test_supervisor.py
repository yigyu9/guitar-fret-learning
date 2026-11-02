"""GPU 없이 평가 복구·중단 기준·주기 저장 재개를 확인한다."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('single18_supervisor',HERE/'supervisor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def metrics(count=16, achievement=16):
    return dict(episodes=count,achievement=achievement,clean_fraction=.95,physical=0,wrist=0,wrong_s=0.)


class SupervisorTests(unittest.TestCase):
    def study(self):
        study=m.Study.__new__(m.Study)
        study.state={'jobs':{},'deadline_epoch':float('inf')}
        study.save=lambda:None
        return study

    def case(self):
        return dict(case_id='index_s1_f1',catalog='catalog',provenance='proof',updates=0,
            status='ready',history=[],candidate_updates=[])

    def test_fast_and_confirmation_gates_include_failures(self):
        self.assertTrue(m.passed(metrics(),16))
        self.assertFalse(m.passed(metrics(16,14),16))
        self.assertTrue(m.passed(metrics(32,31),32))
        value=metrics();value['physical']=1
        self.assertFalse(m.passed(value,16))

    def test_atomic_state_replaces_and_leaves_no_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.json'
            m.write(path,{'status':'running'});m.write(path,{'status':'complete'})
            self.assertEqual(json.loads(path.read_text())['status'],'complete')
            self.assertFalse(path.with_name('state.json.tmp').exists())

    def test_interrupted_evaluation_uses_existing_training_checkpoint(self):
        study=self.study();case=self.case()
        case.update(updates=25,checkpoint='/existing/J/final.pt',status='trained')
        study.retry_job=lambda *a,**kw: self.fail('학습 재실행 금지')
        study.assess=lambda *a:(metrics(),Path('/evaluation'))
        study.train_block(case,25)
        self.assertEqual(case['history'][0]['checkpoint'],'/existing/J/final.pt')
        self.assertEqual(case['completed_boundaries'],[25])

    def test_interrupted_confirmation_is_not_skipped(self):
        study=self.study();case=self.case()
        case.update(updates=50,checkpoint='/existing/J/final.pt',status='trained',candidate_updates=[25,50])
        study.retry_job=lambda *a,**kw: self.fail('학습 재실행 금지')
        seen=[]
        def assess(case,checkpoint,count,label):
            seen.append(count);return metrics(count,count),Path('/evaluation')
        study.assess=assess
        study.train_block(case,50)
        self.assertEqual(seen,[16,32]);self.assertEqual(case['status'],'passed')
        self.assertEqual(case['candidate_updates'],[25,50])

    def test_retry_uses_hashed_periodic_checkpoint_and_remaining_updates(self):
        study=self.study();case=self.case()
        calls=[]
        with tempfile.TemporaryDirectory() as directory:
            phase=Path(directory)/'J';phase.mkdir()
            checkpoint=phase/'checkpoint_000010.pt';checkpoint.write_bytes(b'valid-periodic')
            manifest=phase/'checkpoint_manifest.jsonl'
            manifest.write_text(json.dumps(dict(path=checkpoint.name,kind='periodic',optimizer_updates=10,sha256=m.sha(checkpoint)))+'\n')
            def job(label,operation,case,args,timeout):
                calls.append(list(args))
                if len(calls)==1:
                    study.state['jobs'][label]=[dict(out=directory,status='failed')]
                    raise RuntimeError('일시적 프로세스 오류')
                return Path('/success')
            study.job=job
            result=study.retry_job('train','train',case,['--updates',25])
            self.assertEqual(result,Path('/success'))
            self.assertEqual(calls[1][calls[1].index('--updates')+1],15)
            self.assertEqual(calls[1][calls[1].index('--resume')+1],str(checkpoint))

    def test_global_integrity_failure_is_not_retried(self):
        study=self.study();case=self.case();calls=[]
        def job(*args,**kwargs):
            calls.append(1);raise RuntimeError('GLOBAL_IDENTITY: source changed')
        study.job=job
        with self.assertRaisesRegex(RuntimeError,'GLOBAL_IDENTITY'):
            study.retry_job('eval','evaluate',case,[])
        self.assertEqual(len(calls),1)


if __name__=='__main__':unittest.main()
