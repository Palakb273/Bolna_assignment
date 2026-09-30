import copy
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import bolna_common as common
import configure_agent
import create_test_call

AGENT = '11111111-1111-4111-8111-111111111111'
EXECUTION = '22222222-2222-4222-8222-222222222222'
PHONE = '+12025550123'  # Synthetic, never sent to a real network.
SECRET = 'sentinel-private-token'


class PayloadTests(unittest.TestCase):
    def test_missing_blank_placeholder_and_header_injection_rejected(self):
        for value in ['', '  ', 'your_bolna_api_key', 'token\r\nInjected: value']:
            with self.subTest(value=value), patch.dict(os.environ, {'BOLNA_API_KEY': value}):
                with self.assertRaises(ValueError) as error:
                    common.required_env('BOLNA_API_KEY')
                if value.strip():
                    self.assertNotIn(value, str(error.exception))
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                common.required_env('BOLNA_API_KEY')

    def test_valid_key_read_without_normalization(self):
        with patch.dict(os.environ, {'BOLNA_API_KEY': SECRET}):
            self.assertEqual(common.required_env('BOLNA_API_KEY'), SECRET)

    def test_agent_payload_injects_policy_into_both_languages_without_mutation(self):
        config = json.loads((ROOT / 'config/agent.json').read_text(encoding='utf-8'))
        original = copy.deepcopy(config)
        payload = common.build_agent_payload(config, 'Shared policy', 'हिंदी निर्देश')
        self.assertEqual(config, original)
        self.assertEqual(payload['agent_prompts']['task_1']['system_prompt'], 'Shared policy')
        languages = payload['agent_config']['tasks'][0]['tools_config']['multilingual_config']['languages']
        self.assertEqual(languages['en']['system_prompt'], 'Shared policy')
        self.assertEqual(languages['hi']['system_prompt'], 'Shared policy\n\nहिंदी निर्देश')

    def test_broken_config_and_empty_prompt_rejected(self):
        with self.assertRaises(ValueError):
            common.build_agent_payload({}, 'policy')
        config = json.loads((ROOT / 'config/agent.json').read_text(encoding='utf-8'))
        with self.assertRaises(ValueError):
            common.build_agent_payload(config, ' ')
        config['agent_config']['tasks'][0]['task_config']['hangup_after_silence'] = 5
        with self.assertRaises(ValueError):
            common.build_agent_payload(config, 'policy')

    def test_call_payload_has_only_documented_required_fields(self):
        self.assertEqual(common.build_call_payload(AGENT, PHONE),
                         {'agent_id': AGENT, 'recipient_phone_number': PHONE})

    def test_invalid_recipient_or_agent_fails_without_echoing(self):
        for phone in ['9876543210', '+0123', '+91 99999', '+１２３４５６７８９', PHONE + '\n']:
            with self.subTest(phone=phone), self.assertRaises(ValueError):
                common.build_call_payload(AGENT, phone)
        for agent in ['your_agent_id', AGENT + '\n', 'bad']:
            with self.subTest(agent=agent), self.assertRaises(ValueError):
                common.build_call_payload(agent, PHONE)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('bolna_common.build_opener')
        self.factory = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.opener = self.factory.return_value

    def response(self, body):
        response = self.opener.open.return_value.__enter__.return_value
        response.status = 200
        response.read.return_value = body

    def test_single_https_post_with_bearer_and_timeout(self):
        self.response(json.dumps({'execution_id': EXECUTION}).encode())
        result = common.post_json('/call', common.build_call_payload(AGENT, PHONE), SECRET)
        self.assertEqual(result, {'execution_id': EXECUTION})
        self.assertEqual(self.opener.open.call_count, 1)
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.bolna.ai/call')
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.get_header('Authorization'), 'Bearer ' + SECRET)
        self.assertEqual(json.loads(request.data), {'agent_id': AGENT, 'recipient_phone_number': PHONE})
        self.assertEqual(self.opener.open.call_args.kwargs['timeout'], 30)

    def test_timeout_is_not_retried_and_reports_unknown_submission(self):
        self.opener.open.side_effect = TimeoutError(SECRET)
        with self.assertRaises(RuntimeError) as error:
            common.post_json('/call', {}, SECRET)
        self.assertEqual(self.opener.open.call_count, 1)
        self.assertIn('unknown', str(error.exception))
        self.assertNotIn(SECRET, str(error.exception))

    def test_http_and_network_errors_are_sanitized_and_not_retried(self):
        for failure in [HTTPError('https://private', 401, SECRET, {}, io.BytesIO(SECRET.encode())),
                        HTTPError('https://private', 500, SECRET, {}, io.BytesIO(SECRET.encode())),
                        URLError(SECRET)]:
            with self.subTest(failure=type(failure).__name__):
                self.opener.open.reset_mock()
                self.opener.open.side_effect = failure
                with self.assertRaises(RuntimeError) as error:
                    common.post_json('/call', {}, SECRET)
                self.assertNotIn(SECRET, str(error.exception))
                self.assertEqual(self.opener.open.call_count, 1)

    def test_redirect_handler_refuses_new_destination(self):
        self.response(b'{}')
        common.post_json('/call', {}, SECRET)
        handler = next(arg for arg in self.factory.call_args.args
                       if isinstance(arg, common.NoRedirect))
        self.assertIsNone(handler.redirect_request(None, None, 302, '', {}, 'https://other.example'))

    def test_malformed_or_nonobject_response_is_safe(self):
        for body in [SECRET.encode(), b'[]', b'null', b'\xff']:
            with self.subTest(body=body):
                self.response(body)
                with self.assertRaises(RuntimeError) as error:
                    common.post_json('/call', {}, SECRET)
                self.assertNotIn(SECRET, str(error.exception))

    def test_external_url_and_unsupported_path_rejected_before_network(self):
        for path in ['https://evil.example', '//evil.example', '/delete', '/call?key=secret']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                common.post_json(path, {}, SECRET)
        self.factory.assert_not_called()


