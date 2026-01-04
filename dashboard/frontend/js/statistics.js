const API_BASE = 'http://localhost:8000';

async function loadGraphs() {
    const container = document.getElementById('correlation-graphs');
    const loading = document.getElementById('stats-loading');
    
    if (!container) {
        console.error('Container not found');
        return;
    }
    
    try {
        if (loading) loading.style.display = 'block';
        container.innerHTML = '';
        
        const response = await fetch(`${API_BASE}/api/graphs/list`);
        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }
        
        const data = await response.json();
        const graphs = data.graphs?.корреляции || [];
        
        if (loading) loading.style.display = 'none';
        
        graphs.forEach((graph) => {
            if (!graph || !graph.name || !graph.title) return;
            
            const card = document.createElement('div');
            card.className = 'graph-card';
            const imgPath = `${API_BASE}/api/graphs/${encodeURIComponent(graph.name)}`;
            card.innerHTML = `
                <div class="graph-image-container">
                    <img src="${imgPath}" alt="${graph.title}" class="graph-image">
                </div>
                <div class="graph-title">${graph.title}</div>
            `;
            container.appendChild(card);
        });
        
        console.log(`✅ Загружено ${graphs.length} графиков корреляции`);
        
    } catch (error) {
        console.error('Error:', error);
        if (loading) loading.style.display = 'none';
        container.innerHTML = `<div class="error">Ошибка загрузки: ${error.message}</div>`;
    }
}

window.loadGraphs = loadGraphs;

document.addEventListener('DOMContentLoaded', () => {
    const section = document.getElementById('analysis');
    if (section && section.classList.contains('active')) {
        loadGraphs();
    }
});
