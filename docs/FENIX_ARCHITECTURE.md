# Fenix Messenger — Architecture Reference

This document describes the intended production architecture of the Fenix Messenger bundle.

## Runtime
- FastAPI application entrypoint: `backend.main:app`
- PostgreSQL is the persistent source of truth.
- SQLAlchemy owns database mappings.
- JWT is used for authenticated API requests.
- WebSocket support is used for live chat events.
- Vite/React source is kept under `frontend/src` and the deployable static build is under `frontend/dist`.

## Account lifecycle
1. User requests an email verification code.
2. The server creates a verification record and sends the code through configured SMTP.
3. The code is verified server-side.
4. The user completes the profile.
5. A persistent `users` record is created.
6. Login returns a JWT.

## Social graph
`contacts` stores directional contacts. `friend_requests` stores the request state. `blocks` stores user blocks. Accepted friend requests create contact entries and a persistent private chat.

## Private chats
Private chats are represented by the `chats` table and the `chat_members` association table. The service must always reuse an existing two-member private chat rather than creating duplicates.

## Deployment
FastAPI Cloud should use `backend.main:app` as the explicit entrypoint. PostgreSQL credentials and SMTP credentials belong in environment variables/secrets, never in source control.
