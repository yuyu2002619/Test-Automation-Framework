from common.security import redact_sensitive, redact_text, redact_url


def test_redact_sensitive_returns_safe_copy():
    source = {
        'Authorization': 'Bearer real-token',
        'nested': {'password': 'real-password', 'name': 'tester'},
    }

    result = redact_sensitive(source)

    assert result == {
        'Authorization': '<redacted>',
        'nested': {'password': '<redacted>', 'name': 'tester'},
    }
    assert source['nested']['password'] == 'real-password'


def test_redact_url_and_response_text_hide_tokens():
    safe_url = redact_url('https://example.test/api?access_token=real-token&page=1')
    safe_text = redact_text('{"token": "real-token", "code": 0}')

    assert 'real-token' not in safe_url
    assert 'page=1' in safe_url
    assert 'real-token' not in safe_text
    assert '<redacted>' in safe_text
