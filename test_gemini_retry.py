import io,json,unittest
from unittest.mock import patch
from urllib.error import HTTPError,URLError
import gemini_idea_review as g
def failure(code, retry_after=None):
    h={} if retry_after is None else {'Retry-After':retry_after}
    return HTTPError('https://example.invalid',code,'failure',h,io.BytesIO(json.dumps({'error':{'status':'UNAVAILABLE','message':'temporary SECRET'}}).encode()))
class RetryTests(unittest.TestCase):
    @patch.object(g,'key',return_value='SECRET')
    def test_transient_then_success(self,k):
        response=unittest.mock.MagicMock()
        response.__enter__.return_value=io.StringIO('{"ok":true}')
        with patch.object(g,'urlopen',side_effect=[failure(503),response]) as call,patch.object(g.time,'sleep') as sleep:
            self.assertTrue(g.api('models',attempts=4)['ok']); self.assertEqual(call.call_count,2); sleep.assert_called_once()
    @patch.object(g,'key',return_value='SECRET')
    def test_quota_not_retried(self,k):
        with patch.object(g,'urlopen',side_effect=failure(429)) as call,patch.object(g.time,'sleep') as sleep:
            with self.assertRaises(HTTPError): g.api('models')
            self.assertEqual(call.call_count,1); sleep.assert_not_called()
    @patch.object(g,'key',return_value='SECRET')
    def test_bounded_retries(self,k):
        with patch.object(g,'urlopen',side_effect=[failure(503) for _ in range(4)]) as call,patch.object(g.time,'sleep'):
            with self.assertRaises(HTTPError): g.api('models')
            self.assertEqual(call.call_count,4)
    @patch.object(g,'key',return_value='SECRET')
    def test_network_uncertainty_not_retried(self,k):
        with patch.object(g,'urlopen',side_effect=URLError('timeout')) as call:
            with self.assertRaises(URLError): g.api('models')
            self.assertEqual(call.call_count,1)
    @patch.object(g,'key',return_value='SECRET')
    def test_secret_redacted(self,k):
        self.assertNotIn('SECRET',g.error_info(failure(503))['message'])
    def test_long_retry_after_stops(self):
        self.assertIsNone(g.retry_delay(0,'120'))
    def test_retry_after_respected(self):
        self.assertGreaterEqual(g.retry_delay(0,'20'),20)
if __name__=='__main__': unittest.main()
