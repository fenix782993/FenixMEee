# Fenix Messenger 11.0 — Full Phone + Desktop build

## Email registration / login
- Email-first registration and login
- 6-digit OTP by Brevo SMTP or Brevo API
- 5 minute code expiry
- 45 second resend cooldown
- Up to 5 code attempts
- One-time signup token after verification
- Three-step onboarding: Email → Code → Profile
- Avatar upload during onboarding
- Live username availability indicator
- Username validation and duplicate protection
- Auto-submit when 6-digit code is entered

## Profile
- Avatar upload after login
- Display name
- Username
- Bio
- Public 3/4 digit ID
- Email shown in profile

## Messenger
- Telegram-style desktop two-column layout
- Mobile bottom navigation
- Private chats, groups, channels, saved messages
- Message history
- WebSocket live messages
- Reply / edit / delete / pin / reaction / favorite
- Draft autosave
- Read state
- File upload
- Emoji picker
- Attachment sheet

## Calls
- Audio/video call session creation
- Call signaling endpoints
- Calls UI

## Settings
- Light/dark theme
- Profile editing
- Contacts search by name, username and 3/4-digit ID
- Devices screen
- Privacy/settings placeholders

## Deployment
- Prebuilt `frontend/dist` included
- FastAPI serves API + static frontend
- SQLite default, PostgreSQL through DATABASE_URL
- FastAPI Cloud ready
