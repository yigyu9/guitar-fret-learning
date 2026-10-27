"""Verification-only guard for both parent and spawned training workers."""
import sys
import os
import importlib.abc
_BLOCKED = tuple('/home/ajou/yigyu/3/' + name + '/' for name in ('tab2body', 'stability_adapter_2'))
def audit(event, args):
    if event == 'open' and args and isinstance(args[0], (str, bytes)):
        path = os.path.abspath(os.fsdecode(args[0]))
        if path.startswith(_BLOCKED):
            raise AssertionError('Legacy file read blocked: ' + path)
class BlockLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'tab2body', 'stability_adapter_2'}:
            raise AssertionError('Legacy import blocked: ' + fullname)
sys.addaudithook(audit)
sys.meta_path.insert(0, BlockLegacy())
