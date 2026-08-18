"""common.sendrequest 的请求异常传播回归测试。"""

import re

import pytest
import requests

from common.exceptions import RequestExecutionError
from common.sendrequest import SendRequest


@pytest.mark.parametrize(
    ("original_error", "message"),
    [
        pytest.param(
            requests.Timeout("read timed out"),
            "HTTP请求超时",
            id="timeout",
        ),
        pytest.param(
            requests.ConnectionError("connection refused"),
            "HTTP连接失败",
            id="connection-error",
        ),
        pytest.param(
            requests.RequestException("invalid request"),
            "HTTP请求执行失败",
            id="generic-request-error",
        ),
    ],
)
def test_send_request_raises_contextual_error_and_keeps_cause(
    monkeypatch,
    original_error,
    message,
):
    def fail_request(*args, **kwargs):
        raise original_error

    monkeypatch.setattr(requests.sessions.Session, "request", fail_request)
    requester = SendRequest()
    url = "https://example.test/users?token=secret-token"

    with pytest.raises(
        RequestExecutionError,
        match=re.escape(message),
    ) as exc_info:
        requester.send_request(method="get", url=url)

    error_text = str(exc_info.value)
    assert "method=GET" in error_text
    assert "https://example.test/users" in error_text
    assert "secret-token" not in error_text
    assert exc_info.value.__cause__ is original_error


@pytest.mark.parametrize(
    ("method_name", "request_error"),
    [
        pytest.param("get", requests.ConnectionError("get refused"), id="get"),
        pytest.param("post", requests.Timeout("post timed out"), id="post"),
    ],
)
def test_legacy_request_methods_no_longer_return_none(
    monkeypatch,
    method_name,
    request_error,
):
    def fail_request(*args, **kwargs):
        raise request_error

    monkeypatch.setattr(requests, method_name, fail_request)
    requester = SendRequest()

    with pytest.raises(RequestExecutionError) as exc_info:
        getattr(requester, method_name)(
            "https://example.test/legacy",
            None,
            {},
        )

    assert exc_info.value.__cause__ is request_error
