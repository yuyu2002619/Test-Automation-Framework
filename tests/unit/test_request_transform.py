"""变量替换和响应提取的当前行为基线。"""

import json

import pytest

from base.apiutil import RequestBase


class FakeDebugTalk:
    values = {
        "token": "abc123",
        "userId": 7,
        "goodsIds": ["G01", "G02"],
    }

    def get_extract_data(self, name):
        return self.values[name]


class SpyYamlWriter:
    def __init__(self):
        self.records = []

    def write_yaml_data(self, value):
        self.records.append(value)


@pytest.fixture
def request_base():
    """跳过 RequestBase.__init__，避免构造与本方法无关的真实依赖。"""

    return object.__new__(RequestBase)


@pytest.fixture
def fake_debugtalk(monkeypatch):
    monkeypatch.setattr("base.apiutil.DebugTalk", FakeDebugTalk)


def test_replaces_one_placeholder_in_a_string(request_base, fake_debugtalk):
    result = request_base.replace_load("Bearer ${get_extract_data(token)}")

    assert result == "Bearer abc123"


def test_replaces_placeholder_inside_a_dict_and_keeps_dict_type(
    request_base, fake_debugtalk
):
    result = request_base.replace_load(
        {"userId": "${get_extract_data(userId)}", "enabled": True}
    )

    assert result == {"userId": "7", "enabled": True}
    assert isinstance(result, dict)


def test_replaces_multiple_placeholders_from_left_to_right(
    request_base, fake_debugtalk
):
    result = request_base.replace_load(
        "token=${get_extract_data(token)}&user=${get_extract_data(userId)}"
    )

    assert result == "token=abc123&user=7"
    assert "${" not in result


def test_list_replacement_is_joined_with_commas_current_behavior(
    request_base, fake_debugtalk
):
    result = request_base.replace_load("${get_extract_data(goodsIds)}")

    assert result == "G01,G02"


def test_jsonpath_single_value_is_written_to_the_spy(request_base):
    writer = SpyYamlWriter()
    request_base.read = writer
    response = json.dumps({"orderNumber": "ORDER-10001"})

    request_base.extract_data({"orderNumber": "$.orderNumber"}, response)

    assert writer.records == [{"orderNumber": "ORDER-10001"}]


def test_missing_single_value_is_swallowed_current_behavior(request_base):
    writer = SpyYamlWriter()
    request_base.read = writer
    response = json.dumps({"order": {}})

    request_base.extract_data({"orderNumber": "$.orderNumber"}, response)

    assert writer.records == []


def test_empty_jsonpath_list_writes_a_message_current_behavior(request_base):
    writer = SpyYamlWriter()
    request_base.read = writer
    response = json.dumps({"goodsList": []})

    request_base.extract_data_list(
        {"goodsIds": "$.goodsList[*].goodsId"},
        response,
    )

    assert writer.records == [
        {"goodsIds": "未提取到数据，该接口返回结果可能为空"}
    ]


def test_regex_single_value_is_written_to_the_spy(request_base):
    writer = SpyYamlWriter()
    request_base.read = writer

    request_base.extract_data(
        {"orderNumber": r'"orderNumber":"(.+?)"'},
        '{"orderNumber":"ORDER-20001"}',
    )

    assert writer.records == [{"orderNumber": "ORDER-20001"}]
