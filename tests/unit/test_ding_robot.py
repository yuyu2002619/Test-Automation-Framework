from unittest.mock import patch

import pytest

from common.dingRobot import generate_sign, send_dd_msg
from conf import setting


@patch('common.dingRobot.time.time', return_value=1700000000)
def test_generate_sign_uses_supplied_secret(mock_time):
    timestamp, sign = generate_sign('fake-secret')

    assert timestamp == '1700000000000'
    assert isinstance(sign, str)
    assert sign
    mock_time.assert_called_once()


def test_generate_sign_rejects_empty_secret():
    with pytest.raises(ValueError, match='Secret'):
        generate_sign('')


@patch('common.dingRobot.requests.post')
def test_send_dd_msg_uses_environment_and_does_not_send_real_request(mock_post, monkeypatch):
    monkeypatch.setenv('TAF_DINGTALK_WEBHOOK', 'https://example.test/fake-webhook')
    monkeypatch.setenv('TAF_DINGTALK_SECRET', 'fake-secret')
    mock_post.return_value.text = 'ok'

    result = send_dd_msg('测试消息', at_all=False)

    assert result == 'ok'
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == 'https://example.test/fake-webhook'
    assert kwargs['json']['text']['content'] == '测试消息'
    assert kwargs['json']['at']['isAtAll'] is False
    assert set(kwargs['params']) == {'timestamp', 'sign'}
    assert kwargs['timeout'] == setting.API_TIMEOUT
    assert kwargs['verify'] is setting.TLS_VERIFY


@patch('common.dingRobot.requests.post')
def test_send_dd_msg_requires_environment_credentials(mock_post, monkeypatch):
    monkeypatch.delenv('TAF_DINGTALK_WEBHOOK', raising=False)
    monkeypatch.delenv('TAF_DINGTALK_SECRET', raising=False)

    with pytest.raises(RuntimeError, match='TAF_DINGTALK_WEBHOOK'):
        send_dd_msg('测试消息')

    mock_post.assert_not_called()
