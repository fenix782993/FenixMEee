# Архитектура

Frontend разделён на features, reusable components, hooks и lib. Backend разделён на API routers, services, SQLAlchemy models, Pydantic schemas и core configuration/security/database.

Realtime: клиент подключается к `/ws/{chat_id}`. События сообщения, редактирования, удаления, реакции, pin и typing рассылаются через ConnectionManager.

Для production рекомендуется вынести WebSocket fanout в Redis, файлы в S3-compatible storage, добавить Alembic migrations, rate limiting, refresh tokens и отдельный worker.
