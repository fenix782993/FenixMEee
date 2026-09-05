# FastAPI Cloud environment

Set these variables in the deployment environment for real SMS:

- `JWT_SECRET` — long random secret
- `OTP_PEPPER` — long random secret, different from JWT_SECRET
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_VERIFY_SERVICE_SID`
- `DATABASE_URL` — PostgreSQL URL for production

Without Twilio credentials, phone verification runs in development mode and the generated code is printed to server logs. It is not returned to the browser.
