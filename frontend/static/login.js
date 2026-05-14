const form = document.getElementById("loginForm");
const username = document.getElementById("username");
const password = document.getElementById("password");
const button = document.getElementById("loginButton");
const message = document.getElementById("loginMessage");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";
  button.disabled = true;

  try {
    const response = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    });

    if (!response.ok) {
      message.textContent = "账号或密码不正确";
      return;
    }

    window.location.href = "/dashboard";
  } catch (error) {
    message.textContent = "登录失败，请稍后重试";
  } finally {
    button.disabled = false;
  }
});
