# Fenix Messenger — Full MVP

Полноценная Telegram-inspired основа мессенджера: авторизация, профили, личные и групповые чаты, realtime WebSocket, редактирование/удаление, реакции, ответы, поиск, вложения, закрепление, уведомления и адаптивный интерфейс.

## Запуск

### Backend
`python -m venv .venv` → `pip install -r backend/requirements.txt` → `uvicorn backend.main:app --reload`

### Frontend
`cd frontend` → `npm install` → `npm run dev`

Для production Docker собирает React и отдаёт его через FastAPI. По умолчанию SQLite; для PostgreSQL задайте `DATABASE_URL`.

## Переменные
`DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `UPLOAD_DIR`.

## Что уже реализовано
- регистрация / вход / JWT
- профиль, bio, online/last seen
- пользователи и поиск
- личные чаты и группы
- история сообщений
- WebSocket realtime
- typing / read events
- reply / edit / delete
- реакции
- pin / unpin
- файлы и изображения
- поиск сообщений
- непрочитанные сообщения
- адаптивный desktop/mobile UI
- Render + Docker

Это самостоятельная реализация с Telegram-подобной логикой интерфейса, без копирования исходного кода Telegram или его закрытых ресурсов.
