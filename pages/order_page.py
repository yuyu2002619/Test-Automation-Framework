"""Page Object for product loading and order creation."""

from playwright.sync_api import Page


class OrderPage:
    def __init__(self, page: Page):
        self.page = page
        self.products_status = page.get_by_test_id("products-status")
        self.product_select = page.get_by_test_id("product-select")
        self.quantity = page.get_by_test_id("quantity")
        self.create_order_button = page.get_by_test_id("create-order-button")
        self.order_message = page.get_by_test_id("order-message")
        self.order_number = page.get_by_test_id("order-number")
        self.order_status = page.get_by_test_id("order-status")

    def select_product(self, goods_id: str) -> None:
        self.product_select.select_option(goods_id)

    def create_order(self, quantity: int) -> None:
        self.quantity.fill(str(quantity))
        self.create_order_button.click()
