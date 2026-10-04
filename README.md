# URL Shortener

FastAPI + PostgreSQL backend, React (Vite) frontend.

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # then edit DATABASE_URL
alembic upgrade head          # apply database migrations
uvicorn app.main:app --reload
```

## Frontend

```powershell
cd frontend
npm ci
npm run dev
```

## Database migrations

Run these from `backend/`. Migrations live in `migrations/versions/release_<x_y_z>/`.

1. `alembic revision -m "describe the change"`
2. Move the new file into the release folder.
3. Write `upgrade()` and `downgrade()`.
4. `alembic upgrade head`, then `alembic current` to confirm.

Never edit a migration that has already been applied. Add a new one.
