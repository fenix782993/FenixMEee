# Email setup for Fenix Messenger 11.0

FastAPI Cloud Environment Variables:

SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=YOUR_BREVO_SMTP_LOGIN
SMTP_PASSWORD=YOUR_BREVO_SMTP_KEY
SMTP_USE_TLS=true
MAIL_FROM=YOUR_VERIFIED_SENDER
MAIL_FROM_NAME=Fenix Messenger

Also configure:
JWT_SECRET=long-random-secret
OTP_PEPPER=another-long-random-secret

For Brevo SMTP, the SMTP key is the password and the SMTP login is the username. Port 587 uses TLS.
Do not commit secrets to GitHub and do not put them into frontend JavaScript.
