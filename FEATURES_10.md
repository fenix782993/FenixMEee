# Fenix Messenger 10.0 — feature map

## Account
- Email OTP registration/login
- Avatar, display name, username (5+), email and public ID
- Owner role and 3/4-digit public codes
- Profile/settings shell

## Messenger layout
- Desktop sidebar + chat workspace
- Search bar and chat folders
- Private chats, groups, channels, saved messages
- Chat header, pinned strip, message bubbles and composer
- Context menu for reply/favorite/pin/reaction/edit/delete
- Attachment sheet, emoji picker, profile/settings/device/calls dialogs
- Dark/light theme
- Responsive mobile layout

## Realtime/backend
- FastAPI API
- JWT auth
- SQLAlchemy 2
- SQLite/PostgreSQL
- WebSocket authentication and membership checks
- Message history, reactions, pinning, editing, deletion
- People search by username/name or 3/4-digit public code
- Favorites, drafts, read state, blocking
- Group admins, channels and call signaling endpoints
- File upload route and static uploads

## Email delivery
- Brevo API support
- SMTP support
- Development fallback writes OTP only to server logs
- OTP expires after 5 minutes and has attempt/rate limits

This is a Fenix-branded implementation. It does not ship Telegram source code or Telegram proprietary assets.
