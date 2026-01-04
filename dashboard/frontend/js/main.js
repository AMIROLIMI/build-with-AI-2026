// Navigation
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const section = btn.dataset.section;
        
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update sections
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(section).classList.add('active');
    });
});


// Load districts (optional - districts are already in HTML, but we can update them from API)
async function loadDistricts() {
    try {
        const data = await API.getDistricts();
        const select = document.getElementById('sale-district');
        // Clear existing options except the first one
        const firstOption = select.querySelector('option[value=""]');
        select.innerHTML = '';
        if (firstOption) {
            select.appendChild(firstOption);
        }
        // Add districts from API
        data.districts.forEach(district => {
            const option = document.createElement('option');
            option.value = district;
            option.textContent = district;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading districts:', error);
        // Districts are already in HTML, so it's okay if API fails
    }
}

// Load floor options
function loadFloors() {
    const select = document.getElementById('sale-floor');
    for (let i = 1; i <= 22; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        if (i === 4) {
            option.selected = true;
        }
        select.appendChild(option);
    }
}

// Sale form
const saleForm = document.getElementById('sale-form');
saleForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!saleForm.checkValidity()) {
        saleForm.reportValidity();
        return;
    }
    
    const formData = new FormData(saleForm);
    const priceValue = formData.get('price');
    const data = {
        rooms: parseInt(formData.get('rooms')),
        area_m2: parseFloat(formData.get('area_m2')),
        floor: parseInt(formData.get('floor')),
        district: formData.get('district'),
        build_type: formData.get('build_type'),
        renovation: formData.get('renovation'),
        bathroom: formData.get('bathroom'),
        heating: formData.get('heating'),
        condition: formData.get('condition'),
        techpassport: formData.get('techpassport'),
        price: priceValue && priceValue.trim() !== '' ? parseFloat(priceValue) : null
    };
    
    const resultDiv = document.getElementById('sale-result');
    resultDiv.classList.remove('hidden', 'success', 'warning', 'info', 'error');
    resultDiv.innerHTML = '<div class="loading">Загрузка...</div>';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    try {
        const result = await API.predictSale(data);
        
        // Debug: log the result
        console.log('=== API RESPONSE ===');
        console.log('Full result:', JSON.stringify(result, null, 2));
        console.log('Explanation exists:', !!result.explanation);
        console.log('Explanation type:', typeof result.explanation);
        console.log('Explanation value:', result.explanation);
        console.log('Explanation length:', result.explanation ? result.explanation.length : 0);
        console.log('Explanation trimmed:', result.explanation ? result.explanation.trim() : 'N/A');
        console.log('Recommendation exists:', !!result.recommendation);
        console.log('Recommendation value:', result.recommendation);
        console.log('Recommendation length:', result.recommendation ? result.recommendation.length : 0);
        
        // Check if explanation is actually empty
        if (!result.explanation || (typeof result.explanation === 'string' && !result.explanation.trim())) {
            console.error('❌ Explanation is missing or empty!');
            console.error('Result keys:', Object.keys(result));
        } else {
            console.log('✅ Explanation received:', result.explanation.substring(0, 100));
        }
        
        resultDiv.className = `result ${result.status}`;
        resultDiv.innerHTML = `
            <h3>Результат прогноза</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div>
                    <div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 5px;">Прогнозируемая цена</div>
                    <div class="price" style="font-size: 1.3rem;">${formatPrice(result.predicted_price)} сомони</div>
                </div>
                ${result.user_price ? `
                <div>
                    <div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 5px;">Ваша цена</div>
                    <div class="price" style="font-size: 1.3rem;">${formatPrice(result.user_price)} сомони</div>
                </div>
                ` : ''}
            </div>
            <div class="message">${result.message}</div>
            ${result.difference_percent !== undefined ? `
                <div style="margin-top: 15px; padding: 10px; background: #F3F4F6; border-radius: 8px; text-align: center;">
                    <strong style="color: ${result.status === 'success' ? '#10B981' : result.status === 'warning' ? '#F59E0B' : '#6B7280'};">
                        Разница: ${result.difference_percent > 0 ? '+' : ''}${result.difference_percent.toFixed(2)}%
                    </strong>
                </div>
            ` : ''}
            
            ${result.explanation && result.explanation.trim() ? `
                <div style="margin-top: 25px; padding: 20px; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-left: 5px solid #3B82F6; border-radius: 10px; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);">
                    <h4 style="margin-bottom: 12px; color: #1E40AF; font-size: 1.2rem; font-weight: 700;">🤖 Объяснение от AI</h4>
                    <p style="color: #1F2937; line-height: 1.8; font-size: 1.05rem;">${result.explanation}</p>
                </div>
            ` : result.explanation ? `
                <div style="margin-top: 20px; padding: 15px; background: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 8px;">
                    <p style="color: #92400E;">⚠️ Объяснение пустое. Проверьте логи сервера.</p>
                </div>
            ` : `
                <div style="margin-top: 20px; padding: 15px; background: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 8px;">
                    <p style="color: #92400E;">⚠️ Объяснение не получено. Проверьте консоль браузера (F12) для отладки.</p>
                </div>
            `}
            
            ${result.recommendation && result.recommendation.trim() ? `
                <div style="margin-top: 15px; padding: 20px; background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border-left: 5px solid #22C55E; border-radius: 10px; box-shadow: 0 4px 6px rgba(34, 197, 94, 0.1);">
                    <h4 style="margin-bottom: 12px; color: #15803D; font-size: 1.2rem; font-weight: 700;">💡 Рекомендация от AI</h4>
                    <p style="color: #1F2937; line-height: 1.8; font-size: 1.05rem;">${result.recommendation}</p>
                </div>
            ` : ''}
        `;
    } catch (error) {
        resultDiv.className = 'result error';
        let errorMsg = 'Неизвестная ошибка';
        
        if (error instanceof Error) {
            errorMsg = error.message;
        } else if (typeof error === 'string') {
            errorMsg = error;
        } else if (error && error.message) {
            errorMsg = error.message;
        } else if (error && error.detail) {
            errorMsg = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
        } else {
            errorMsg = JSON.stringify(error);
        }
        
        if (errorMsg === 'Failed to fetch' || errorMsg.includes('Failed to fetch')) {
            errorMsg = 'Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен на http://localhost:8000';
        }
        
        resultDiv.innerHTML = `<div class="error">Ошибка: ${errorMsg}</div>`;
        console.error('Prediction error:', error);
    }
});


function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU').format(Math.round(price));
}

// Initialize
loadDistricts();
loadFloors();

