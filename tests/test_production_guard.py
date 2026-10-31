"""P0 regression tests, written before production changes. No network, browser, or render."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from production_guard import check_timeline, authorize_submission, record_attempt, GuardError

class ProductionGuardTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        self._control_tmp = TemporaryDirectory()
        self.addCleanup(self._control_tmp.cleanup)
        root = Path(self._control_tmp.name)
        (root / '.initialized').write_text('ready', encoding='utf8')
        p = patch('production_guard.CONTROL_ROOT', root)
        p.start()
        self.addCleanup(p.stop)

    def test_script_prompt_duration_conflict(self):
        with self.assertRaises(GuardError):
            check_timeline("One continuous shot. 12 seconds.", "MASTER — 16 seconds. Cut to close-up.")
    def test_unapproved_cut_in_continuous_shot(self):
        with self.assertRaises(GuardError):
            check_timeline("12s, one continuous shot.", "12 seconds. Cut to close-up.")
    def test_dialogue_not_silently_dropped(self):
        with self.assertRaises(GuardError):
            check_timeline('8s. Daughter: "Mama, no." Mother: "No?"',
                           '8 seconds. Daughter: "Mama, no."')
    def test_matching_scene(self):
        check_timeline('12s. One continuous shot. Daughter: "Mama, no."',
                       '12 seconds. Single continuous shot. Daughter says "Mama, no."')
    def test_hyphenated_duration_is_recognized(self):
        with self.assertRaisesRegex(GuardError, 'duration mismatch'):
            check_timeline('12s. Daughter: "Hi"', 'A 16-second film. Daughter says "Hi"')

    def test_duration_spellings_agree(self):
        check_timeline('12s. Daughter: "Hi"', 'A 12-second film. Daughter says "Hi"')

    def test_blocked_vietnamese_status(self):
        from production_guard import check_production_status
        with self.assertRaises(GuardError):
            check_production_status('Bị chặn')
        with self.assertRaises(GuardError):
            check_production_status('On-Hold')
        check_production_status('Sẵn sàng')

    def test_cli_uses_packet_segment_not_missing_args_segment(self):
        from pathlib import Path
        source = Path('run_browser.py').read_text(encoding='utf8')
        self.assertIn("ap.add_argument('--segment'", source)
        self.assertNotIn('reserve_submission(Path(args.runtime), args.idea, args.segment', source)
        self.assertIn("reserve_submission(Path(args.runtime), args.idea, packet['segment_id'], job.key, True, args.revision_approved)", source)

    def test_historical_lock_blocks_idea_even_with_permission(self):
        import json
        from production_guard import check_historical_lock
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            from production_guard import CONTROL_ROOT
            hold=CONTROL_ROOT/'historical-locks'
            hold.mkdir()
            (hold/'IDEA_002.json').write_text(json.dumps({'idea_id':'IDEA_002','status':'unreconciled'}),encoding='utf-8')
            with self.assertRaises(GuardError):
                check_historical_lock(root,'IDEA_002')
            check_historical_lock(root,'IDEA_001')

    def test_switching_runtime_cannot_bypass_central_lock(self):
        from production_guard import CONTROL_ROOT
        import json
        marker=CONTROL_ROOT/'historical-locks'/'IDEA_002.json'
        marker.parent.mkdir(parents=True,exist_ok=True)
        marker.write_text(json.dumps({'status':'unreconciled'}),encoding='utf8')
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            for runtime in (first, second):
                with self.assertRaisesRegex(GuardError,'Historical render'):
                    authorize_submission(Path(runtime),'IDEA_002','01',True,True)

    def test_atomic_reservation_budget_revision_and_replay(self):
        from production_guard import reserve_submission, CONTROL_ROOT
        import json
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaisesRegex(GuardError,'confirmation'):
                reserve_submission(root,'IDEA_X','01','key1',False,False)
            reserve_submission(root,'IDEA_X','01','key1',True,False)
            with self.assertRaisesRegex(GuardError,'Same render key'):
                reserve_submission(root,'IDEA_X','01','key1',True,True)
            with self.assertRaisesRegex(GuardError,'Revision'):
                reserve_submission(root,'IDEA_X','01','key2',True,False)
            reserve_submission(root,'IDEA_X','01','key2',True,True)
            with self.assertRaisesRegex(GuardError,'budget'):
                reserve_submission(root,'IDEA_X','01','key3',True,True)
            p=CONTROL_ROOT/'render-ledger'/'IDEA_X_01.json'
            self.assertEqual(len(json.loads(p.read_text())['attempts']),2)

    def test_atomic_lock_and_runtime_change(self):
        from production_guard import reserve_submission, CONTROL_ROOT
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            reserve_submission(first,'IDEA_Y','01','key1',True,False)
            with self.assertRaisesRegex(GuardError,'Revision'):
                reserve_submission(second,'IDEA_Y','01','key2',True,False)
            p=CONTROL_ROOT/'render-ledger'/'IDEA_Y_01.lock'
            p.write_text('busy')
            with self.assertRaisesRegex(GuardError,'Another submission'):
                reserve_submission(second,'IDEA_Y','01','key2',True,True)

    def test_explicit_authorization_required(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(GuardError):
                authorize_submission(Path(tmp), "IDEA_002", "01", False, False)
    def test_revision_requires_extra_approval_and_budget(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            authorize_submission(root, "IDEA_002", "01", True, False)
            record_attempt(root, "IDEA_002", "01", "key1")
            with self.assertRaises(GuardError):
                authorize_submission(root, "IDEA_002", "01", True, False)
            authorize_submission(root, "IDEA_002", "01", True, True)
            record_attempt(root, "IDEA_002", "01", "key2")
            with self.assertRaises(GuardError):
                authorize_submission(root, "IDEA_002", "01", True, True)
    def test_same_key_cannot_submit_twice(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            record_attempt(root, "IDEA_002", "01", "same-key")
            with self.assertRaises(GuardError):
                record_attempt(root, "IDEA_002", "01", "same-key")

if __name__ == "__main__":
    unittest.main()
