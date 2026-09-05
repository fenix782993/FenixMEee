# Fenix Messenger — Full Starter

Telegram-inspired full-stack messenger foundation: authentication, profiles, private chats, groups, realtime WebSocket messaging, edit/delete, replies, reactions, search, pinning, typing indicator, read state, media upload, notifications, PWA-ready frontend, PostgreSQL/SQLite support, Docker and Render deployment.

## Run locally
1. `cd frontend && npm install && npm run build`
2. `cd .. && python -m venv .venv`
3. Activate venv and `pip install -r backend/requirements.txt`
4. `uvicorn backend.main:app --reload --port 8000`
5. Open `http://localhost:8000`

For development frontend: `cd frontend && npm run dev`.

Set `DATABASE_URL` for PostgreSQL and a strong `JWT_SECRET` in production.
