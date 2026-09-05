# FastAPI Cloud

Use the root `pyproject.toml` entrypoint `backend.main:app`.

For email OTP, configure either Brevo:
- `BREVO_API_KEY`
- `MAIL_FROM`
- `MAIL_FROM_NAME`

or SMTP:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `MAIL_FROM`
- `SMTP_USE_TLS`

`frontend/dist` is included in this archive, so the deployed FastAPI app can serve the web client without running npm during deployment.

Email flow: email → 6 digit code → profile avatar/name/username → account.
