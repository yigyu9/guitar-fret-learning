"""CPU Gym integration checks; requires the project's rl38/native Gym setup."""
import json
import unittest
from unittest.mock import Mock, patch

from stability_adapter_2.environment import InitialEnvironment, gymapi, np, vector, quaternion
from stability_adapter_2.strap import point_kinematics
from stability_adapter_2.run_initialization import snapshot


class NativeContractTests(unittest.TestCase):
    def test_lower_initial_pose_preserves_upper_body_and_physics(self):
        settings = {'guitar_initial_z_offset_m':.005,'strap_rest_length_m':1.0891851746440693}
        env = InitialEnvironment(settings)
        try:
            q = env.initial_q.copy()
            human,guitar = env.bodies(env.human),env.bodies(env.guitar)
            props = env.gym.get_actor_dof_properties(env.env,env.human).copy()
            main,torso = list(env.main_indices),list(env.torso_indices)
            unchanged_bodies = [i for i,n in enumerate(env.human_bodies)
                if n not in {side+'_'+body for side in ('L','R') for body in ('Hip','Knee','Ankle','Toe')}]
            index = env.names.index('R_Knee_x')
        finally:
            env.close()
        requested = float(q[index])+.025
        env = InitialEnvironment(dict(settings,joint_angles_rad={'R_Knee_x':requested}))
        try:
            expected = q.copy();expected[index]=requested
            np.testing.assert_array_equal(env.initial_q,expected)
            np.testing.assert_array_equal(env.bodies(env.human)[unchanged_bodies],human[unchanged_bodies])
            np.testing.assert_array_equal(env.bodies(env.guitar),guitar)
            np.testing.assert_array_equal(env.gym.get_actor_dof_properties(env.env,env.human),props)
            self.assertEqual(list(env.main_indices),main)
            self.assertEqual(list(env.torso_indices),torso)
            self.assertEqual(len(main),66)
            self.assertEqual(env.rest_length,settings['strap_rest_length_m'])
            env.set_main_offsets(np.zeros(66,dtype=np.float32))
            np.testing.assert_array_equal(env.target,expected)
        finally:
            env.close()

    def test_guitar_z_initialization_preserves_human_and_never_reinjects(self):
        env = InitialEnvironment()
        try:
            human,guitar = env.bodies(env.human),env.bodies(env.guitar)
            original_q,goal_q = env.initial_q.copy(),env.goal_quaternion.copy()
            source,rest = env.goal_position.copy(),env.rest_length
        finally:
            env.close()
        native = gymapi.acquire_gym()
        class Recorder:
            def __getattr__(self,name):
                return getattr(native,name)
        recorder = Recorder()
        recorder.set_actor_dof_states = Mock(wraps=native.set_actor_dof_states)
        recorder.set_actor_rigid_body_states = Mock(wraps=native.set_actor_rigid_body_states)
        with patch('stability_adapter_2.environment.gymapi.acquire_gym',return_value=recorder):
            env = InitialEnvironment({'guitar_initial_z_offset_m':.005,'strap_rest_length_m':rest})
        try:
            np.testing.assert_array_equal(env.initial_q,original_q)
            np.testing.assert_array_equal(env.bodies(env.human),human)
            shifted = env.bodies(env.guitar)
            for axis in ('x','y','z'):
                np.testing.assert_allclose(shifted['pose']['p'][axis]-guitar['pose']['p'][axis],
                    .005 if axis=='z' else 0,atol=2e-7,rtol=0)
            np.testing.assert_array_equal(shifted['pose']['r'],guitar['pose']['r'])
            np.testing.assert_array_equal(shifted['vel'],guitar['vel'])
            np.testing.assert_array_equal(env.goal_quaternion,goal_q)
            np.testing.assert_array_equal(env.source_goal_position,source)
            np.testing.assert_allclose(env.goal_position,source+[0,0,.005],atol=1e-12,rtol=0)
            self.assertEqual(env.rest_length,rest)
            initial = snapshot(env)
            self.assertLess(initial['position_error_m'],1e-6)
            self.assertAlmostEqual(initial['source_position_error_m'],.005,places=6)
            self.assertEqual(recorder.set_actor_dof_states.call_count,1)
            self.assertEqual(recorder.set_actor_rigid_body_states.call_count,1)
            env.step()
            self.assertEqual(recorder.set_actor_dof_states.call_count,1)
            self.assertEqual(recorder.set_actor_rigid_body_states.call_count,1)
            np.testing.assert_array_equal(env.goal_position,source+[0,0,.005])
            self.assertGreater(snapshot(env)['position_error_m'],1e-7)
        finally:
            env.close()

    def test_initial_settings_apply_once_without_rebasing_length(self):
        env = InitialEnvironment()
        try:
            names = list(env.names)
            original_q = env.initial_q.copy()
            goal = env.goal_position.copy()
            goal_q = env.goal_quaternion.copy()
            length = env.rest_length
            original_route = env.initial_route_length
            wrist = vector(env.bodies(env.human)[env.human_bodies.index('R_Wrist')]['pose']['p'])
        finally:
            env.close()
        index = names.index('L_Thorax_x')
        requested = float(original_q[index])+.02
        env = InitialEnvironment({'joint_angles_rad':{'L_Thorax_x':requested},
                                  'strap_rest_length_m':length+.001})
        try:
            states = env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL)
            self.assertAlmostEqual(float(states['pos'][index]),requested,places=6)
            others = np.arange(len(names))!=index
            np.testing.assert_array_equal(states['pos'][others],original_q[others])
            np.testing.assert_array_equal(states['vel'],0)
            np.testing.assert_array_equal(env.goal_position,goal)
            np.testing.assert_array_equal(env.goal_quaternion,goal_q)
            self.assertEqual(env.rest_length,length+.001)
            self.assertGreater(abs(env.initial_route_length-original_route),1e-6)
            # The unrelated right hand keeps its actual initial FK position.
            np.testing.assert_array_equal(vector(env.bodies(env.human)[env.human_bodies.index('R_Wrist')]['pose']['p']),wrist)
            env.step()
            self.assertEqual(env.rest_length,length+.001)
            np.testing.assert_array_equal(env.target,env.initial_q)
        finally:
            env.close()

    def test_target_changes_actual_joint_motion(self):
        positions = []
        for offset in (0., .02):
            env = InitialEnvironment()
            try:
                index = env.names.index('R_Elbow_x')
                action = np.zeros(66, dtype=np.float32)
                action[list(env.main_indices).index(index)] = offset
                env.set_main_offsets(action)
                env.step()
                positions.append(float(env.gym.get_actor_dof_states(
                    env.env, env.human, gymapi.STATE_ALL)['pos'][index]))
            finally:
                env.close()
        response = positions[1] - positions[0]
        print(json.dumps({'probe': 'R_Elbow_x_target_response', 'offset_rad': .02,
                          'positions_rad': positions, 'response_rad': response}))
        self.assertGreater(response, 1e-6)

    def test_native_velocity_is_at_com(self):
        gym = gymapi.acquire_gym()
        params = gymapi.SimParams()
        params.dt = .001
        params.gravity = gymapi.Vec3(0, 0, 0)
        params.use_gpu_pipeline = params.physx.use_gpu = False
        sim = gym.create_sim(0, -1, gymapi.SIM_PHYSX, params)
        self.assertIsNotNone(sim)
        try:
            env = gym.create_env(sim, gymapi.Vec3(-1, -1, -1), gymapi.Vec3(1, 1, 1), 1)
            asset = gym.create_box(sim, .1, .1, .1, gymapi.AssetOptions())
            actor = gym.create_actor(env, asset, gymapi.Transform(), 'offset_com', 0, 0)
            props = gym.get_actor_rigid_body_properties(env, actor)
            props[0].com = gymapi.Vec3(.2, 0, 0)
            self.assertTrue(gym.set_actor_rigid_body_properties(env, actor, props, False))
            self.assertTrue(gym.prepare_sim(sim))
            states = gym.get_actor_rigid_body_states(env, actor, gymapi.STATE_ALL).copy()
            states['vel']['linear'].fill(0)
            states['vel']['angular'].fill(0)
            states['vel']['angular']['z'] = 1
            self.assertTrue(gym.set_actor_rigid_body_states(env, actor, states, gymapi.STATE_ALL))
            before = gym.get_actor_rigid_body_states(env, actor, gymapi.STATE_ALL)[0].copy()
            actual_com = gym.get_actor_rigid_body_properties(env, actor)[0].com
            _, predicted = point_kinematics(vector(before['pose']['p']), quaternion(before['pose']['r']),
                vector(before['vel']['linear']), vector(before['vel']['angular']), np.zeros(3),
                np.array([actual_com.x, actual_com.y, actual_com.z]))
            gym.simulate(sim)
            gym.fetch_results(sim, True)
            after = gym.get_actor_rigid_body_states(env, actor, gymapi.STATE_ALL)[0].copy()
            finite_difference = (vector(after['pose']['p']) - vector(before['pose']['p'])) / params.dt
            print(json.dumps({'probe': 'offset_com_origin_velocity', 'predicted_mps': predicted.tolist(),
                              'finite_difference_mps': finite_difference.tolist(),
                              'reported_com_velocity_mps': vector(after['vel']['linear']).tolist()}))
            np.testing.assert_allclose(vector(after['vel']['linear']), 0, atol=1e-6)
            np.testing.assert_allclose(predicted, [0, -.2, 0], atol=1e-6)
            np.testing.assert_allclose(finite_difference, predicted, atol=5e-4)
        finally:
            gym.destroy_sim(sim)


if __name__ == '__main__':
    unittest.main()
