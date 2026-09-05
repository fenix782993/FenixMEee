# Fenix Messenger — FULL

Полноценный full-stack мессенджер на FastAPI + SQLAlchemy + WebSocket с готовым статическим frontend/dist.

## Что уже внутри

- регистрация и вход по JWT;
- профиль пользователя и статус online;
- поиск пользователей;
- личные чаты;
- групповые чаты;
- история сообщений;
- отправка, редактирование и удаление сообщений;
- emoji reactions;
- закрепление сообщений;
- загрузка файлов до 25 MB;
- WebSocket для realtime typing/presence/messages;
- адаптивный Telegram-подобный интерфейс;
- светлая и тёмная тема;
- поиск сообщений;
- FastAPI Cloud конфигурация через pyproject.toml;
- готовый `frontend/dist`, поэтому для деплоя не требуется Node.js на сервере.

## FastAPI Cloud

В корне проекта уже есть `pyproject.toml`, `requirements.txt` и `main.py`. Точка входа: `backend.main:app`.

Переменные окружения:

- `DATABASE_URL` — PostgreSQL URL или SQLite;
- `JWT_SECRET` — длинный секрет для JWT;
- `CORS_ORIGINS` — список origin через запятую или `*`.

## Локально

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Открой `http://127.0.0.1:8000`.

## Разработка frontend

Исходник React/Vite находится в `frontend/src`. Если установлен Node.js:

```bash
cd frontend
npm install
npm run build
```

Собранный результат заменит `frontend/dist`.
