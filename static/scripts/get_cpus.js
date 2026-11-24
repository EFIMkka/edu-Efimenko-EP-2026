async function getCpuList() {
    try {
        const response = await fetch('/api/cpus');

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

getCpuList();