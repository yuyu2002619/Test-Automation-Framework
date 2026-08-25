const form = document.querySelector('[data-testid="login-form"]');
const usernameInput = document.querySelector('[data-testid="username"]');
const passwordInput = document.querySelector('[data-testid="password"]');
const loginButton = document.querySelector('[data-testid="login-button"]');
const errorMessage = document.querySelector('[data-testid="login-error"]');

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorMessage.textContent = "";
    loginButton.disabled = true;
    loginButton.textContent = "登录中……";

    try {
        const response = await fetch("/coupApply/cms/login_dw", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                username: usernameInput.value.trim(),
                password: passwordInput.value,
            }),
        });

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload.success !== true) {
            throw new Error(payload.error || payload.msg || "用户名或密码错误");
        }

        sessionStorage.setItem("taf_user_token", payload.data?.user_token || "mock-token");
        window.location.assign("/ui/orders");
    } catch (error) {
        errorMessage.textContent = error.message || "登录失败，请稍后重试";
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "登录";
    }
});
