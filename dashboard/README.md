# Дашборд недвижимости

Веб-приложение для анализа и прогнозирования стоимости квартир с использованием ML-модели.

## Структура проекта

```
dashboard/
├── backend/          # FastAPI бэкенд
│   ├── app.py       # Основное приложение
│   └── requirements.txt
├── frontend/        # HTML/CSS/JS фронтенд
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── api.js
│       └── main.js
└── README.md
```

## Установка и запуск

### 1. Установка зависимостей

```bash
cd dashboard/backend
pip install -r requirements.txt
```

### 2. Запуск бэкенда

```bash
cd dashboard/backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Бэкенд будет доступен по адресу: `http://localhost:8000`

### 3. Запуск фронтенда

Откройте файл `dashboard/frontend/index.html` в браузере или используйте простой HTTP-сервер:

```bash
cd dashboard/frontend
python -m http.server 8080
```

Затем откройте в браузере: `http://localhost:8080`

## Использование

### Раздел "Продажа"

1. Заполните все поля формы с характеристиками квартиры
2. Укажите цену, по которой хотите продать
3. Нажмите "Получить прогноз"
4. Система покажет:
   - Прогнозируемую рыночную цену
   - Рекомендацию по продаже

### Раздел "Покупка"

1. Просмотрите информацию о квартире
2. Нажмите "Оценить квартиру"
3. Система покажет:
   - Реальную стоимость квартиры по прогнозу модели
   - Сравнение с ценой продавца

## Требования

- Python 3.8+
- Модель в `artifacts/standard_catboost.pkl`
- Encoder в `Notebooks/ohe_encoder.joblib`

## API Endpoints

- `POST /api/predict/sale` - Прогноз для продажи
- `POST /api/predict/buy` - Прогноз для покупки
- `GET /api/districts` - Список районов
- `GET /api/health` - Проверка здоровья API

