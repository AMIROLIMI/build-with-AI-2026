const API_BASE = 'http://localhost:8000';

class API {
    static async predictSale(data) {
        try {
            const response = await fetch(`${API_BASE}/api/predict/sale`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
                const errorMessage = typeof error.detail === 'string' ? error.detail : 
                                   (error.message || JSON.stringify(error) || 'Ошибка при прогнозировании');
                throw new Error(errorMessage);
            }
            
            return await response.json();
        } catch (error) {
            if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
                throw new Error('Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен на http://localhost:8000');
            }
            throw error;
        }
    }


    static async getDistricts() {
        const response = await fetch(`${API_BASE}/api/districts`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке районов');
        }
        return await response.json();
    }

    static async getStatistics() {
        const response = await fetch(`${API_BASE}/api/statistics`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка при загрузке статистики');
        }
        return await response.json();
    }
}

