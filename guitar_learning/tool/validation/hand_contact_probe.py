"""현행 타현·영상 도구가 공유하는 native 그래픽·입력 봉인·영상 종료 보조."""

def physics_source_paths(root):
    """보상·정책과 별개로 물리 실행 입력 경로를 모은다."""
    paths = [root/'guitar_learning'/p for p in (
        'gpu/scene.py', 'gpu/control.py', 'gpu/contact.py', 'core/control.py',
        'core/geometry.py', 'runtime/prepared_reset_v1.py', 'runtime/native_session.py',
        'native/paths.py', 'tool/validation/hand_contact_probe.py',
        'tool/validation/press_acquisition.py')]
    return {p for p in paths if p.exists()} | set((root/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*'))


class GraphicsGym:
    """영상용 그래픽 장치만 지정하고 나머지 native 호출은 그대로 전달한다."""
    def __init__(self, native):
        self.native = native

    def __getattr__(self, name):
        return getattr(self.native, name)

    def create_sim(self, compute, graphics, engine, params):
        if graphics != -1:
            raise ValueError('Expected production headless graphics choice')
        return self.native.create_sim(compute, compute, engine, params)


def finish_video(video):
    """영상 입력이 끊겨도 인코더 프로세스의 종료를 회수한다."""
    errors, code = [], None
    if video is not None:
        try:
            video.stdin.close()
        except OSError as error:
            errors.append('encoder_stdin: '+repr(error))
        try:
            code = video.wait()
        except Exception as error:
            errors.append('encoder_wait: '+repr(error))
    return code, errors
