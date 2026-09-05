# Security checklist

- Never deploy with the example JWT secret.
- Restrict CORS in production.
- Put the app behind HTTPS.
- Add rate limits to auth and message endpoints.
- Validate upload MIME types and maximum file sizes.
- Store uploads outside the web process in production.
- Add refresh-token rotation and session revocation.
- Use Redis for distributed realtime events.
- Add database backups and monitoring.
