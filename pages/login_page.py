"""Page Object for the mock order-system login page."""

from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.username = page.get_by_test_id("username")
        self.password = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error_message = page.get_by_test_id("login-error")

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/ui/login")

    def login(self, username: str, password: str) -> None:
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()
