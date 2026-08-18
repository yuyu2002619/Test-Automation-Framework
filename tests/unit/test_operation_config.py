"""conf.operationConfig 的当前行为基线。"""

import configparser

from conf.operationConfig import OperationConfig


def make_config(tmp_path, content):
    config_file = tmp_path / "test-config.ini"
    config_file.write_text(content, encoding="utf-8")
    return config_file


def test_reads_report_type_and_api_host(tmp_path):
    config_file = make_config(
        tmp_path,
        """[REPORT_TYPE]
type = allure

[api_envi]
host = http://127.0.0.1:8787
""",
    )

    config = OperationConfig(str(config_file))

    assert config.type == "allure"
    assert config.get_section_for_data("api_envi", "host") == "http://127.0.0.1:8787"


def test_returns_empty_string_when_option_is_missing(tmp_path):
    config_file = make_config(tmp_path, "[REPORT_TYPE]\ntype = allure\n")
    config = OperationConfig(str(config_file))

    assert config.get_section_for_data("REPORT_TYPE", "missing") == ""


def test_writes_a_new_section_to_the_given_file(tmp_path):
    config_file = make_config(tmp_path, "[REPORT_TYPE]\ntype = allure\n")
    config = OperationConfig(str(config_file))

    config.write_config_data("api_envi", "host", "http://localhost:8787")

    reloaded = configparser.ConfigParser()
    reloaded.read(config_file, encoding="utf-8")
    assert reloaded.get("api_envi", "host") == "http://localhost:8787"


def test_existing_section_is_not_updated_current_behavior(tmp_path):
    config_file = make_config(
        tmp_path,
        "[REPORT_TYPE]\ntype = allure\n\n[api_envi]\nhost = old-host\n",
    )
    config = OperationConfig(str(config_file))

    config.write_config_data("api_envi", "timeout", "10")

    reloaded = configparser.ConfigParser()
    reloaded.read(config_file, encoding="utf-8")
    assert reloaded.get("api_envi", "host") == "old-host"
    assert not reloaded.has_option("api_envi", "timeout")
def test_returns_empty_string_when_section_is_missing_current_behavior(
    tmp_path,
):
    # Arrange：创建临时配置文件
    config_file = make_config(
        tmp_path,
        "[REPORT_TYPE]\ntype = allure\n",
    )
    config = OperationConfig(str(config_file))

    # Act：读取不存在的 Section
    result = config.get_section_for_data(
        "NOT_EXISTS",
        "host",
    )

    # Assert：记录当前行为
    assert result == ""


def test_environment_overrides_database_ini_value(tmp_path, monkeypatch):
    config_file = make_config(
        tmp_path,
        """[REPORT_TYPE]
type = allure

[MYSQL]
host = 127.0.0.1
""",
    )
    config = OperationConfig(str(config_file))
    monkeypatch.setenv('TAF_MYSQL_HOST', 'mysql.ci.internal')

    assert config.get_section_mysql('host') == 'mysql.ci.internal'
