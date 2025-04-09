# 📊 Flask Dashboard с синтетическими данными

Это аналитическое веб-приложение на Flask с интерактивными графиками Plotly и синтетическими данными. Проект демонстрирует архитектуру, близкую к реальному бизнес-проекту: с логикой клиентских аккаунтов, транзакциями, сессиями, задачами и фильтрацией.

## 🚀 Возможности

- Генерация синтетических данных с помощью `seed_data.py` (включая UUID, временные метки, суммы, статусы и версии приложений)
- Использование SQLite для хранения данных
- Оптимизированные SQL-запросы с индексами
- Три Plotly-графика:
  - Сессии по дням и версиям приложения
  - Сумма транзакций по дням
  - Задачи по дням и типу задачи
- Гибкие фильтры:
  - Версия приложения
  - Тип задачи
  - Диапазон дат
- Переключатель тёмной/светлой темы
- Плавная анимация загрузки графиков
- UI с мягкими цветами, закруглениями, тенями и хорошей читаемостью

## 🧱 Стек технологий

- Python 3.11+
- Flask
- Plotly
- SQLite
- Jinja2
- HTML + CSS

## 📁 Структура проекта

project/
├── db/
│   ├── connection.py         # Подключение к SQLite
│   └── seed_data.py          # Генерация синтетических данных
├── static/
│   └── style.css             # Основные стили, поддержка тем
├── templates/
│   └── index.html            # Главная страница с графиками
├── main.py                   # Основной Flask-приложение
├── requirements.txt          # Зависимости
└── README.md                 # Описание проекта

## 📷 Скриншоты

| Светлая тема | Тёмная тема |
|-------------|-------------|
| ![light](https://github.com/user-attachments/assets/f9f78df2-d110-444c-a07d-277bb30aa5b4) | ![dark](https://github.com/user-attachments/assets/6f49d2ff-3001-438d-bffd-ba1063a0be3c)


## 💡 Примечания

- Для увеличения объёма данных можно отредактировать параметры генерации в `seed_data.py`
- Используются UUID вместо числовых ID для большей реалистичности
- Индексы добавлены вручную для повышения производительности SQL-запросов
- Приложение полностью автономно и не требует внешнего API

## 🛠️ Планы по улучшению

- Добавить одновременную фильтрацию нескольких графиков по дате
- Сделать сброс фильтров по кнопке
- Сгенерировать побольше дат
- Подключение к PostgreSQL
- Экспорт графиков

## 🧑‍💻 Автор

Эмиль Назыров, студент направления *Программирование в инфокоммуникационных системах*  
