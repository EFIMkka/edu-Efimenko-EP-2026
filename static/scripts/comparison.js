const comparisonConfig = {
    cpus: {
        listUrl: "/api/cpus",
        compareUrl: "/api/cpus/compare",
        performanceKeys: ["cores_count", "threads_count", "clock_frequency"],
        labels: [
            ["cores_count", "Количество ядер", ""],
            ["threads_count", "Количество потоков", ""],
            ["clock_frequency", "Тактовая частота", " ГГц"],
        ],
    },
    gpus: {
        listUrl: "/api/gpus",
        compareUrl: "/api/gpus/compare",
        performanceKeys: ["vram_volume", "vram_clock_frequency", "core_clock_frequency"],
        labels: [
            ["vram_type", "Тип видеопамяти", ""],
            ["vram_volume", "Объём видеопамяти", " ГБ"],
            ["vram_clock_frequency", "Частота видеопамяти", " МГц"],
            ["core_clock_frequency", "Частота графического ядра", " МГц"],
        ],
    },
};

function calculatePerformanceScores(items, performanceKeys) {
    if (items.length !== 2 || performanceKeys.length === 0) {
        throw new Error("Для оценки производительности нужны две модели и числовые показатели.");
    }

    const metricScores = items.map(() => []);
    performanceKeys.forEach((key) => {
        const values = items.map((item) => Number(item[key]));
        if (values.some((value) => !Number.isFinite(value) || value < 0)) {
            throw new Error(`Не удалось рассчитать производительность по показателю «${key}».`);
        }

        const bestValue = Math.max(...values);
        items.forEach((_, index) => {
            metricScores[index].push(bestValue === 0 ? 100 : values[index] / bestValue * 100);
        });
    });

    const averageScores = metricScores.map(
        (scores) => scores.reduce((sum, score) => sum + score, 0) / scores.length
    );
    const bestAverage = Math.max(...averageScores);
    if (bestAverage === 0) {
        return items.map(() => 100);
    }

    return averageScores.map((score) => Math.round(score / bestAverage * 100));
}

window.calculatePerformanceScores = calculatePerformanceScores;
let performanceChart;

function destroyPerformanceChart() {
    if (performanceChart) {
        performanceChart.destroy();
        performanceChart = undefined;
    }
}

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
    destroyPerformanceChart();
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

    renderPerformanceChart(result, items, comparisonConfig[kind].performanceKeys);
}

function renderPerformanceChart(result, items, performanceKeys) {
    const section = document.createElement("section");
    section.className = "performance-panel";

    const heading = document.createElement("h2");
    heading.className = "result-heading";
    heading.textContent = "Общая производительность";

    const description = document.createElement("p");
    description.className = "performance-description";
    description.textContent =
        "Среднее по числовым характеристикам с одинаковым весом; лучшая из двух моделей принята за 100%.";

    const scores = calculatePerformanceScores(items, performanceKeys);
    const chartContainer = document.createElement("div");
    chartContainer.className = "performance-chart-container";
    const canvas = document.createElement("canvas");
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "Горизонтальная диаграмма относительной производительности комплектующих");
    chartContainer.append(canvas);

    const scoreList = document.createElement("ul");
    scoreList.className = "performance-score-list";
    items.forEach((item, index) => {
        const entry = document.createElement("li");
        const name = document.createElement("span");
        name.textContent = item.full_product_name;
        const score = document.createElement("strong");
        score.textContent = `${scores[index]}%`;
        entry.append(name, score);
        scoreList.append(entry);
    });
    section.append(heading, description, chartContainer, scoreList);

    if (typeof window.Chart !== "function") {
        const error = document.createElement("p");
        error.className = "performance-chart-error";
        error.setAttribute("role", "status");
        error.textContent = "Не удалось загрузить библиотеку диаграммы. Обновите страницу и попробуйте ещё раз.";
        section.append(error);
    } else {
        const scoreLabels = {
            id: "performanceScoreLabels",
            afterDatasetsDraw(chart) {
                const { ctx } = chart;
                const bars = chart.getDatasetMeta(0).data;
                ctx.save();
                ctx.font = "700 12px Inter, Segoe UI, Arial, sans-serif";
                ctx.textBaseline = "middle";
                bars.forEach((bar, index) => {
                    const label = `${scores[index]}%`;
                    const barWidth = bar.x - chart.scales.x.left;
                    const textWidth = ctx.measureText(label).width;
                    if (barWidth > textWidth + 18) {
                        ctx.fillStyle = "#ffffff";
                        ctx.textAlign = "right";
                        ctx.fillText(label, bar.x - 9, bar.y);
                    } else {
                        ctx.fillStyle = "#166534";
                        ctx.textAlign = "left";
                        ctx.fillText(label, bar.x + 9, bar.y);
                    }
                });
                ctx.restore();
            },
        };

        performanceChart = new window.Chart(canvas, {
            type: "bar",
            data: {
                labels: items.map((item) => item.full_product_name),
                datasets: [{
                    label: "Индекс производительности",
                    data: scores,
                    backgroundColor: scores.map((score) => score === 100 ? "#16a34a" : "#86c99b"),
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 34,
                }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 350 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `Производительность: ${context.parsed.x}%`,
                        },
                    },
                },
                scales: {
                    x: {
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: "Производительность, %",
                            color: "#64736a",
                            font: { family: "Inter, Segoe UI, Arial, sans-serif", weight: "600" },
                        },
                        ticks: {
                            stepSize: 10,
                            callback: (value) => `${value}%`,
                            color: "#64736a",
                        },
                        grid: { color: "#e8eee9" },
                        border: { display: false },
                    },
                    y: {
                        ticks: { color: "#17241b", font: { weight: "600" } },
                        grid: { display: false },
                        border: { display: false },
                    },
                },
            },
            plugins: [scoreLabels],
        });
    }

    result.append(section);
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
        destroyPerformanceChart();
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
        destroyPerformanceChart();
        result.replaceChildren();
        setComparisonStatus("");
    });
});
