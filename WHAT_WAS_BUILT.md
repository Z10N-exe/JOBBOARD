# What Was Built

## Overview

This project is a Django-based job board application with role-based access and smart matching features. It supports three types of users: job seekers, employers, and administrators.

The application includes a custom user model, resume upload and parsing, job posting management, application tracking, and TF-IDF-based relevance scoring to suggest jobs to seekers.

## Core Features

- Custom `CustomUser` model with email login and role field
- Role-based dashboards for:
  - Job seekers
  - Employers
  - Administrators
- Job seeker workflows:
  - Register as a job seeker
  - Create a profile
  - Upload a resume
  - Browse active jobs
  - Apply to jobs
  - View application status
- Employer workflows:
  - Register as an employer
  - Create and manage job listings
  - View job applicant counts and top job postings
  - Edit and delete posted jobs
- Administrator support through Django admin
- Resume upload and text extraction for document files
- TF-IDF matching logic to compute relevance between job descriptions and resume text

## Architecture

- `jobboard_project/` — Django project settings, URL routing, and WSGI/ASGI entry points
- `jobboard_project/core/` — Core application logic
  - `models.py` — custom user model, seeker/employer profiles, jobs, applications, match score cache
  - `views.py` — user registration, dashboards, job management, application submission, resume upload
  - `forms.py` — form handling for custom user creation, profile entry, resume upload, job posting, application status
  - `utils.py` — resume text extraction and TF-IDF relevance computation
- `templates/` — HTML page templates for the app
- `static/` — static assets including CSS and favicon
- `db.sqlite3` — default development database

## Matching and Resume Logic

The app includes reusable NLP utilities for scoring how well a job posting fits a seeker’s resume.

- Preprocesses text with normalization, punctuation removal, stop-word filtering, and stemming
- Uses `TfidfVectorizer` from scikit-learn
- Computes cosine similarity between job descriptions and resume content
- Shows top job recommendations on the seeker dashboard when a resume is uploaded

## Production and Deployment Readiness

- Environment-aware settings support production configuration
- Configurable database backend with MySQL support via environment variables
- Static file collection is supported with Django `collectstatic`
- Secure production settings available through environment variables including:
  - `DJANGO_SECRET_KEY`
  - `DJANGO_DEBUG`
  - `DJANGO_ALLOWED_HOSTS`
  - `DJANGO_SECURE_SSL_REDIRECT`
  - `DJANGO_SECURE_HSTS_SECONDS`
  - `DJANGO_EMAIL_BACKEND`
  - `DJANGO_DEFAULT_FROM_EMAIL`

## Testing

- Automated Django tests are included in `jobboard_project/core/tests.py`
- Current test coverage verifies:
  - Custom superuser creation and role assignment
  - Role-based dashboard access
  - Registration flows and redirects
  - Employer job creation and application tracking
- The test suite runs successfully with `python manage.py test`

## How to Run

1. Navigate to the project root:

   ```powershell
   cd C:\Users\ZION\Documents\PROJECT-EVE\jobboard
   ```

2. Install dependencies:

   ```powershell
   python -m pip install django mysqlclient scikit-learn nltk PyPDF2
   ```

3. Apply migrations:

   ```powershell
   python manage.py migrate
   ```

4. Create a superuser:

   ```powershell
   python manage.py createsuperuser
   ```

5. Start the development server:

   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```

6. Access the application:

   - Main site: `http://localhost:8000/`
   - Admin site: `http://localhost:8000/admin/`

## Summary

This job board project is a complete Django application with:
- role-based authentication and dashboards
- resume-driven job matching
- employer job management
- administrator management support
- production-ready settings and test coverage
