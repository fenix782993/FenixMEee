# Fenix v15 — аккаунты, друзья и контакты

## Аккаунты

Аккаунты хранятся в таблице `users` PostgreSQL/SQLAlchemy. Email является уникальным идентификатором регистрации; username и public_code также уникальны. JWT хранится только на клиенте как сессия, данные аккаунта не зависят от localStorage.

**Важно для FastAPI Cloud:** у приложения должна быть постоянная PostgreSQL база. Не использовать ephemeral SQLite для production, иначе аккаунты исчезнут вместе с файловой системой/перезапуском.

## Контакты

`contacts` — персональная адресная книга пользователя. Один пользователь может добавить другого в контакты с собственным локальным именем.

## Друзья

`friend_requests` хранит запросы: `pending`, `accepted`, `rejected`.

После принятия запроса:
1. оба пользователя автоматически получают друг друга в контакты;
2. создаётся личный чат;
3. чат и контакты остаются в PostgreSQL.

## Поиск

Поиск пользователей работает через `/api/social/people` по имени, username и public ID.

## API

- `GET /api/contacts`
- `POST /api/contacts`
- `PATCH /api/contacts/{user_id}`
- `DELETE /api/contacts/{user_id}`
- `GET /api/contacts/requests`
- `POST /api/contacts/request`
- `POST /api/contacts/request/respond`
