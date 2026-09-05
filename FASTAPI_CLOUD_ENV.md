# FastAPI Cloud environment

Set these variables in the deployment environment for real SMS:

- `JWT_SECRET` — long random secret
- `OTP_PEPPER` — long random secret, different from JWT_SECRET
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_VERIFY_SERVICE_SID`
- `DATABASE_URL` — PostgreSQL URL for production

Without Twilio credentials, phone verification runs in development mode and the generated code is printed to server logs. It is not returned to the browser.


## Email OTP (11.2)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=YOUR_BREVO_SMTP_LOGIN
SMTP_PASSWORD=YOUR_NEW_BREVO_SMTP_KEY
SMTP_USE_TLS=true
MAIL_FROM=YOUR_VERIFIED_SENDER
MAIL_FROM_NAME=Fenix Messenger
EMAIL_DEV_MODE=false

Проверка после деплоя: GET /api/auth/email/status.
