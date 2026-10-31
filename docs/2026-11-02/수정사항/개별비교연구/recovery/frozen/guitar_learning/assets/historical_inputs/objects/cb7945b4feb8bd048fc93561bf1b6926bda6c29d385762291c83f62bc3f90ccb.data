"""JSON float-bit equivalence and explicit adapter lifetime, without native scenes."""
import gzip
import hashlib

import numpy as np
import io
import json
import math
from pathlib import Path
import random
import struct
import unittest
from unittest.mock import patch

from guitar_learning.transition_refinement_runtime_v2 import serialization as adapter


def bits(value):
    return struct.pack('>d', value)


def same_tree(test, original, actual):
    if isinstance(original, float):
        test.assertIsInstance(actual, float)
        test.assertEqual(bits(original), bits(actual))
    elif isinstance(original, dict):
        test.assertEqual(original.keys(), actual.keys())
        for key,value in original.items():same_tree(test,value,actual[key])
    elif isinstance(original, list):
        test.assertEqual(len(original),len(actual))
        for a,b in zip(original,actual):same_tree(test,a,b)
    else:test.assertEqual(original,actual)


class SerializationV2Tests(unittest.TestCase):
    def tearDown(self):
        if adapter._active is not None:adapter.restore(adapter._active)

    def test_all_float_boundaries_and_random64_roundtrip_exact_bits(self):
        patterns = [0,1,2,0x000fffffffffffff,0x0010000000000000,
            0x3ff0000000000000,0x3fb999999999999a,0x7fefffffffffffff]
        patterns += [value | (1<<63) for value in patterns]
        rng=random.Random(734)
        patterns += [rng.getrandbits(64) for _ in range(5000)]
        values = [struct.unpack('>d',value.to_bytes(8,'big'))[0] for value in patterns]
        values = [value for value in values if math.isfinite(value)]
        token=adapter.install()
        encoded=json.dumps(values,allow_nan=False)
        decoded=json.loads(encoded)
        same_tree(self,values,decoded)
        # Every emitted numeric token remains compatible with the original decoder.
        original_loads=next(old for owner,name,old,_ in token['entries'] if owner is json and name=='loads')
        same_tree(self,values,original_loads(encoded,cls=adapter._DECODER))

    def test_parser_halfway_signed_zero_and_extreme_exponent_semantics(self):
        adapter.install()
        for text,pattern in [('9007199254740993.0',0x4340000000000000),
                ('2.4703282292062327e-324',0),('2.4703282292062328e-324',1),
                ('-0.0',1<<63),('-1e-10000000000',1<<63)]:
            self.assertEqual(bits(json.loads(text)),pattern.to_bytes(8,'big'))
        self.assertEqual(json.loads('1e10000000000'),math.inf)
        self.assertEqual(json.loads('-1e10000000000'),-math.inf)
        self.assertEqual(json.loads('1.7976931348623157e308'),float.fromhex('0x1.fffffffffffffp+1023'))

    def test_encoder_options_default_indent_sort_unicode_and_container_errors(self):
        class Array:
            def tolist(self):return [.1,-0.,[2.]]
        adapter.install()
        value={'z':Array(),'a':'한글'}
        encoded=json.dumps(value,default=lambda x:x.tolist(),allow_nan=False,
            indent=2,sort_keys=True,ensure_ascii=False,separators=(',',': '))
        self.assertIn('한글',encoded);self.assertTrue(encoded.startswith('{\n  "a"'))
        same_tree(self,{'z':[.1,-0.,[2.]],'a':'한글'},json.loads(encoded))
        circular=[];circular.append(circular)
        with self.assertRaises(ValueError):json.dumps(circular)
        with self.assertRaises(TypeError):json.dumps(object())
        self.assertEqual(json.loads(json.dumps({object():1},skipkeys=True)),{})

    def test_nonfinite_rejection_is_not_disabled_and_allow_nan_matches_standard(self):
        adapter.install()
        for value in (math.nan,math.inf,-math.inf):
            with self.assertRaises(ValueError):json.dumps([value],allow_nan=False)
        self.assertEqual(json.dumps([math.nan,math.inf,-math.inf]),'[NaN, Infinity, -Infinity]')
        def reject(text):raise ValueError('constant rejected')
        with self.assertRaisesRegex(ValueError,'constant rejected'):
            json.loads('NaN',parse_constant=reject)

    def test_loads_callbacks_bytes_bom_file_apis_and_decoder_errors(self):
        adapter.install()
        text='{"a":0.1,"b":2}'
        self.assertEqual(json.loads(text,parse_float=lambda value:('float',value),
            parse_int=lambda value:('int',value)),{'a':('float','0.1'),'b':('int','2')})
        self.assertEqual(json.loads(text,object_pairs_hook=tuple), (('a',.1),('b',2)))
        self.assertEqual(json.loads(text,object_hook=lambda value:list(value)),['a','b'])
        for value in (text,text.encode(),bytearray(text.encode()),text.encode('utf-16')):
            same_tree(self,{'a':.1,'b':2},json.loads(value))
        stream=io.StringIO();json.dump([.1,-0.],stream,allow_nan=False)
        stream.seek(0);same_tree(self,[.1,-0.],json.load(stream))
        same_tree(self,[.1],json.load(io.BytesIO(b'[0.1]')))
        for text in ('[1,]','{"a":}','0.1 trailing'):
            with self.assertRaises(json.JSONDecodeError):json.loads(text)

    def test_formatter_never_uses_original_encoder_or_float_subclass_format_hooks(self):
        class TrapFloat(float):
            def __repr__(self):raise AssertionError('float repr called')
            def __format__(self, spec):raise AssertionError('float format called')
            def __float__(self):raise AssertionError('float conversion override called')
            def as_integer_ratio(self):raise AssertionError('subclass ratio override called')
        adapter.install()
        with patch.object(json.encoder,'c_make_encoder',side_effect=AssertionError('C encoder called')), \
                patch.object(adapter._ENCODER,'iterencode',side_effect=AssertionError('original encoder called')):
            result=json.loads(json.dumps([TrapFloat(.1),TrapFloat(-0.)]))
        same_tree(self,[.1,-0.],result)

    def test_guard_runs_before_and_finally_after_and_restore_is_exact(self):
        before=(json.dumps,json.dump,json.loads,json.load,json.JSONEncoder,json.JSONDecoder,
                json._default_encoder,json._default_decoder,json.encoder.JSONEncoder,json.decoder.JSONDecoder)
        calls=[]
        guard=lambda:calls.append('guard')
        token=adapter.install(guard)
        self.assertIs(adapter.install(guard),token)
        json.dumps(.1);self.assertEqual(calls,['guard','guard'])
        calls.clear()
        with self.assertRaises(ValueError):json.dumps(math.nan,allow_nan=False)
        self.assertEqual(calls,['guard','guard'])
        with self.assertRaises(RuntimeError):adapter.install(lambda:None)
        adapter.restore(token)
        after=(json.dumps,json.dump,json.loads,json.load,json.JSONEncoder,json.JSONDecoder,
               json._default_encoder,json._default_decoder,json.encoder.JSONEncoder,json.decoder.JSONDecoder)
        self.assertTrue(all(a is b for a,b in zip(before,after)))
        with self.assertRaises(ValueError):adapter.restore(token)

    def test_abnormal_guard_fails_closed_before_serialization_without_reset(self):
        def guard():raise FloatingPointError('abnormal read-only FPU state')
        adapter.install(guard)
        with self.assertRaisesRegex(FloatingPointError,'abnormal read-only'):
            json.dumps([.1])

    def test_operation_and_after_guard_failure_preserves_primary_with_secondary_evidence(self):
        calls=[]
        def guard():
            calls.append('guard')
            if len(calls)==2:raise FloatingPointError('abnormal after JSON failure')
        adapter.install(guard)
        with self.assertRaises(TypeError) as error:json.dumps(object())
        self.assertIsInstance(error.exception.json_guard_error,FloatingPointError)
        self.assertEqual(str(error.exception.json_guard_error),'abnormal after JSON failure')
        self.assertEqual(calls,['guard','guard'])

    def test_float_dictionary_keys_rejected_in_nested_and_default_results(self):
        adapter.install()
        for value in ({.1:'changed string key'}, {'nested':[{1.:'float key'}]}):
            with self.assertRaisesRegex(TypeError,'floating dictionary keys'):
                json.dumps(value)
        with self.assertRaisesRegex(TypeError,'floating dictionary keys'):
            json.dumps(object(),default=lambda value:{'nested':{.1:'float key'}})
        self.assertEqual(json.loads(json.dumps({2:3,True:4,None:5})),{'2':3,'true':4,'null':5})

    def test_dragon4_matches_original_repr_on_boundaries_and_100k_random_float64(self):
        patterns=[0,1,2,0x000fffffffffffff,0x0010000000000000,0x7fefffffffffffff]
        for value in (1e-4,1e16,1.,.1):
            center=int.from_bytes(bits(value),'big')
            patterns += [center-1,center,center+1]
        patterns += [value | (1<<63) for value in patterns]
        rng=random.Random(735)
        patterns += [rng.getrandbits(64) for _ in range(100000)]
        for pattern in patterns:
            value=struct.unpack('>d',pattern.to_bytes(8,'big'))[0]
            if math.isfinite(value):
                self.assertEqual(adapter.float_token(value),float.__repr__(value))

    def test_old_contract_canonical_sha_bytes_match_sort_indent_default(self):
        root=Path(__file__).resolve().parents[2]
        folder=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1'
        paths=[folder/'single_a_bc_eval_v1/case_000/contract.json',
            root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_v1/training_contract.json']
        contracts=[json.loads(path.read_text()) for path in paths]
        # The default encoder must also retain exact text after NumPy conversion.
        contracts.append(dict(actual_contract=contracts[0],probe=np.array([.1,-0.,1e16,1e-5])))
        options=[dict(sort_keys=True),dict(sort_keys=True,indent=2),
                 dict(sort_keys=True,separators=(',',':'),allow_nan=False)]
        default=lambda value:value.tolist()
        expected=[[json.dumps(value,default=default,**option) for option in options] for value in contracts]
        adapter.install()
        for value,texts in zip(contracts,expected):
            for option,original in zip(options,texts):
                actual=json.dumps(value,default=default,**option)
                self.assertEqual(actual,original)
                self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(),hashlib.sha256(original.encode()).hexdigest())

    def test_actual_native_trace_roundtrips_exact_values(self):
        root=Path(__file__).resolve().parents[2]
        path=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1/single_a_bc_eval_v1/case_000/trace.jsonl.gz'
        with gzip.open(path,'rt') as stream:line=next(stream)
        original=json.loads(line)
        adapter.install()
        same_tree(self,original,json.loads(line))
        same_tree(self,original,json.loads(json.dumps(original,allow_nan=False)))


if __name__=='__main__':unittest.main()
