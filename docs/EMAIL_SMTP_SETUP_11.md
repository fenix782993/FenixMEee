# Email OTP — Fenix Messenger 11.2

В FastAPI Cloud → Environment Variables добавь именно эти переменные:

```text
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=ТВОЙ_SMTP_LOGIN
SMTP_PASSWORD=ТВОЙ_НОВЫЙ_SMTP_KEY
SMTP_USE_TLS=true
MAIL_FROM=ТВОЙ_ПОДТВЕРЖДЁННЫЙ_SENDER
MAIL_FROM_NAME=Fenix Messenger
EMAIL_DEV_MODE=false

JWT_SECRET=длинная-случайная-строка
OTP_PEPPER=другая-длинная-случайная-строка
```

`SMTP_USER` — SMTP login Brevo. `SMTP_PASSWORD` — SMTP key Brevo.
`MAIL_FROM` — отдельный подтверждённый Sender в Brevo; SMTP login сюда ставить нельзя.

После деплоя открой:

`/api/auth/email/status`

Он не показывает пароль и должен вернуть `configured: true`, `provider: brevo_smtp`, `smtp_user_set: true`, `smtp_password_set: true`, `mail_from_set: true`.

Если код не отправляется, `/api/auth/email/request` теперь возвращает точную ошибку вместо ложного сообщения «Код отправлен».

Не коммить SMTP key в GitHub и не вставлять его во frontend.
