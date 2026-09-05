# Phone authentication

Fenix Messenger 9.0 uses a phone-first onboarding flow:

1. User enters a phone number in international E.164 format.
2. Server sends an SMS verification code through Twilio Verify when the three Twilio variables are configured.
3. User enters the 6-digit code.
4. Registration continues to profile setup: avatar, display name and username.
5. After profile completion the server creates the account and returns the normal Fenix JWT.
6. Existing users can log in by phone + SMS code.

For local development without Twilio, the generated OTP is written only to the server log as `FENIX OTP DEV`; it is not returned by the API.

Required production environment variables:

- `OTP_PEPPER`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_VERIFY_SERVICE_SID`

Use only phone numbers whose owner has requested the code. SMS delivery to arbitrary third-party numbers requires a real SMS provider and its credentials.
