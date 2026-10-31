import unittest
from production_guard import GuardError
from github_review_evidence import verify_github_review

class GitHubEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.commit="a"*40
        self.run={"id":123,"head_sha":self.commit,"status":"completed","conclusion":"success",
                  "actor":{"login":"Committer"}}
        self.approvals=[{"state":"approved","user":{"login":"Reviewer"},
                         "environments":[{"name":"human-approval"}]}]
    def verify(self):
        return verify_github_review(self.run,self.approvals,expected_commit=self.commit)
    def test_independent_reviewer(self):
        self.assertEqual("Reviewer",self.verify()["reviewer"])
    def test_self_review_rejected(self):
        self.approvals[0]["user"]["login"]="Committer"
        with self.assertRaises(GuardError): self.verify()
    def test_case_insensitive_self_review_rejected(self):
        self.approvals[0]["user"]["login"]="COMMITTER"
        with self.assertRaises(GuardError): self.verify()
    def test_wrong_commit_rejected(self):
        self.run["head_sha"]="b"*40
        with self.assertRaises(GuardError): self.verify()
    def test_failed_run_rejected(self):
        self.run["conclusion"]="failure"
        with self.assertRaises(GuardError): self.verify()
    def test_wrong_environment_rejected(self):
        self.approvals[0]["environments"][0]["name"]="other"
        with self.assertRaises(GuardError): self.verify()
    def test_rejected_approval_rejected(self):
        self.approvals[0]["state"]="rejected"
        with self.assertRaises(GuardError): self.verify()
    def test_missing_actor_rejected(self):
        self.run["actor"]={}
        with self.assertRaises(GuardError): self.verify()

if __name__=="__main__": unittest.main()
