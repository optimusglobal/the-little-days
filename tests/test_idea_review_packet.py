import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.prepare_idea_review import atomic_json, binding, prepare, sha

class IdeaReviewPacketTests(unittest.TestCase):
    def test_source_content_changes_binding(self):
        self.assertNotEqual(binding({'gpt_idea':'a'}, 'source1', 'ref'),
                            binding({'gpt_idea':'a'}, 'source2', 'ref'))

    def test_gpt_revision_changes_binding(self):
        self.assertNotEqual(binding({'gpt_idea':'a'}, 'source', 'ref'),
                            binding({'gpt_idea':'b'}, 'source', 'ref'))

    def test_atomic_replace_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'packet.json'
            atomic_json(path, {'a': 1})
            before = sha(path)
            atomic_json(path, {'a': 2})
            self.assertEqual(json.loads(path.read_text()), {'a': 2})
            self.assertNotEqual(before, sha(path))
            self.assertEqual(list(Path(tmp).glob('*.tmp')), [])

    def test_wrong_reference_rejected_before_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ref = Path(tmp)/'source', Path(tmp)/'ref'
            source.write_bytes(b'source')
            ref.write_bytes(b'wrong image')
            with patch('runner.plan', return_value=[{'gpt_idea':'draft'}]), \
                 patch('pilot_workflow.contract', return_value={
                     'configuration_snapshot': {'canonical_reference_sha256':'expected'}}), \
                 patch('subprocess.run') as process:
                with self.assertRaisesRegex(ValueError, 'canonical L5'):
                    prepare({}, {}, 'IDEA_TEST', source, ref, tmp)
                process.assert_not_called()

    def test_unsafe_id_rejected_before_files(self):
        with patch('runner.plan', return_value=[{'gpt_idea':'draft'}]):
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                prepare({}, {}, '../escape', 'none', 'none', 'none')
