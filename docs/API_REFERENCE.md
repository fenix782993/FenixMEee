# Fenix Messenger API Reference

## Health
- `GET /api/health`

## Authentication
- `GET /api/auth/email/status`
- `POST /api/auth/email/request`
- `POST /api/auth/email/verify`
- `POST /api/auth/email/complete`
- `POST /api/auth/login`
- legacy phone verification endpoints remain available when configured.

## Users
- user profile and account endpoints are protected by JWT.
- username search supports public discovery rules configured by the backend.

## Contacts
- `GET /api/contacts`
- `GET /api/contacts/search?q=...`
- `GET /api/contacts/requests/incoming`
- `GET /api/contacts/requests/outgoing`
- `POST /api/contacts/request`
- `POST /api/contacts/request/{request_id}/accept`
- `POST /api/contacts/request/{request_id}/decline`
- `DELETE /api/contacts/{contact_id}`

## Chats and messages
- private chat creation/reuse is persistent in PostgreSQL.
- messages are persisted and can be delivered through WebSocket events.
- chat membership is stored independently from message records.

## Security
Never expose SMTP passwords, SMTP keys, JWT secrets, database passwords, or OTP pepper values in the frontend bundle.
