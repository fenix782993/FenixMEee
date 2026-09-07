# Fenix Cloud Deployment Checklist

1. Upload the complete project archive.
2. Confirm `pyproject.toml` contains exactly one `[tool.fastapi]` block.
3. Confirm `entrypoint = "backend.main:app"`.
4. Confirm PostgreSQL `DATABASE_URL` is present.
5. Confirm `JWT_SECRET` is present.
6. Confirm SMTP host, port, login, password/key and sender variables are present.
7. Deploy.
8. Check `/api/health`.
9. Open the web application and complete email registration.
10. Create two accounts.
11. Search the second account.
12. Send and accept a friend request.
13. Verify both accounts show the contact.
14. Open the private chat from both accounts.
15. Send messages in both directions.
16. Restart/redeploy and confirm accounts and messages remain in PostgreSQL.
