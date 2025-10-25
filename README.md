# HR Backend (Django) — MVC-style scaffold

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

Notes:

- For PostgreSQL, set env vars (see `.env.example`) or use the provided compose file.
- Redis and Celery are planned for async tasks and caching; not used yet in MVC pages.
- Next apps to add: `leaves`, `attendance`, `payroll`, each under `apps/<domain>/` with the same folder pattern.
