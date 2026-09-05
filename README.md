# Fenix Messenger 10.0 — FULL

Полноценная основа Fenix Messenger с Telegram-подобной компоновкой и email-first авторизацией.

## Авторизация

1. Пользователь вводит email.
2. Сервер создаёт 6-значный OTP.
3. Код отправляется через Brevo API или SMTP.
4. После подтверждения пользователь задаёт аватар, имя и username (минимум 5 символов).
5. После завершения профиля выдаётся JWT и открывается мессенджер.

Если почтовый провайдер не настроен, код не возвращается браузеру: он пишется только в server log для разработки.

## Основные возможности

- аккаунты, профили, аватары, email, username, ID;
- поиск людей по username/имени и 3/4-значному public ID;
- личные чаты и Избранное;
- группы и каналы;
- сообщения, reply, edit, delete, pin, reactions;
- emoji, sticker/GIF разделы;
- вложения и файловая область;
- WebSocket realtime, typing/presence;
- настройки, тема, уведомления, приватность, устройства;
- WebRTC signaling API для звонков;
- FastAPI + SQLAlchemy + SQLite/PostgreSQL;
- готовый `frontend/dist` для деплоя без npm build.

## FastAPI Cloud

Entrypoint: `backend.main:app`.

Для реального email OTP добавьте переменные из `.env.example`.
