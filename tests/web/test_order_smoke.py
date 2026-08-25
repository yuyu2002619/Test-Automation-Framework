"""Core browser smoke path for the mock order system."""

import re

import pytest
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.order_page import OrderPage


@pytest.mark.web
@pytest.mark.smoke
def test_login_load_products_and_create_order(
    page: Page,
    web_base_url: str,
    web_credentials: tuple[str, str],
) -> None:
    login_page = LoginPage(page, web_base_url)
    login_page.open()
    login_page.login(*web_credentials)

    expect(page).to_have_url(f"{web_base_url}/ui/orders")

    order_page = OrderPage(page)
    expect(order_page.products_status).to_have_text("已加载 5 件商品")
    expect(order_page.product_select).to_be_enabled()

    order_page.select_product("33809635011")
    order_page.create_order(quantity=2)

    expect(order_page.order_message).to_have_text("提交订单成功")
    expect(order_page.order_number).to_have_text(re.compile(r"^\d{21}$"))
    expect(order_page.order_status).to_have_text("待支付")
