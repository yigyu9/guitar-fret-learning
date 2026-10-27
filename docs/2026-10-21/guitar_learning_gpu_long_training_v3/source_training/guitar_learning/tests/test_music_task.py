import unittest
from guitar_learning.music_task import ScoreTask, ScoreTarget, MusicLedger


def target(identity='a',onset=.1,end=.2,fret=5,finger=1,string=0):
    return ScoreTarget(identity,identity,string,fret,finger,1,onset,end,0.,onset,end)


class MusicTests(unittest.TestCase):
    def test_expiration_does_not_require_fake_release(self):
        task = ScoreTask((target(),),capacity=1)
        ledger = MusicLedger(task)
        rows,mask,ids = task.tokens(10,{},ledger)
        self.assertFalse(any(mask))
        self.assertFalse(ledger.progress['a'].released)

    def test_final_release_window_remains_visible_then_expires(self):
        task = ScoreTask((target(onset=.1,end=1.),))
        ledger = MusicLedger(task)
        geometry = {'a':dict(delta=[0.,0.,0.],velocity=[0.,0.,0.])}
        for now in (1.,1.05,1.1):
            rows,mask,identities = task.tokens(now,geometry,ledger)
            self.assertTrue(mask[0])
            self.assertEqual(identities[0],'a')
            self.assertAlmostEqual(rows[0][1],1.-now)
        self.assertFalse(any(task.tokens(1.100001,{},ledger)[1]))
        self.assertFalse(ledger.progress['a'].released)

    def test_release_requires_end_and_measured_contact(self):
        task=ScoreTask((target(),)); ledger=MusicLedger(task)
        with self.assertRaises(ValueError): ledger.release('a',.3)
        ledger.update_interval(.1,.15,{'a'})
        with self.assertRaises(ValueError): ledger.release('a',.15)
        ledger.release('a',.21)
        self.assertTrue(ledger.progress['a'].released)

    def test_short_note_fractional_hold(self):
        task=ScoreTask((target(onset=.001,end=.0242),)); ledger=MusicLedger(task)
        ledger.update_interval(0,.03,{'a'})
        self.assertAlmostEqual(ledger.progress['a'].held_s,.0232)

    def test_conflict_and_missing_geometry_overflow(self):
        with self.assertRaises(ValueError): ScoreTask((target(),target('b',fret=6)))
        task=ScoreTask((target(),)); ledger=MusicLedger(task)
        with self.assertRaises(KeyError): task.tokens(0,{},ledger)
        task=ScoreTask((target(),target('b',string=1)),capacity=1)
        with self.assertRaises(ValueError): task.tokens(0,{},MusicLedger(task))

    def test_windows_and_duplicate_crossing(self):
        task=ScoreTask((target(),)); ledger=MusicLedger(task)
        result=ledger.crossing('x',.175,0,1,{'a'})
        self.assertNotIn(.05,result); self.assertEqual(result[.1],'a')
        with self.assertRaises(ValueError): ledger.crossing('x',.175,0,1,{'a'})

    def test_real_bundle(self):
        root='data/song_bundles/05_BN2-131-B_solo'
        for stage in ('B','C','D'):
            task=ScoreTask.from_bundle(root,stage=stage)
            self.assertTrue(task.targets)
        # Full mode must either preserve every event or explicitly reject source
        # conflicts/unsupported events. It cannot silently choose a short phrase.
        try:
            task=ScoreTask.from_bundle(root,stage='full')
        except ValueError as exc:
            self.assertTrue(any(x in str(exc) for x in ('unsupported','conflicting','mapping','timing')))
        else:
            self.assertEqual(task.provenance['stage'],'full')
            self.assertGreater(len(task.targets),8)

if __name__=='__main__': unittest.main()
