"""Fixtures that isolate and configure Playwright Web smoke tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def clear_extract():
    """Override the root fixture so Web tests do not mutate extract.yaml."""


@pytest.fixture(scope="session")
def web_base_url() -> str:
    return os.getenv("TAF_WEB_BASE_URL", "http://127.0.0.1:8787").rstrip("/")


@pytest.fixture(scope="session")
def web_credentials() -> tuple[str, str]:
    return (
        os.getenv("TAF_WEB_USERNAME", "test123"),
        os.getenv("TAF_WEB_PASSWORD", "qwe666"),
    )


@pytest.fixture(autouse=True)
def preserve_mock_order_state():
    """Restore the file-backed order state after every browser test."""

    project_root = Path(__file__).resolve().parents[2]
    order_state = (
        project_root
        / "mock_server"
        / "api_server"
        / "data"
        / "mockdata"
        / "orderNumber.json"
    )
    original = order_state.read_bytes()
    try:
        yield
    finally:
        order_state.write_bytes(original)
