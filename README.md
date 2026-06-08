# Job Board Django Application

This is a Django-based job board application for managing three user roles:
- **Job Seeker**: upload resumes, browse jobs, and apply.
- **Employer**: create and manage job postings, review applicants, and update application status.
- **Administrator**: manage users, jobs, and monitor the system through Django admin.

The app uses a custom `CustomUser` model with role-based dashboards and supports resume upload plus job matching logic.

## Features

- Role-based registration and login
- Custom user model with `seeker`, `employer`, and `admin` roles
- Job posting CRUD for employers
- Resume upload and text extraction
- Application submission and status tracking
- Django admin interface for advanced management
- MySQL-ready configuration with fallback to SQLite for development

## Project Structure

- `manage.py` — Django management utility
- `jobboard_project/` — Django project settings and routing
- `jobboard_project/core/` — core app with models, views, forms, templates, and migrations
- `templates/` — shared HTML templates
- `db.sqlite3` — default SQLite development database

## Prerequisites

- Python 3.11+ or compatible
- Django 6.x installed
- Optional for MySQL: `mysqlclient` or compatible MySQL DB driver

## Running Locally

1. Open a terminal and navigate to the project root:

   ```powershell
   cd C:\Users\ZION\Documents\PROJECT-EVE\jobboard
   ```

2. Install Python dependencies if not already installed:

   ```powershell
   python -m pip install django mysqlclient
   ```

3. Apply migrations:

   ```powershell
   python manage.py migrate
   ```

4. Create a superuser for admin access:

   ```powershell
   python manage.py createsuperuser
   ```

5. Start the development server:

   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```

6. Open the app in your browser:

   - Main site: `http://localhost:8000/`
   - Django admin: `http://localhost:8000/admin/`

## MySQL Configuration

To use MySQL instead of SQLite, set the following environment variables before running the app:

- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST` (default: `127.0.0.1`)
- `MYSQL_PORT` (default: `3306`)

Example on PowerShell:

```powershell
$env:MYSQL_DATABASE = 'jobboard'
$env:MYSQL_USER = 'root'
$env:MYSQL_PASSWORD = 'your_password'
$env:MYSQL_HOST = '127.0.0.1'
$env:MYSQL_PORT = '3306'
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Production configuration

The project reads production settings from environment variables when available:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_EMAIL_BACKEND`
- `DJANGO_DEFAULT_FROM_EMAIL`

Django writes static assets into `staticfiles/` when you run:

```powershell
python manage.py collectstatic
```

For production, set `DJANGO_DEBUG=False` and configure a real email backend.

## Testing

Run the test suite with:

```powershell
python manage.py test
```

## Notes

- The app currently uses `AUTH_USER_MODEL = 'core.CustomUser'`.
- Uploaded resume files are stored under `media/resumes/`.
- Static files are served by Django in development mode only.
- For production, use a proper WSGI/ASGI server and database configuration.

## Troubleshooting

- If you see migration issues, remove stale `db.sqlite3` and rerun `python manage.py migrate`.
- Make sure you run commands from the `jobboard` directory containing `manage.py`.

---

Enjoy building and testing the job board application!