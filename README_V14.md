# Fenix Messenger v14 — Desktop / Mobile

Самостоятельный Telegram-inspired messenger. Telegram Desktop исходники в проект не включены.

## Stack
FastAPI + SQLAlchemy + PostgreSQL + WebSocket + React/Vite.

## Deployment
FastAPI Cloud должен запускать backend и раздавать `frontend/dist`.

## Email
Используются `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `MAIL_FROM`, `MAIL_FROM_NAME`.
Для Brevo `SMTP_PASSWORD` должен быть SMTP key, а не пароль аккаунта.

## Important
`frontend/src/App.jsx` теперь содержит реальный React shell. Production `frontend/dist` из предыдущей версии сохранён для совместимости, а source tree можно собирать через Vite.
