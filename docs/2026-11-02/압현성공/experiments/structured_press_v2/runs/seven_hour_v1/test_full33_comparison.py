"""GPU 없이 fresh→strict resume와 부분 블록 제외 절차를 확인한다."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import full33_comparison as runner


class Full33ProcedureTests(unittest.TestCase):
    def exercise(self, stop_second=False):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        runtime = root/'runtime'
        geometry = runtime/'guitar_learning/assets/structured_press_v2/catalog.json'
        geometry.parent.mkdir(parents=True)
        geometry.write_text(json.dumps({'goals': [{'finger': 'index', 'song': 'fixture'}]}))
        commands = []
        def execute(command, destination, out, state):
            commands.append(command)
            destination = Path(destination)
            if stop_second and command[0] == 'train' and '--resume' in command:
                raise runner.research.BudgetStop('fixture deadline')
            destination.mkdir()
            if command[0] == 'train':
                (destination/'report.json').write_text('{"completed":true}')
                (destination/'J').mkdir()
                for name in ('initial', 'final'):
                    (destination/'J'/(name+'.pt')).write_text(str(destination)+name)
            else:
                checkpoint = command[command.index('--checkpoint')+1]
                (destination/'report.json').write_text(json.dumps({
                    'checkpoint_sha256': runner.research.digest(checkpoint)}))
                for name in ('episodes.jsonl', 'episode_metadata.json'):
                    (destination/name).write_text('{}')
            return .01
        values = dict(safe_success=0, failure_episodes=0, mean_safe_clean_s=0.)
        with patch.object(runner, '__file__', str(root/'full33_comparison.py')), \
             patch.object(runner.research, 'RUNTIME', runtime), \
             patch.object(runner.research, 'verify_seal', return_value='sealed'), \
             patch.object(runner.research, 'training_budget', return_value={'allowed': True}), \
             patch.object(runner.research, 'aggregate', return_value=values), \
             patch.object(runner.research, 'execute', side_effect=execute):
            (root/'budget.json').write_text('{}')
            runner.main()
            summary = json.loads((root/'index_full33_seed7_v1/summary.json').read_text())
            with self.assertRaises(FileExistsError):
                runner.main()
        return commands, summary

    def test_fresh_then_strict_resume_and_three_evaluations(self):
        commands, summary = self.exercise()
        trains = [c for c in commands if c[0] == 'train']
        self.assertEqual(len(trains), 2)
        self.assertNotIn('--resume', trains[0])
        self.assertNotIn('--initialize-from', trains[0])
        self.assertIn('--resume', trains[1])
        self.assertEqual(trains[1][trains[1].index('--resume')+1], summary['blocks'][0]['checkpoint'])
        self.assertEqual([r['updates'] for r in summary['blocks']], [100, 200])
        self.assertEqual(len([c for c in commands if c[0] == 'evaluate']), 3)
        self.assertTrue(all(c[c.index('--num-envs')+1] == '32' for c in commands if c[0] == 'evaluate'))
        self.assertEqual(summary['status'], 'completed_comparison_not_stage_promotion')
        self.assertFalse(summary['passed'])

    def test_budget_stop_excludes_unfinished_second_block(self):
        commands, summary = self.exercise(stop_second=True)
        self.assertEqual(summary['status'], 'budget_stopped')
        self.assertEqual([r['updates'] for r in summary['blocks']], [100])
        self.assertEqual(len([c for c in commands if c[0] == 'evaluate']), 2)
        self.assertFalse(summary['passed'])


if __name__ == '__main__':
    unittest.main()
