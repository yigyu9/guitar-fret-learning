"""Pure CPU checkpoint ranking, capture and pose mapping checks; no SDK or GL."""
import ast
import copy
import importlib.util
from pathlib import Path
import unittest
import numpy as np

PHASE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name,PHASE/(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


evaluation, video = load('evaluate_checkpoints'), load('render_video')


def report(updates, notes, safe=1024):
    return dict(completed=True,num_envs=1024,source_optimizer_updates=updates,checkpoint=str(updates)+'.pt',
        evaluation_directory='/evaluation/'+str(updates), episodes=[dict(env_id=i,
            song=dict(left_success_count=notes),reason='timeline_complete' if i<safe else 'terminal_failure',
            left_curriculum=dict(full_safe=i<safe),task_time_s=32.8167 if i<safe else 5.) for i in range(1024)])


class VideoWorkflowTests(unittest.TestCase):
    def test_same_budget_paths_and_all_mean_safety_latest_ranking(self):
        for count,name in ((0,'initial.pt'),(500,'checkpoint_000499.pt'),(1000,'checkpoint_000999.pt'),
                           (1500,'checkpoint_001499.pt'),(2000,'final.pt')):
            self.assertEqual(evaluation.checkpoint_path(Path('/run'),count).name,name)
        with self.assertRaises(ValueError): evaluation.checkpoint_path(Path('/run'),499)
        rows = [report(0,8),report(500,7),report(1000,7,1023),report(1500,7),report(2000,6)]
        result = evaluation.checkpoint_selection(rows)
        self.assertEqual(result['best']['updates'],1500); self.assertEqual(result['latest']['updates'],2000)
        self.assertFalse(result['mean_achieved_improved_over_initial'])
        rows[1]['episodes'][0]['song']['left_success_count']=9
        self.assertEqual(evaluation.checkpoint_selection(rows)['best']['updates'],500)
        self.assertEqual(evaluation.checkpoint_selection(rows)['scores'][1]['mean_achieved'],7+2/1024)
        rows[1]['episodes'][0]['song']['left_success_count']=67
        rows[1]['episodes'][0]['reason']='terminal_failure'; rows[1]['episodes'][0]['left_curriculum']['full_safe']=False
        self.assertEqual(evaluation.checkpoint_selection(rows)['scores'][1]['mean_achieved'],7+60/1024)

    def test_incomplete_duplicate_and_invalid_note_results_rejected(self):
        row = report(500,1)
        for rows in ([row,row],[dict(row,episodes=row['episodes'][:-1])]):
            with self.assertRaises(ValueError): evaluation.checkpoint_selection(rows)
        row['episodes'][0]['song']['left_success_count']=float('nan')
        with self.assertRaises(ValueError): evaluation.checkpoint_selection([row])
        partial = evaluation.checkpoint_selection([report(2000,2)])
        self.assertIsNone(partial['mean_achieved_improved_over_initial'])

    def test_predeclared_video_cohort_is_safe_then_id_not_score(self):
        rows = report(500,0,0)['episodes'][:8]
        self.assertEqual(evaluation.select_video_env(rows),0)
        rows[7]['task_time_s']=10.; self.assertEqual(evaluation.select_video_env(rows),7)
        for i in (3,5): rows[i].update(reason='timeline_complete',left_curriculum=dict(full_safe=True))
        rows[5]['song']['left_success_count']=67
        self.assertEqual(evaluation.select_video_env(list(reversed(rows))),3)

    def test_capture_clock_finite_counts_and_pose_reordering(self):
        arrays = dict(body_state=np.zeros((3,106,13)),q=np.zeros((3,105)),qd=np.zeros((3,105)),
            target=np.zeros((3,105)),action=np.zeros((3,39)),clock=np.array([0,4,8]),
            left_count=np.array([0,0,1]),near_count=np.zeros(3),contact_count=np.zeros(3),candidate_count=np.zeros(3))
        arrays['body_state'][...,6]=1.
        episode = dict(steps=2,task_time_s=8/240.,song=dict(left_success_count=1))
        evaluation.validate_capture(arrays,106,episode)
        bad = copy.deepcopy(arrays); bad['clock'][1]=8
        with self.assertRaises(ValueError): evaluation.validate_capture(bad,106,episode)
        initial = dict(human_body_names=['Pelvis'],guitar_body_names=['guitar'])
        names = ['human/Pelvis','guitar/guitar','chair/box']
        poses = np.arange(39.).reshape(3,13)
        result = video.pose_state(names,poses,initial)
        self.assertEqual(result['guitar_body_states'][0]['pose']['p'],dict(x=13.,y=14.,z=15.))
        with self.assertRaises(ValueError): video.pose_state(list(reversed(names)),poses,initial)

    def test_json_writes_keep_public_encoder_and_no_policy_update_calls(self):
        for name in ('evaluate_checkpoints','render_video'):
            tree = ast.parse((PHASE/(name+'.py')).read_text())
            calls = [n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
            writes = [n.func for n in calls if n.func.attr in ('dump','dumps')]
            self.assertTrue(writes)
            self.assertTrue(all(isinstance(f.value,ast.Name) and f.value.id=='json_io' for f in writes))
            self.assertFalse(any(isinstance(n.func.value,ast.Name) and n.func.value.id=='trainer' and
                n.func.attr in ('update','save') for n in calls))


if __name__=='__main__': unittest.main()
