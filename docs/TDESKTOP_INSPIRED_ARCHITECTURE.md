# Fenix Messenger — архитектура v14

Fenix **не копирует исходники Telegram Desktop**. Репозиторий tdesktop используется только как архитектурный ориентир: в нём отдельно организованы UI, core/data, storage, WebRTC/media и build modules. Официальный проект сам является большим C++/CMake приложением. [Официальный репозиторий](https://github.com/telegramdesktop/tdesktop).

## Аналогия слоёв

| tdesktop-подход | Fenix |
|---|---|
| Core / launcher / platform | `backend/main.py`, `backend/core/` |
| Data / session / history | `backend/models/`, `backend/services/` |
| API / network | `backend/api/`, WebSocket |
| Storage | PostgreSQL / SQLAlchemy |
| UI | React source + production client |
| Media / calls | `backend/api/files.py`, будущий WebRTC layer |
| Settings | `backend/models/settings.py`, `SettingsPanel` |

## Правило проекта

Не переносим C++/Qt/MTProto код Telegram Desktop в Fenix. Fenix остаётся самостоятельным FastAPI + PostgreSQL + WebSocket + React проектом.

## Production flow

Browser → FastAPI → API/WebSocket → service layer → SQLAlchemy/PostgreSQL.

Email OTP → SMTP/Brevo → verification record → JWT session.

## Следующие этапы

1. Real chat persistence and pagination.
2. Presence/read receipts over WebSocket.
3. Upload pipeline with thumbnails.
4. Groups/channels/roles.
5. Search index.
6. Calls/WebRTC.
7. Push notifications.