class CommandTests(unittest.TestCase):
    def run_command(self, module, args, env=None, response=None):
        output = io.StringIO()
        with patch.dict(os.environ, env or {}, clear=True), patch('bolna_common.build_opener') as network:
            network.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps(response or {}).encode()
            network.return_value.open.return_value.__enter__.return_value.status = 200
            with redirect_stdout(output), redirect_stderr(output):
                code = module.main(args)
            return code, output.getvalue(), network

    def test_configure_dry_run_needs_no_credentials_and_never_calls(self):
        code, output, network = self.run_command(configure_agent, [])
        self.assertEqual(code, 0)
        self.assertIn('No request sent', output)
        network.assert_not_called()

    def test_call_dry_run_validates_but_never_sends(self):
        code, output, network = self.run_command(create_test_call, ['--to', PHONE], {'BOLNA_AGENT_ID': AGENT})
        self.assertEqual(code, 0)
        self.assertNotIn(PHONE, output)
        network.assert_not_called()

    def test_execute_missing_key_fails_without_network(self):
        code, output, network = self.run_command(create_test_call, ['--to', PHONE, '--execute'], {'BOLNA_AGENT_ID': AGENT})
        self.assertEqual(code, 1)
        self.assertIn('BOLNA_API_KEY', output)
        network.assert_not_called()

    def test_execute_call_sends_once_and_prints_only_identifier(self):
        code, output, network = self.run_command(create_test_call, ['--to', PHONE, '--execute'],
            {'BOLNA_AGENT_ID': AGENT, 'BOLNA_API_KEY': SECRET},
            {'execution_id': EXECUTION, 'message': SECRET, 'status': 'queued'})
        self.assertEqual(code, 0)
        self.assertIn(EXECUTION, output)
        self.assertNotIn(SECRET, output)
        self.assertNotIn(PHONE, output)
        self.assertEqual(network.return_value.open.call_count, 1)

    def test_create_agent_sends_once_and_prints_agent_id(self):
        code, output, network = self.run_command(configure_agent, ['--execute'], {'BOLNA_API_KEY': SECRET},
            {'agent_id': AGENT, 'state': 'created', 'version_id': EXECUTION})
        self.assertEqual(code, 0)
        self.assertIn(AGENT, output)
        self.assertEqual(network.return_value.open.call_count, 1)
        request = network.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.bolna.ai/v2/agent')

    def test_missing_or_unsafe_success_identifier_is_not_printed(self):
        for value in [None, EXECUTION + '\n' + SECRET, SECRET]:
            with self.subTest(value=value):
                code, output, network = self.run_command(create_test_call, ['--to', PHONE, '--execute'],
                    {'BOLNA_AGENT_ID': AGENT, 'BOLNA_API_KEY': SECRET}, {'execution_id': value})
                self.assertEqual(code, 1)
                self.assertNotIn(SECRET, output)
                self.assertIn('unknown', output)
                self.assertEqual(network.return_value.open.call_count, 1)


if __name__ == '__main__':
    unittest.main()
