"""Pure CPU selection/clock fixtures; never create MuJoCo, GPU or GL contexts."""
import copy
import importlib.util
from pathlib import Path
import unittest

import numpy as np

SPEC = importlib.util.spec_from_file_location('ring_pinky_render',Path(__file__).with_name('render_probe.py'))
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def metadata():
    names = ['LH:ring1_x','LH:ring1_z','LH:ring2','LH:ring3','LH:pinky1_x','LH:pinky1_z','LH:pinky2','LH:pinky3']
    cases = [dict(env_id=2*i+j,kind='pulse',joint=name,axis_index=i,direction=direction)
             for i,name in enumerate(names) for j,direction in enumerate((1,-1))]
    cases += [dict(env_id=16,kind='hold'),dict(env_id=17,kind='coordinated_return')]
    return dict(tested_joint_names=names,native_lower_rad=[-1.]*8,native_upper_rad=[1.]*8,
                probe_start_target_rad=[[0.]*8 for _ in range(18)],cases=cases)


class RenderProbeTests(unittest.TestCase):
    def test_larger_native_headroom_and_tie_lowest_case_id_not_outcome(self):
        m = metadata()
        for row in m['probe_start_target_rad']: row[2]=.7; row[5]=-.5
        m['cases'].reverse()
        result = tool.select_cases(m)
        self.assertEqual([c['env_id'] for c in result],[5,10,14,17])
        self.assertAlmostEqual(result[0]['selection_headroom_rad'],1.7)
        changed = copy.deepcopy(m)
        for c in changed['cases']: c['physical_success']=c['env_id'] not in (5,10,14,17)
        self.assertEqual([c['env_id'] for c in tool.select_cases(changed)],[5,10,14,17])

    def test_at_limit_selects_inward_and_invalid_headroom_rejected(self):
        m = metadata()
        for row in m['probe_start_target_rad']: row[2]=-1.; row[5]=1.; row[7]=1.
        self.assertEqual([c['env_id'] for c in tool.select_cases(m)],[4,11,15,17])
        m['probe_start_target_rad'][0][0]=2.
        with self.assertRaises(ValueError): tool.select_cases(m)

    def test_exact_source_endpoint_and_prefix_time_mapping(self):
        for start in (0,600):
            clock = np.arange(start+181)*4
            indices = tool.clip_frames(clock,start)
            self.assertEqual((len(indices),int(indices[0]),int(indices[-1])),(180,start+1,start+180))
            self.assertAlmostEqual(clock[indices[0]]/240.,start/60.+1/60.)
            self.assertEqual(clock[indices[-1]]/240.,start/60.+3.)
            with self.assertRaises(ValueError): tool.clip_frames(clock[:-1],start)
            clock[-1]+=1
            with self.assertRaises(ValueError): tool.clip_frames(clock,start)


if __name__=='__main__':
    unittest.main()
