"""CPU contracts: moving frame, assigned note, release and action ownership."""
import unittest
from types import SimpleNamespace
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

from .environment import (MusicGuitarEnvironment,fret_target,world_to_guitar,
                          swept_crossings,press_candidate,shell,RotationEnvelope)
from .environment import crossing_press_valid

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT/'data/song_bundles/00_SS1-68-E_comp'


class GeometryTest(unittest.TestCase):
    def test_moving_guitar_frame(self):
        local = np.array([[.01,.1,.012],[-.02,-.3,.008]])
        rotation = Rotation.from_euler('xyz',[.4,1.2,-.8]).as_matrix()
        position = np.array([-.3,.1,.8])
        world = local@rotation.T+position
        np.testing.assert_allclose(world_to_guitar(world,position,rotation),local,atol=1e-15)

    def test_fret_interval_on_actual_sloping_string(self):
        start,end = np.array([.01,.2,.012]),np.array([.03,-.4,.014])
        target = fret_target(start,end,.16,.2)
        self.assertAlmostEqual(target[1],.18)
        np.testing.assert_allclose(target,start+(end-start)/30)

    def test_wrong_finger_contact_and_hold_not_ready(self):
        target = np.array([.01,.18,.012])
        self.assertEqual(press_candidate(target,target,False,1),(True,False))
        self.assertEqual(press_candidate(target,target,True,.05),(True,False))
        self.assertEqual(press_candidate(target,target,True,.1),(True,True))
        self.assertEqual(press_candidate(target+[.02,0,0],target,True,1),(False,False))

    def test_kinematic_crossing_depth_direction_and_zone(self):
        starts = np.array([[0,.2,.012]])
        ends = np.array([[0,-.4,.012]])
        p0,p1 = np.array([-.01,-.32,.009]),np.array([.01,-.32,.009])
        rows = swept_crossings(p0,p1,starts,ends)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['direction'],1)
        self.assertAlmostEqual(rows[0]['fraction'],.5)
        self.assertEqual(swept_crossings(p0+[0,0,.01],p1+[0,0,.01],starts,ends),[])
        self.assertEqual(swept_crossings(p0+[0,.2,0],p1+[0,.2,0],starts,ends),[])
        self.assertEqual(swept_crossings(p0,p0,starts,ends),[])

    def test_action54_leaves_remaining27_at_reference(self):
        reference = np.linspace(-.3,.3,81)
        indices = np.r_[np.arange(15),np.arange(21,60)]
        result = shell.action_targets(np.ones(54),reference,indices,reference[indices]-.2,reference[indices]+.2)
        kept = np.setdiff1d(np.arange(81),indices)
        np.testing.assert_array_equal(result[kept],reference[kept])
        np.testing.assert_allclose(result[indices],reference[indices]+.2)

    def test_user_rotation_box_boundary_and_quaternion_sign(self):
        envelope = RotationEnvelope()
        for euler in ([45,50,135],[90,100,180],[67.5,90,157.5]):
            q = Rotation.from_euler('xyz',euler,degrees=True).as_quat()
            self.assertTrue(envelope.distance(q)['inside'])
            self.assertTrue(envelope.distance(-q)['inside'])
            self.assertEqual(envelope.distance(q)['upper_rad'],0)
        self.assertFalse(envelope.distance(Rotation.identity().as_quat())['inside'])

    def test_wrong_direction_duplicate_and_timing(self):
        env = MusicGuitarEnvironment.__new__(MusicGuitarEnvironment)
        target = SimpleNamespace(fret=0,finger=None,string=2,traversal_offset_s=0)
        event = SimpleNamespace(event_id='one',score_time_s=1,string_targets=[target],
                                strike=SimpleNamespace(direction='down'))
        env.task = SimpleNamespace(stage='C',events=[event],task_time=lambda t:t,active_targets=lambda t:{})
        env._geometry = lambda:{}
        env._clear_music()
        def crossing(direction,time):
            return dict(string=2,direction=direction,score_time_s=time,ready_before_crossing=[0]*6)
        env.crossings = [crossing(-1,1)]
        self.assertEqual(env._measure_music(1)['wrong_crossings'],1)
        env.crossings = [crossing(1,1.3)]
        self.assertEqual(env._measure_music(1)['accepted_crossings'],0)
        env.crossings = [crossing(1,1)]
        self.assertEqual(env._measure_music(1)['accepted_crossings'],1)
        env.crossings = [crossing(1,1)]
        result = env._measure_music(1)
        self.assertEqual(result['accepted_crossings'],0)
        self.assertEqual(result['wrong_crossings'],1)

    def test_crossing_rejects_released_or_changed_finger_stale_readiness(self):
        target = SimpleNamespace(fret=3,finger=2,string=1)
        bracket = dict(owner_before=[3,2],owner_after=[3,2],valid_before=True,
                       valid_after=True,continuous_dwell_before_s=.12)
        crossing = dict(press_bracket={'1':bracket},ready_before_crossing=[1]*6)
        self.assertTrue(crossing_press_valid(crossing,target))
        bracket['valid_after'] = False
        self.assertFalse(crossing_press_valid(crossing,target))
        bracket.update(valid_after=True,owner_after=[3,1])
        self.assertFalse(crossing_press_valid(crossing,target))
        bracket.update(owner_after=[4,2])
        self.assertFalse(crossing_press_valid(crossing,target))
        bracket.update(owner_after=[3,2],continuous_dwell_before_s=.05)
        self.assertFalse(crossing_press_valid(crossing,target))

    def test_readiness_can_prepare_before_onset_without_crediting_hold(self):
        env = MusicGuitarEnvironment.__new__(MusicGuitarEnvironment)
        target = SimpleNamespace(fret=1,finger=1,string=0,press_start_s=1.,
                                 release_s=2.,sustain_until_s=2.,traversal_offset_s=0)
        event = SimpleNamespace(event_id='press',score_time_s=1.,string_targets=[target],
                                strike=SimpleNamespace(direction='down'))
        env.task = SimpleNamespace(stage='B',events=[event],task_time=lambda t:t,
                                   active_targets=lambda t:{0:(event,target,2.,True)} if 1<=t<2 else {})
        point = np.array([0.,.18,.012])
        env._geometry = lambda:dict(starts=np.array([[0.,.2,.012]]),ends=np.array([[0.,-.4,.012]]),
                                    local={'G:nut':np.array([0.,.2,.012]),'G:fret1':np.array([0.,.16,.012])},
                                    tips={'LH:index3':point})
        env.contacts = [dict(body0_name='human/LH:index3',body1_name='guitar/G:fret1')]
        env._clear_music()
        for i in range(7): metrics = env._measure_music(.8+i/60)
        self.assertEqual(env.readiness[0],1)
        self.assertEqual(metrics['press_hold_release'][0]['assigned_contact_geometric_seconds'],0)
        metrics = env._measure_music(1.)
        self.assertEqual(env.readiness[0],1)
        self.assertAlmostEqual(metrics['press_hold_release'][0]['assigned_contact_geometric_seconds'],1/60)

    def test_shared_source_press_credits_audible_intervals_without_double_dwell(self):
        env = MusicGuitarEnvironment.__new__(MusicGuitarEnvironment)
        def event(name,onset,end):
            target = SimpleNamespace(fret=1,finger=1,string=0,press_start_s=0.,release_s=10.,
                                     sustain_until_s=end,traversal_offset_s=0.)
            return SimpleNamespace(event_id=name,score_time_s=onset,string_targets=[target],
                                   strike=SimpleNamespace(direction='down'))
        first,second = event('first',1.,1.8),event('second',1.5,2.)
        env.task = SimpleNamespace(stage='B',events=[first,second],task_time=lambda t:t,
                                   active_targets=lambda t:{0:(first,first.string_targets[0],1.8,True)})
        env._geometry = lambda:dict(starts=np.array([[0.,.2,.012]]),ends=np.array([[0.,-.4,.012]]),
                                    local={'G:nut':np.array([0.,.2,.012]),'G:fret1':np.array([0.,.16,.012])},
                                    tips={'LH:index3':np.array([0.,.18,.012])})
        env.contacts = [dict(body0_name='human/LH:index3',body1_name='guitar/G:fret1')]
        env._clear_music()
        rows = env._measure_music(1.6)['press_hold_release']
        self.assertAlmostEqual(rows[0]['required_seconds'],.8)
        self.assertAlmostEqual(rows[1]['required_seconds'],.5)
        for row in rows: self.assertAlmostEqual(row['assigned_contact_geometric_seconds'],1/60)
        self.assertAlmostEqual(env.hold_seconds[0],1/60)

    @unittest.skipUnless(BUNDLE.is_dir(),'bundled score unavailable')
    def test_timeline_press_hold_release_and_abi(self):
        env = MusicGuitarEnvironment(BUNDLE,stage='B')
        task = env.task
        event = task.events[0]
        target = event.string_targets[0]
        self.assertGreater(target.fret,0)
        start = task.task_time(target.press_start_s)
        release = task.task_time(min(target.release_s,target.sustain_until_s))
        self.assertEqual(task.encode(max(0,start-.01))[target.string*5+2],0)
        self.assertEqual(task.encode((start+release)/2)[target.string*5+2],1)
        self.assertEqual(task.encode(release+.01)[target.string*5+2],0)
        self.assertEqual(env.obs_dim,744)
        self.assertEqual(env.abi['version'],'fresh_music_native_v1')
        self.assertAlmostEqual(env.horizon,2+task.duration_s)
        self.assertGreater(env.config['finger_range_rad'],shell.DEFAULT_CONFIG['finger_range_rad'])


if __name__=='__main__': unittest.main()
