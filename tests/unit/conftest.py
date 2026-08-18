"""Day 48 单元测试的隔离边界。"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def clear_extract():
    """覆盖根目录同名 Fixture，禁止单元测试清空真实 extract.yaml。"""


@pytest.fixture(autouse=True)
def forbid_external_services(monkeypatch):
    """任何意外的 HTTP 或数据库访问都应该立即让单元测试失败。"""

    def blocked_http(*args, **kwargs):
        raise AssertionError("unit tests must not send HTTP requests")

    def blocked_database(*args, **kwargs):
        raise AssertionError("unit tests must not connect to a real database")

    monkeypatch.setattr("requests.sessions.Session.request", blocked_http)
    monkeypatch.setattr("common.assertions.ConnectMysql", blocked_database)
