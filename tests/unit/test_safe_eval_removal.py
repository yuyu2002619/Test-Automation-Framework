"""Day 50：去除 eval 后的结构化数据回归测试。"""

import json

import pytest

import base.apiutil as single_apiutil
import base.apiutil_business as business_apiutil


class FakeResponse:
    status_code = 200
    text = json.dumps({"msg_code": 200}, ensure_ascii=False)

    def json(self):
        return {"msg_code": 200}


class RecordingRunner:
    def __init__(self):
        self.calls = []

    def run_main(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse()


class RecordingAssertions:
    def __init__(self):
        self.calls = []

    def assert_result(self, validation, response, status_code):
        self.calls.append((validation, response, status_code))


def build_single_request_base():
    request_base = object.__new__(single_apiutil.RequestBase)
    request_base.conf = object()
    request_base.run = RecordingRunner()
    request_base.asserts = RecordingAssertions()
    return request_base


def build_business_request_base():
    request_base = object.__new__(business_apiutil.RequestBase)
    request_base.conf = object()
    request_base.run = RecordingRunner()
    return request_base


@pytest.fixture
def isolate_framework_side_effects(monkeypatch):
    monkeypatch.setattr(single_apiutil.allure, "attach", lambda *args, **kwargs: None)
    monkeypatch.setattr(single_apiutil.setting, "get_api_base_url", lambda conf: "http://mock.test")
    monkeypatch.setattr(business_apiutil.setting, "get_api_base_url", lambda conf: "http://mock.test")


@pytest.mark.parametrize(
    "request_base_class",
    [single_apiutil.RequestBase, business_apiutil.RequestBase],
    ids=["single-interface", "business-interface"],
)
@pytest.mark.parametrize(
    "structured_data",
    [
        pytest.param([], id="empty-list"),
        pytest.param({}, id="empty-dict"),
        pytest.param(
            [{"eq": {"enabled": True, "value": None}}],
            id="nested-validation-list",
        ),
    ],
)
def test_replace_load_preserves_dict_and_list_types(
    request_base_class,
    structured_data,
):
    request_base = object.__new__(request_base_class)

    result = request_base.replace_load(structured_data)

    assert result == structured_data
    assert type(result) is type(structured_data)


def test_single_executor_passes_structured_cookie_and_validation(
    isolate_framework_side_effects,
):
    request_base = build_single_request_base()
    base_info = {
        "api_name": "Cookie和断言回归",
        "url": "/users",
        "method": "GET",
        "header": {"Accept": "application/json"},
        "cookies": {"session_id": "abc123"},
    }
    test_case = {
        "case_name": "结构化数据不依赖eval",
        "validation": [{"eq": {"msg_code": 200}}],
    }

    request_base.specification_yaml(base_info, test_case)

    assert request_base.run.calls[0]["cookies"] == {"session_id": "abc123"}
    validation, response, status_code = request_base.asserts.calls[0]
    assert validation == [{"eq": {"msg_code": 200}}]
    assert isinstance(validation, list)
    assert response == {"msg_code": 200}
    assert status_code == 200


def test_single_executor_rejects_string_cookie(
    isolate_framework_side_effects,
):
    request_base = build_single_request_base()
    base_info = {
        "api_name": "Cookie类型校验",
        "url": "/users",
        "method": "GET",
        "header": {},
        "cookies": "{'session_id': 'abc123'}",
    }
    test_case = {
        "case_name": "Cookie不允许写成Python字面量字符串",
        "validation": [{"eq": {"msg_code": 200}}],
    }

    with pytest.raises(TypeError, match=r"baseInfo\.cookies.*dict"):
        request_base.specification_yaml(base_info, test_case)


def test_business_executor_passes_structured_validation(
    isolate_framework_side_effects,
    monkeypatch,
):
    request_base = build_business_request_base()
    assertions = RecordingAssertions()
    monkeypatch.setattr(business_apiutil, "assert_res", assertions)
    case_info = {
        "baseInfo": {
            "api_name": "业务断言回归",
            "url": "/orders",
            "method": "POST",
            "header": {"Content-Type": "application/json"},
            "cookies": {"session_id": "abc123"},
        },
        "testCase": [
            {
                "case_name": "业务执行器不依赖eval",
                "json": {"order_id": 1001},
                "validation": [{"eq": {"msg_code": 200}}],
            }
        ],
    }

    request_base.specification_yaml(case_info)

    assert request_base.run.calls[0]["cookies"] == {"session_id": "abc123"}
    validation, response, status_code = assertions.calls[0]
    assert validation == [{"eq": {"msg_code": 200}}]
    assert isinstance(validation, list)
    assert response == {"msg_code": 200}
    assert status_code == 200


@pytest.mark.parametrize("executor", ["single", "business"])
@pytest.mark.parametrize(
    ("validation", "error_type", "message"),
    [
        pytest.param([], ValueError, "validation不能为空", id="empty-list"),
        pytest.param({}, TypeError, "validation必须是list", id="empty-dict"),
        pytest.param([{}], TypeError, "validation每一项都必须是非空dict", id="empty-item"),
    ],
)
def test_executor_rejects_empty_or_invalid_validation(
    executor,
    validation,
    error_type,
    message,
    isolate_framework_side_effects,
):
    if executor == "single":
        request_base = build_single_request_base()
        base_info = {
            "api_name": "validation结构校验",
            "url": "/users",
            "method": "GET",
            "header": {},
        }
        test_case = {"case_name": "validation不合法", "validation": validation}
        call = lambda: request_base.specification_yaml(base_info, test_case)
    else:
        request_base = build_business_request_base()
        case_info = {
            "baseInfo": {
                "api_name": "validation结构校验",
                "url": "/orders",
                "method": "POST",
                "header": {},
            },
            "testCase": [
                {"case_name": "validation不合法", "validation": validation}
            ],
        }
        call = lambda: request_base.specification_yaml(case_info)

    with pytest.raises(error_type, match=message):
        call()


@pytest.mark.parametrize("executor", ["single", "business"])
def test_executor_rejects_missing_validation(
    executor,
    isolate_framework_side_effects,
):
    if executor == "single":
        request_base = build_single_request_base()
        base_info = {
            "api_name": "validation缺失校验",
            "url": "/users",
            "method": "GET",
            "header": {},
        }
        call = lambda: request_base.specification_yaml(
            base_info,
            {"case_name": "缺少validation"},
        )
    else:
        request_base = build_business_request_base()
        case_info = {
            "baseInfo": {
                "api_name": "validation缺失校验",
                "url": "/orders",
                "method": "POST",
                "header": {},
            },
            "testCase": [{"case_name": "缺少validation"}],
        }
        call = lambda: request_base.specification_yaml(case_info)

    with pytest.raises(ValueError, match="缺少validation字段"):
        call()


@pytest.mark.parametrize(
    ("executor", "case_factory"),
    [
        pytest.param(
            "single",
            lambda payload: (
                {
                    "api_name": "单接口恶意字符串回归",
                    "url": "/users",
                    "method": "GET",
                    "header": {},
                },
                {"case_name": "恶意validation", "validation": payload},
            ),
            id="single-interface",
        ),
        pytest.param(
            "business",
            lambda payload: {
                "baseInfo": {
                    "api_name": "业务恶意字符串回归",
                    "url": "/orders",
                    "method": "POST",
                    "header": {},
                },
                "testCase": [
                    {"case_name": "恶意validation", "validation": payload}
                ],
            },
            id="business-interface",
        ),
    ],
)
def test_validation_string_is_rejected_without_code_execution(
    executor,
    case_factory,
    isolate_framework_side_effects,
    tmp_path,
):
    marker_file = tmp_path / f"{executor}-eval-executed.txt"
    payload = (
        "__import__('pathlib').Path("
        f"{str(marker_file)!r}"
        ").write_text('executed', encoding='utf-8')"
    )

    if executor == "single":
        request_base = build_single_request_base()
        base_info, test_case = case_factory(payload)
        call = lambda: request_base.specification_yaml(base_info, test_case)
    else:
        request_base = build_business_request_base()
        case_info = case_factory(payload)
        call = lambda: request_base.specification_yaml(case_info)

    with pytest.raises(TypeError, match=r"validation.*list"):
        call()

    assert not marker_file.exists()
