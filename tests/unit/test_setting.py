import pytest

from conf import setting
from conf.operationConfig import OperationConfig


def make_config(tmp_path, content):
    config_file = tmp_path / 'test-setting.ini'
    config_file.write_text(content, encoding='utf-8')
    return config_file


@pytest.mark.parametrize(
    ('raw_value', 'expected'),
    [('true', True), ('YES', True), ('0', False), (' off ', False)],
)
def test_get_env_bool_parses_supported_values(monkeypatch, raw_value, expected):
    monkeypatch.setenv('TAF_TEST_BOOL', raw_value)

    assert setting.get_env_bool('TAF_TEST_BOOL', not expected) is expected


def test_get_env_bool_uses_default_and_rejects_invalid_value(monkeypatch):
    monkeypatch.delenv('TAF_TEST_BOOL', raising=False)
    assert setting.get_env_bool('TAF_TEST_BOOL', True) is True

    monkeypatch.setenv('TAF_TEST_BOOL', 'sometimes')
    with pytest.raises(ValueError, match='TAF_TEST_BOOL'):
        setting.get_env_bool('TAF_TEST_BOOL', True)


def test_get_env_int_converts_and_validates(monkeypatch):
    monkeypatch.setenv('TAF_TEST_INT', ' 30 ')
    assert setting.get_env_int('TAF_TEST_INT', 60) == 30

    monkeypatch.setenv('TAF_TEST_INT', 'abc')
    with pytest.raises(ValueError, match='TAF_TEST_INT'):
        setting.get_env_int('TAF_TEST_INT', 60)

    monkeypatch.setenv('TAF_TEST_INT', '0')
    with pytest.raises(ValueError, match='不能小于'):
        setting.get_env_int('TAF_TEST_INT', 60)


def test_api_base_url_env_overrides_ini_without_modifying_file(tmp_path, monkeypatch):
    original_content = """[REPORT_TYPE]
type = allure

[api_envi]
host = http://127.0.0.1:8787
"""
    config_file = make_config(tmp_path, original_content)
    config = OperationConfig(str(config_file))
    monkeypatch.setenv('TAF_API_BASE_URL', 'https://test.example.com')

    result = setting.get_api_base_url(config)

    assert result == 'https://test.example.com'
    assert config_file.read_text(encoding='utf-8') == original_content


def test_api_base_url_uses_ini_then_default(tmp_path, monkeypatch):
    monkeypatch.delenv('TAF_API_BASE_URL', raising=False)
    config_file = make_config(
        tmp_path,
        '[REPORT_TYPE]\ntype = allure\n\n[api_envi]\nhost = http://127.0.0.1:9000\n',
    )
    assert setting.get_api_base_url(OperationConfig(str(config_file))) == 'http://127.0.0.1:9000'

    empty_host_file = make_config(
        tmp_path,
        '[REPORT_TYPE]\ntype = allure\n\n[api_envi]\nhost =\n',
    )
    assert setting.get_api_base_url(OperationConfig(str(empty_host_file))) == 'http://127.0.0.1:8787'


def test_api_base_url_rejects_explicit_empty_environment_value(tmp_path, monkeypatch):
    config_file = make_config(
        tmp_path,
        '[REPORT_TYPE]\ntype = allure\n\n[api_envi]\nhost = http://127.0.0.1:8787\n',
    )
    config = OperationConfig(str(config_file))
    monkeypatch.setenv('TAF_API_BASE_URL', '   ')

    with pytest.raises(ValueError, match='TAF_API_BASE_URL'):
        setting.get_api_base_url(config)
