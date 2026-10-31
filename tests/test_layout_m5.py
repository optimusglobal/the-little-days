import copy
import json
from pathlib import Path
import unittest
from workflow_v2.layout import validate

class LayoutM5Tests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((Path(__file__).parents[1] / 'workflow_v2/layout.contract.json').read_text())
        ref = self.contract['canonical_reference']
        row = [''] * 32
        row[0:2] = ['IDEA_TEST', 'https://drive.google.com/file/d/source/view']
        row[8] = row[11] = row[21] = False
        row[12] = 'https://drive.google.com/file/d/' + ref['drive_id'] + '/view'
        self.snapshot = {'spreadsheet_id':self.contract['spreadsheet_id'],
                         'headers':copy.deepcopy(self.contract['headers']), 'rows':[row],
                         'settings':{'canonical_reference_cell':'01_SAN_XUAT!M5',
                                     'canonical_reference_drive_id':ref['drive_id'],
                                     'canonical_reference_sha256':ref['sha256']}}

    def test_unchecked_admin_does_not_block_layout_or_certify_media(self):
        result = validate(self.snapshot, self.contract, 'IDEA_TEST')
        self.assertEqual(result['layout'], 'PASS')
        self.assertFalse(result['media_verified'])
        self.assertFalse(result['production_ready'])

    def test_old_l5_config_rejected(self):
        self.snapshot['settings']['canonical_reference_cell'] = '01_SAN_XUAT!L5'
        with self.assertRaisesRegex(ValueError, 'location'):
            validate(self.snapshot, self.contract, 'IDEA_TEST')

    def test_header_shift_rejected(self):
        self.snapshot['headers'][11], self.snapshot['headers'][12] = self.snapshot['headers'][12], self.snapshot['headers'][11]
        with self.assertRaisesRegex(ValueError, 'Headers'):
            validate(self.snapshot, self.contract, 'IDEA_TEST')

    def test_other_reference_rejected(self):
        self.snapshot['rows'][0][12] = 'https://drive.google.com/file/d/other/view'
        with self.assertRaisesRegex(ValueError, 'canonical Drive'):
            validate(self.snapshot, self.contract, 'IDEA_TEST')

    def test_duplicate_id_rejected(self):
        self.snapshot['rows'].append(copy.deepcopy(self.snapshot['rows'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate(self.snapshot, self.contract, 'IDEA_TEST')
