const comparisonConfig = {
    cpus: {
        listUrl: "/api/cpus",
        compareUrl: "/api/cpus/compare",
        labels: [
            ["cores_count", "Количество ядер", ""],
            ["threads_count", "Количество потоков", ""],
            ["clock_frequency", "Тактовая частота", " ГГц"],
        ],
    },
    gpus: {
        listUrl: "/api/gpus",
        compareUrl: "/api/gpus/compare",
        labels: [
            ["vram_type", "Тип видеопамяти", ""],
            ["vram_volume", "Объём видеопамяти", " ГБ"],
            ["vram_clock_frequency", "Частота видеопамяти", " МГц"],
            ["core_clock_frequency", "Частота графического ядра", " МГц"],
        ],
    },
};

async function readJson(response) {
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || `Ошибка HTTP ${response.status}`);
    }
    return data;
}

function setComparisonStatus(message, isError = false) {
    const status = document.getElementById("comparison-status");
    status.textContent = message;
    status.classList.toggle("status-error", isError);
}

function renderComparison(items, labels, kind) {
    const result = document.getElementById("comparison-result");
    result.replaceChildren();

    const heading = document.createElement("h2");
    heading.className = "result-heading";
    heading.textContent = "Результат сравнения";
    result.append(heading);

    const wrapper = document.createElement("div");
    wrapper.className = "table-scroll";
    const table = document.createElement("table");
    table.className = "comparison-table";
    const head = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const labelHeader = document.createElement("th");
    labelHeader.scope = "col";
    labelHeader.textContent = "Характеристика";
    headerRow.append(labelHeader);

    const imageKey = kind === "cpus" ? "cpu_image_dir_path" : "gpu_image_dir_path";
    const fallbackPath = "/static/images/site/base_specs_master_img.png";
    items.forEach((item) => {
        const cell = document.createElement("th");
        cell.scope = "col";
        const product = document.createElement("div");
        product.className = "comparison-product";
        const image = document.createElement("img");
        image.className = "comparison-product-image";
        image.alt = item.full_product_name;
        window.setSiteImage(image, item[imageKey], fallbackPath);
        const name = document.createElement("span");
        name.textContent = item.full_product_name;
        product.append(image, name);
        cell.append(product);
        headerRow.append(cell);
    });
    head.append(headerRow);
    table.append(head);

    const body = document.createElement("tbody");
    labels.forEach(([key, label, unit]) => {
        const row = document.createElement("tr");
        const name = document.createElement("th");
        name.scope = "row";
        name.textContent = label;
        row.append(name);
        items.forEach((item) => {
            const value = document.createElement("td");
            value.textContent = `${item[key]}${unit}`;
            row.append(value);
        });
        body.append(row);
    });
    table.append(body);
    wrapper.append(table);
    result.append(wrapper);
}

document.addEventListener("DOMContentLoaded", async () => {
    const kind = document.documentElement.dataset.componentKind;
    const config = comparisonConfig[kind];
    if (!config) {
        return;
    }

    const firstSelect = document.getElementById("component-one");
    const secondSelect = document.getElementById("component-two");
    const form = document.getElementById("comparison-form");
    const result = document.getElementById("comparison-result");

    try {
        const items = await readJson(await fetch(config.listUrl));
        [firstSelect, secondSelect].forEach((select) => {
            select.replaceChildren(new Option("Выберите модель...", ""));
            items.forEach((item) => {
                select.add(new Option(item.full_product_name, String(item.id)));
            });
        });
        setComparisonStatus(items.length ? "" : "В каталоге пока нет комплектующих.");
    } catch (error) {
        setComparisonStatus(error.message, true);
        [firstSelect, secondSelect].forEach((select) => {
            select.replaceChildren(new Option("Не удалось загрузить список", ""));
            select.disabled = true;
        });
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        result.replaceChildren();
        setComparisonStatus("Загружаем характеристики...");

        const params = new URLSearchParams({
            first_id: firstSelect.value,
            second_id: secondSelect.value,
        });
        try {
            const data = await readJson(await fetch(`${config.compareUrl}?${params}`));
            renderComparison(data.items, config.labels, kind);
            setComparisonStatus("");
        } catch (error) {
            setComparisonStatus(error.message, true);
        }
    });

    form.addEventListener("reset", () => {
        result.replaceChildren();
        setComparisonStatus("");
    });
});
