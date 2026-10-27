"""Render-source guards and unchanged quaternion ordering; no GL/physics needed."""
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('v20_a500_render',Path(__file__).with_name('render_video.py'))
R=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


def source():
    episodes=[dict(env_id=i,reason='timeline_complete',task_time_s=32.,
        left_curriculum=dict(full_safe=True)) for i in range(8)]
    chain=dict(schema=R.CHAIN_SCHEMA,fresh_policy=True,run_completed=True,
        source_optimizer_updates=500,repeat=1)
    report=dict(completed=True,num_envs=1024,source_optimizer_updates=500,ticks=1969,
        gpu_scene=dict(closed=True,physx_use_gpu=True,use_gpu_pipeline=True,
            environment_count=1024,physics_steps=7876),repeat=1,
        restoration_verified=['model','actor_optimizer','value_optimizer','torch_rng','cuda_rng','numpy_rng','python_rng','3331_curriculum'],
        training_chain=chain,episodes=episodes)
    meta=dict(source_optimizer_updates=500,training_chain=copy.deepcopy(chain),
        selected_env_id=0,capture_envs=list(range(8)),captures=[dict(env_id=i) for i in range(8)])
    return report,meta


class RenderGuards(unittest.TestCase):
    def test_accepts_predeclared_minimum_safe_id_and_rejects_score_selection(self):
        report,meta=source()
        self.assertEqual(R.validate_evaluation(report,meta),0)
        meta['selected_env_id']=7
        with self.assertRaisesRegex(ValueError,'Predeclared selection'):
            R.validate_evaluation(report,meta)

    def test_rejects_old_budget_or_missing_optimizer_audit(self):
        for mutation in ('budget','optimizer','repeat'):
            report,meta=source()
            if mutation=='budget':
                report['source_optimizer_updates']=3000
            elif mutation=='optimizer':
                report['restoration_verified'].remove('value_optimizer')
            else:
                report['training_chain']['repeat']=2
                meta['training_chain']['repeat']=2
            with self.assertRaises(ValueError):
                R.validate_evaluation(report,meta)

    def test_no_safe_completion_falls_back_to_longest_then_id(self):
        report,meta=source()
        for episode in report['episodes']:
            episode['reason']='terminal_failure'
            episode['left_curriculum']['full_safe']=False
            episode['task_time_s']=10.
        report['episodes'][2]['task_time_s']=20.
        report['episodes'][5]['task_time_s']=20.
        meta['selected_env_id']=2
        self.assertEqual(R.validate_evaluation(report,meta),2)

    def test_pose_state_preserves_xyzw_and_rejects_body_reordering(self):
        initial=dict(human_body_names=['palm'],guitar_body_names=['neck'])
        names=['human/palm','guitar/neck','chair/box']
        frames=[[1.,2.,3.,.1,.2,.3,.4]+[0.]*6 for _ in names]
        state=R.pose_state(names,frames,initial)
        self.assertEqual(list(state['human_body_states'][0]['pose']['r']),list('xyzw'))
        self.assertEqual(state['human_body_states'][0]['pose']['r'],dict(x=.1,y=.2,z=.3,w=.4))
        with self.assertRaisesRegex(ValueError,'body order'):
            R.pose_state(names[::-1],frames,initial)


if __name__=='__main__':
    unittest.main()
