import tempfile
import unittest
from pathlib import Path
from production_guard import GuardError
from owner_challenge_ledger import claim_challenge

class ChallengeLedgerTests(unittest.TestCase):
    def test_one_time_claim(self):
        with tempfile.TemporaryDirectory() as d:
            challenge="a"*64
            self.assertTrue(claim_challenge(d,challenge))
            self.assertTrue((Path(d)/(challenge+".spent")).is_file())
            with self.assertRaises(GuardError): claim_challenge(d,challenge)
    def test_requires_existing_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(GuardError): claim_challenge(Path(d)/"absent","a"*64)
    def test_rejects_invalid_challenge(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(GuardError): claim_challenge(d,"unsafe/../challenge")
if __name__=="__main__": unittest.main()
