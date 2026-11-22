async function getGpuList() {
    try {
        const response = await fetch('/api/gpus');

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const data = await response.json();

        console.log('Response:', data);
    }
    catch (error) {
        console.error('Cant connect with API:', error);
    }
}

getGpuList();