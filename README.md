# Fenix Messenger — FULL 5.0

Полноценная Telegram-подобная база мессенджера, подготовленная для FastAPI Cloud.

## Что внутри

- Регистрация и вход
- Юзернейм от 5 символов
- Поиск людей по `@username`, имени и 3/4-значному публичному ID
- Профиль: имя, bio, аватар, публичный ID
- Первый зарегистрированный пользователь получает роль владельца
- Владелец может выдавать пользователям 3- или 4-значные ID
- Личные чаты и группы
- Сообщения, редактирование, удаление, реакции, закрепление
- Избранные сообщения
- Файлы и изображения
- Emoji picker
- Стикеры
- GIF picker
- WebSocket realtime
- Тёмная/светлая тема
- Админские заготовки и owner panel
- Готовый `frontend/dist` уже находится в архиве
- PostgreSQL/SQLite через `DATABASE_URL`

## FastAPI Cloud

Entrypoint: `backend.main:app`.

Для этого архива **не требуется npm для запуска опубликованного интерфейса**, потому что готовый `frontend/dist` уже включён.

## Локально

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Откройте `/`.


## 5.0.1 hotfix
- Fixed duplicate SQLAlchemy `read_states` table registration.
- `ReadState` now has a single canonical model in `backend/models/read.py`.
- `backend/models/__init__.py` uses explicit imports to prevent duplicate model registration.
