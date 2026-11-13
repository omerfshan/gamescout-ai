import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gamescout_ai.application.discovery import discover
from gamescout_ai.domain.models import Scope, ValidationError
from gamescout_ai.infrastructure.json_source import load_file, parse_payload, MAX_FILE_BYTES


class DiscoveryTests(unittest.TestCase):
    def payload(self):
        return json.loads((Path(__file__).resolve().parents[1] / 'fixtures/discovery-demo.json').read_text())

    def test_unknown_profile_kept_by_default(self):
        result = discover(parse_payload(self.payload()), Scope('ios'))
        self.assertEqual(result.returned_count, 1)
        self.assertEqual(result.games[0].developer_profile, 'unknown')

    def test_filters_and_truncation(self):
        games = parse_payload(self.payload())
        result = discover(games, Scope('android', 1))
        self.assertEqual(result.matched_count, 2)
        self.assertEqual(result.returned_count, 1)
        self.assertTrue(any('kesildi' in warning for warning in result.warnings))
        self.assertEqual(discover(games, Scope('android', genre='racing')).returned_count, 1)
        self.assertEqual(discover(games, Scope('android', developer_profile='unknown')).status, 'insufficient_data')

    def test_duplicate_conflicts(self):
        payload = self.payload()
        payload['games'].append(copy.deepcopy(payload['games'][0]))
        self.assertEqual(discover(parse_payload(payload), Scope('android')).deduplicated_count, 3)
        payload['games'][-1]['title'] = 'conflict'
        with self.assertRaises(ValidationError) as caught:
            discover(parse_payload(payload), Scope('android'))
        self.assertEqual(caught.exception.code, 'CONFLICTING_DUPLICATE')

    def test_invalid_scope_types_and_bounds(self):
        for value in (True, 0, 21, 1.5, '10'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Scope('android', value)

    def test_strict_game_fields(self):
        for field, value in [('game_id', True), ('title', ' '), ('normalized_genres', ['puzzle', 1]), ('platform', 'web')]:
            payload = self.payload()
            payload['games'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                parse_payload(payload)

    def test_count_limit(self):
        payload = self.payload()
        payload['games'] = [payload['games'][0]] * 1001
        with self.assertRaises(ValidationError) as caught:
            parse_payload(payload)
        self.assertEqual(caught.exception.code, 'TOO_MANY_GAMES')

    def test_file_bound_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            for content, code in [(b'x' * (MAX_FILE_BYTES + 1), 'FILE_TOO_LARGE'), (b'{', 'INVALID_JSON'), (b'\xff', 'INVALID_JSON'), (b'{"x":NaN}', 'INVALID_JSON')]:
                path.write_bytes(content)
                with self.subTest(code=code), self.assertRaises(ValidationError) as caught:
                    load_file(path)
                self.assertEqual(caught.exception.code, code)
            with self.assertRaises(ValidationError) as caught:
                load_file(path.parent / 'missing.json')
            self.assertEqual(caught.exception.code, 'FILE_UNAVAILABLE')

    def test_empty_payload_is_insufficient_data(self):
        payload = self.payload()
        payload['games'] = []
        self.assertEqual(discover(parse_payload(payload), Scope('android')).status, 'insufficient_data')


if __name__ == '__main__':
    unittest.main()
