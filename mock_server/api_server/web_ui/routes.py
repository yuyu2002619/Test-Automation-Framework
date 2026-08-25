"""Routes for the small order-system UI used by Playwright smoke tests."""

from flask import Blueprint, redirect, render_template, url_for


web_ui = Blueprint(
    "web_ui",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)


@web_ui.get("/")
def index():
    """Send users entering /ui to the login page."""

    return redirect(url_for("web_ui.login"))


@web_ui.get("/login")
def login():
    """Render the login page for the mock order system."""

    return render_template("login.html")


@web_ui.get("/orders")
def orders():
    """Render the product selection and order creation page."""

    return render_template("orders.html")
