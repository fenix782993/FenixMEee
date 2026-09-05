# FastAPI Cloud deployment

This package is intentionally shipped with `frontend/dist` already populated. You do not need npm just to deploy this archive.

1. Upload the whole project.
2. Keep `pyproject.toml` in the project root.
3. The FastAPI entrypoint is `backend.main:app`.
4. Set `DATABASE_URL` to PostgreSQL for persistent production data.
5. Set a long random `JWT_SECRET`.
6. Deploy.

After deployment, check `/api/health`. It should report `frontend: ready`.
