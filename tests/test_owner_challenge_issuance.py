import tempfile
import unittest
from pathlib import Path
from production_guard import GuardError
from owner_challenge_issuance import issue_challenge, validate_issued_challenge

class ChallengeIssuanceTests(unittest.TestCase):
    def test_unique_and_valid_with_expiry(self):
        with tempfile.TemporaryDirectory() as directory:
            first=issue_challenge(directory,now=1000,ttl_seconds=120)
            second=issue_challenge(directory,now=1000,ttl_seconds=120)
            self.assertNotEqual(first["challenge"],second["challenge"])
            self.assertTrue(validate_issued_challenge(directory,first["challenge"],now=1119))
            with self.assertRaises(GuardError):
                validate_issued_challenge(directory,first["challenge"],now=1120)
            with self.assertRaises(GuardError):
                validate_issued_challenge(directory,first["challenge"],now=999)
    def test_missing_record_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(GuardError):
                validate_issued_challenge(directory,"a"*64,now=1000)
    def test_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            record=issue_challenge(directory,now=1000)
            p=Path(directory)/(record["challenge"]+".issued")
            p.write_text("{}")
            with self.assertRaises(GuardError):
                validate_issued_challenge(directory,record["challenge"],now=1001)
    def test_invalid_ttl_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for ttl in (0,901,True):
                with self.assertRaises(GuardError):
                    issue_challenge(directory,ttl_seconds=ttl)
if __name__=="__main__":
    unittest.main()
