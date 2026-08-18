"""common.readyaml 的当前行为基线。"""

import pytest
import yaml

from common.exceptions import TestDataError, YamlLoadError
from common.readyaml import ReadYamlData, get_testcase_yaml


def write_yaml(tmp_path, content, name="case.yaml"):
    yaml_file = tmp_path / name
    yaml_file.write_text(content, encoding="utf-8")
    return yaml_file


def test_single_interface_yaml_expands_each_test_case(tmp_path):
    yaml_file = write_yaml(
        tmp_path,
        """- baseInfo:
    api_name: 查询用户
    url: /users
    method: GET
  testCase:
    - case_name: 正常查询
      params: {id: 1}
    - case_name: 用户不存在
      params: {id: 999}
""",
    )

    result = get_testcase_yaml(str(yaml_file))

    assert len(result) == 2
    assert result[0][0]["api_name"] == "查询用户"
    assert result[0][1]["case_name"] == "正常查询"
    assert result[1][1]["case_name"] == "用户不存在"


def test_business_yaml_with_multiple_steps_is_returned_unchanged(tmp_path):
    yaml_file = write_yaml(
        tmp_path,
        """- baseInfo: {api_name: 登录, url: /login, method: POST}
  testCase:
    - {case_name: 登录成功}
- baseInfo: {api_name: 下单, url: /orders, method: POST}
  testCase:
    - {case_name: 下单成功}
""",
    )

    result = get_testcase_yaml(str(yaml_file))

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["baseInfo"]["api_name"] == "登录"
    assert result[1]["baseInfo"]["api_name"] == "下单"


@pytest.mark.parametrize(
    ("case_name", "content", "missing_file", "error_type", "message"),
    [
        pytest.param(
            "empty",
            "",
            False,
            TestDataError,
            "YAML文件内容为空",
            id="empty-yaml",
        ),
        pytest.param(
            "invalid",
            "baseInfo: [",
            False,
            YamlLoadError,
            "YAML语法解析失败",
            id="invalid-yaml",
        ),
        pytest.param(
            "missing",
            "",
            True,
            YamlLoadError,
            "YAML文件不存在",
            id="missing-file",
        ),
        pytest.param(
            "empty-list",
            "[]\n",
            False,
            TestDataError,
            "YAML测试用例列表不能为空",
            id="empty-list-yaml",
        ),
    ],
)
def test_invalid_yaml_inputs_raise_specific_errors(
    tmp_path,
    case_name,
    content,
    missing_file,
    error_type,
    message,
):
    yaml_file = tmp_path / f"{case_name}.yaml"
    if not missing_file:
        yaml_file.write_text(content, encoding="utf-8")

    with pytest.raises(error_type, match=message):
        get_testcase_yaml(str(yaml_file))


@pytest.mark.parametrize(
    ("content", "message"),
    [
        pytest.param(
            "baseInfo: {}\ntestCase: []\n",
            "YAML根节点必须是list",
            id="root-is-dict",
        ),
        pytest.param(
            "- testCase:\n    - {case_name: 缺少baseInfo}\n",
            "缺少baseInfo",
            id="missing-base-info",
        ),
        pytest.param(
            "- baseInfo: {api_name: 缺少testCase}\n",
            "缺少testCase",
            id="missing-test-case",
        ),
    ],
)
def test_testcase_yaml_rejects_invalid_top_level_structure(
    tmp_path,
    content,
    message,
):
    yaml_file = write_yaml(tmp_path, content)

    with pytest.raises(TestDataError, match=message):
        get_testcase_yaml(str(yaml_file))


def test_invalid_yaml_keeps_parser_error_as_cause(tmp_path):
    yaml_file = write_yaml(tmp_path, "baseInfo: [")

    with pytest.raises(YamlLoadError) as exc_info:
        get_testcase_yaml(str(yaml_file))

    assert isinstance(exc_info.value.__cause__, yaml.YAMLError)


def test_read_yaml_data_preserves_nested_python_types(tmp_path):
    yaml_file = write_yaml(
        tmp_path,
        """user:
  id: 7
  roles:
    - tester
    - admin
enabled: true
""",
    )

    result = ReadYamlData(str(yaml_file)).get_yaml_data

    assert isinstance(result, dict)
    assert result["user"]["id"] == 7
    assert result["user"]["roles"] == ["tester", "admin"]
    assert result["enabled"] is True
