"""Graphics-free training wrapper; recorded evaluation retains device0."""
RENDER_APIS = frozenset(('create_camera_sensor','create_viewer','step_graphics',
    'render_all_camera_sensors','get_camera_image','write_camera_image_to_file'))


def graphics_wrapper(base_class, recording):
    device = 0 if recording else -1
    class IsolatedGraphicsGym(base_class):
        def __init__(self, gym):
            super().__init__(gym)
            self.graphics_creations = []
            self.render_lookup_counts = {}

        def create_sim(self, compute, graphics, engine, params):
            sim = self.gym.create_sim(compute, device, engine, params)
            self.graphics_creations.append({'compute_device_id': int(compute),
                'requested_graphics_device_id': int(graphics), 'forwarded_graphics_device_id': device,
                'engine': str(engine), 'physics_dt': float(params.dt),
                'GPU_pipeline': bool(params.use_gpu_pipeline), 'GPU_PhysX': bool(params.physx.use_gpu),
                'sim_created': sim is not None})
            return sim

        def __getattr__(self, name):
            if name in RENDER_APIS:
                if not recording: raise RuntimeError('render API forbidden in graphics-free training: '+name)
                self.render_lookup_counts[name] = self.render_lookup_counts.get(name,0)+1
            return super().__getattr__(name)
    return IsolatedGraphicsGym
