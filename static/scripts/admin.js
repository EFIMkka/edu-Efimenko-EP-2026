function setAdminStatus(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.classList.toggle("status-error", isError);
}

function bindComponentForm(formId, statusId, endpoint, componentLabel) {
    const form = document.getElementById(formId);
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        setAdminStatus(statusId, "Сохраняем комплектующую...");

        try {
            const response = await fetch(endpoint, {
                method: "POST",
                body: new FormData(form),
            });
            const data = await response.json();
            if (!response.ok) {
                const detail = Array.isArray(data.detail)
                    ? data.detail.map((issue) => issue.msg).join("; ")
                    : data.detail;
                throw new Error(detail || `Ошибка HTTP ${response.status}`);
            }
            form.reset();
            setAdminStatus(
                statusId,
                `${componentLabel} «${data.full_product_name}» добавлен. Техническое имя: ${data.technical_name}.`
            );
        } catch (error) {
            setAdminStatus(statusId, error.message, true);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindComponentForm(
        "admin-cpu-form",
        "cpu-admin-status",
        "/api/admin/cpus",
        "Процессор"
    );
    bindComponentForm(
        "admin-gpu-form",
        "gpu-admin-status",
        "/api/admin/gpus",
        "Видеокарта"
    );
});
