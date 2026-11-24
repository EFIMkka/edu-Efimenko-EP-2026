async function accountRequest(url, method, payload) {
    const options = { method, headers: {} };
    if (payload) {
        if (payload instanceof FormData) {
            options.body = payload;
        } else {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(payload);
        }
    }

    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || `Ошибка HTTP ${response.status}`);
    }
    return data;
}

function showAccountStatus(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    if (!element) {
        return;
    }
    element.textContent = message;
    element.classList.toggle("status-error", isError);
}

function bindAuthForm(formId, statusId, endpoint, fields, successMessage, multipart = false) {
    const form = document.getElementById(formId);
    if (!form) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = multipart
            ? new FormData(form)
            : Object.fromEntries(
                fields.map((field) => [field, form.elements.namedItem(field).value])
            );
        showAccountStatus(statusId, "Обрабатываем запрос...");
        try {
            await accountRequest(endpoint, "POST", payload);
            showAccountStatus(statusId, successMessage);
            window.location.assign("/lk");
        } catch (error) {
            showAccountStatus(statusId, error.message, true);
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    bindAuthForm(
        "login-form",
        "login-status",
        "/api/auth/login",
        ["email", "password"],
        "Вход выполнен."
    );
    bindAuthForm(
        "register-form",
        "register-status",
        "/api/auth/register",
        ["nickname", "email", "password"],
        "Аккаунт создан.",
        true
    );

    const profilePanel = document.getElementById("profile-panel");
    const loginRequired = document.getElementById("login-required");
    if (!profilePanel || !loginRequired) {
        return;
    }

    try {
        const data = await accountRequest("/api/auth/me", "GET");
        if (!data.user) {
            return;
        }

        loginRequired.hidden = true;
        profilePanel.hidden = false;
        document.getElementById("profile-nickname").textContent = data.user.nickname;
        document.getElementById("profile-email").textContent = data.user.email;
        document.getElementById("profile-role").textContent =
            data.user.role === "admin" ? "Администратор" : "Пользователь";
        document.getElementById("profile-admin-link").hidden = data.user.role !== "admin";
        window.setSiteImage(
            document.getElementById("profile-avatar"),
            data.user.avatar_dir_path,
            "/static/images/users/base_user_img.png"
        );
    } catch (error) {
        showAccountStatus("account-status", error.message, true);
    }

    document.getElementById("logout-button").addEventListener("click", async () => {
        try {
            await accountRequest("/api/auth/logout", "POST");
            window.location.assign("/");
        } catch (error) {
            showAccountStatus("account-status", error.message, true);
        }
    });

    document.getElementById("avatar-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        showAccountStatus("avatar-status", "Загружаем аватар...");
        try {
            const result = await accountRequest(
                "/api/auth/avatar",
                "PUT",
                new FormData(form)
            );
            window.setSiteImage(
                document.getElementById("profile-avatar"),
                result.user.avatar_dir_path,
                "/static/images/users/base_user_img.png",
                true
            );
            form.reset();
            showAccountStatus("avatar-status", "Аватар обновлён.");
        } catch (error) {
            showAccountStatus("avatar-status", error.message, true);
        }
    });
});
