# V15.1 — Contacts & persistent accounts

Исправлена критическая ошибка запуска:
`ImportError: cannot import name 'Contact' from 'backend.models'`.

Добавлены реальные SQLAlchemy-модели:
- `Contact`
- `FriendRequest`
- `Block`

`backend.models` теперь экспортирует эти модели, а `backend.main` импортирует их до `Base.metadata.create_all()`.

## Account persistence

Пользователь хранится в PostgreSQL. Контакты и friend requests также хранятся в PostgreSQL и не являются demo-массивами frontend.

## Contacts flow

Найти пользователя → отправить запрос → принять → двусторонние контакты → private chat.

Для production FastAPI Cloud необходимо подключить постоянный PostgreSQL через `DATABASE_URL`.
