"""Source post-physics evaluation without action submission or simulation."""
from .strike_native_view import NativeStrikeView
import ast
import hashlib
import inspect
import textwrap
from tab2body.env.tasks import task_strike


def source_evaluator():
    path=inspect.getsourcefile(task_strike.StrikeTask)
    source=open(path).read()
    if hashlib.sha256(source.encode()).hexdigest() != '6368c8623141369de0a51a6719df0888cea8fbd75bffc04f42dbc80a23871a05':
        raise ValueError('Strike source changed; re-review extraction')
    tree=ast.parse(textwrap.dedent(inspect.getsource(task_strike.StrikeTask.step)))
    fn=tree.body[0]
    prefix=ast.parse('action_phase = self.motor_phase.clone()\nself.apply_actions(actions)\nself.step_physics()\nself.refresh()\nself.progress_buf += 1').body
    if [ast.dump(n) for n in fn.body[:5]] != [ast.dump(n) for n in prefix]:
        raise ValueError('Strike source seam changed')
    fn.name='evaluate_after_physics'
    fn.args.args=[ast.arg(arg='self'),ast.arg(arg='action_phase')]
    fn.body=fn.body[5:]
    if any(isinstance(n,ast.Name) and n.id=='actions' for n in ast.walk(fn)):
        raise ValueError('unexpected post-physics action dependency')
    namespace=dict(vars(task_strike))
    exec(compile(ast.fix_missing_locations(tree),path+':dual_post_physics','exec'),namespace)
    return namespace[fn.name],hashlib.sha256(source.encode()).hexdigest()


class DualStrikeView(NativeStrikeView):
    evaluate_after_physics,source_sha256=source_evaluator()

    def step_physics(self): raise RuntimeError('dual view cannot advance native physics')
