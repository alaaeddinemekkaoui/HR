# HR Backend (Django)

Server-rendered Django scaffold using classic Templates (Bootstrap), organized for scalability with an apps namespace and explicit folders for models, controllers, and views.

What's inside:

- Django project `hr_project` (server-rendered, no SPA required)
- Namespace `apps/` with `employees` app structured as:
   - `models/` data models
   - `controllers/` business logic layer (thin orchestration)
   - `views/` request handlers rendering templates
   - `templates/employees/` Bootstrap pages
- `templates/base.html` with Bootstrap 5 CDN
- SQLite by default; can switch to PostgreSQL via env vars
- `docker-compose.yml` for Postgres + Redis (future) + web
- `requirements.txt` for Python dependencies

Project layout (key parts):

```
hr_project/
   settings.py
   urls.py
   wsgi.py
apps/
   employees/
      models/employee.py
      controllers/employee_controller.py
      views/employee_views.py
      urls.py
templates/
   base.html
   employees/
      list.html
      form.html
```

Quick start (local dev, SQLite):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations employees
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ — you'll be redirected to Employees list.

Docker (optional):

```powershell
docker compose up --build
```

Migrations and seeding (Docker)

If you're running the app with Docker Compose the `web` service exposes the Django manage commands. Use the following PowerShell-friendly commands to run migrations and the seed command (which also can create a superuser):

```powershell
# Build and start dependent services (db, redis) in the background
docker compose up -d --build db redis

# Run migrations inside a one-off web container
docker compose run --rm web python manage.py migrate

# (Optional) Create a superuser and seed groups using the custom seed command
# Usage: python manage.py seed --superuser USERNAME EMAIL PASSWORD
docker compose run --rm web python manage.py seed --superuser admin admin@example.com admin1234

# Seed sample data using existing commands in order:
# 1. Basic org structure (directions, divisions, services, grades, positions)
docker compose run --rm web python manage.py seed_org_basics

# 2. Grade progression rules
docker compose run --rm web python manage.py seed_grade_rules

# 3. Sample employees with user accounts (password: rabat2025)
docker compose run --rm web python manage.py seed_sample_employees

# 4. (Optional) Seed roles/permissions
docker compose run --rm web python manage.py seed_roles

# Start the web service (or bring all services up)
docker compose up --build
```

Sample accounts after seeding:
- Check command output for created employee emails
- **Default password**: rabat2025
- Login with username OR email

Notes:
- The `seed` command creates groups (`HR Admin`, `IT Admin`) and optionally a superuser with `--superuser`.
- The employee seed commands create: organizational structure, grades, positions, and sample employees with linked user accounts.
- If you prefer to run commands against a running web container instead of `run`, use `docker compose exec web <cmd>` after starting the services with `docker compose up -d`.

Notes:

- For PostgreSQL, set env vars (see `.env.example`) or use the provided compose file.
- Redis and Celery are planned for async tasks and caching; not used yet in MVC pages.
- Next apps to add: `leaves`, `attendance`, `payroll`, each under `apps/<domain>/` with the same folder pattern.
