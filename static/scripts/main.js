window.setSiteImage = (image, storedPath, fallbackPath, refresh = false) => {
    const isLocalImagePath =
        typeof storedPath === "string" &&
        storedPath.startsWith("images/") &&
        !storedPath.split("/").includes("..");
    const imagePath = isLocalImagePath ? `/static/${storedPath}` : fallbackPath;
    let usingFallback = !isLocalImagePath;

    image.hidden = false;
    image.onerror = () => {
        if (!usingFallback) {
            usingFallback = true;
            image.src = fallbackPath;
        } else {
            image.hidden = true;
        }
    };
    image.src = refresh && isLocalImagePath
        ? `${imagePath}?v=${Date.now()}`
        : imagePath;
};

document.addEventListener("DOMContentLoaded", async () => {
    const profileLink = document.querySelector(".profile-link");
    if (!profileLink) {
        return;
    }

    try {
        const response = await fetch("/api/auth/me");
        if (!response.ok) {
            throw new Error(`Не удалось проверить аккаунт: HTTP ${response.status}`);
        }

        const data = await response.json();
        if (!data.user) {
            return;
        }

        profileLink.textContent = "Личный кабинет";
        if (data.user.role === "admin") {
            const adminLink = document.createElement("a");
            adminLink.className = "nav-admin-link";
            adminLink.href = "/admin";
            adminLink.textContent = "Админ-панель";
            profileLink.parentElement.append(adminLink);
        }
    } catch (error) {
        console.error("Не удалось загрузить сведения об аккаунте:", error);
    }
});
