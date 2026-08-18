"""common.assertions 的当前行为基线。"""

import pytest

from common.assertions import Assertions


@pytest.fixture(autouse=True)
def disable_allure_attachments(monkeypatch):
    monkeypatch.setattr(
        "common.assertions.allure.attach",
        lambda *args, **kwargs: None,
    )


@pytest.mark.parametrize(
    ("expected_status", "actual_status", "expected_flag"),
    [
        pytest.param(200, 200, 0, id="status-matches"),
        pytest.param(201, 200, 1, id="status-does-not-match"),
    ],
)
def test_contains_assert_compares_status_code(
    expected_status, actual_status, expected_flag
):
    result = Assertions().contains_assert(
        {"status_code": expected_status},
        {"message": "ok"},
        actual_status,
    )

    assert result == expected_flag


def test_contains_assert_finds_text_in_a_nested_field():
    response = {"data": {"message": "订单提交成功"}}

    result = Assertions().contains_assert(
        {"message": "成功"},
        response,
        200,
    )

    assert result == 0


@pytest.mark.parametrize(
    ("expected", "actual", "expected_flag"),
    [
        pytest.param({"code": "0000"}, {"code": "0000"}, 0, id="equal"),
        pytest.param({"code": "0000"}, {"code": "4000"}, 1, id="not-equal"),
    ],
)
def test_equal_assert_for_one_field(expected, actual, expected_flag):
    assert Assertions().equal_assert(expected, actual) == expected_flag


def test_equal_assert_with_multiple_fields_fails_current_behavior():
    expected = {"code": "0000", "message": "成功"}
    actual = {"code": "0000", "message": "成功", "data": {}}

    assert Assertions().equal_assert(expected, actual) == 1


def test_contains_missing_field_raises_type_error_current_behavior():
    # jsonpath 在没有匹配项时返回 False，当前实现随后访问 False[0]。
    with pytest.raises(TypeError, match="not subscriptable"):
        Assertions().contains_assert(
            {"orderId": "ORDER-1"},
            {"message": "ok"},
            200,
        )


def test_response_any_missing_field_returns_success_current_behavior():
    result = Assertions().assert_response_any(
        {"message": "ok"},
        {"orderId": "ORDER-1"},
    )

    assert result == 0


def test_equal_assert_rejects_non_dictionary_inputs():
    with pytest.raises(TypeError, match="必须为字典类型"):
        Assertions().equal_assert({"code": "0000"}, "not-a-dict")


def test_response_time_requires_strictly_less_than_expected():
    assertion = Assertions()

    assert assertion.assert_response_time(0.19, 0.2) is True
    with pytest.raises(AssertionError):
        assertion.assert_response_time(0.2, 0.2)

def test_assert_result_raises_when_one_assertion_fails():
    expected = [
        {
            "eq": {
                "code": "0000",
            }
        }
    ]
    response = {
        "code": "4000",
    }

    with pytest.raises(AssertionError):
        Assertions().assert_result(
            expected,
            response,
            200,
        )
