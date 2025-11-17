# Sira Assessments

Marketing site + hiring console + candidate experience for running role-based diagnostics.

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit secrets + email creds
python manage.py migrate
python manage.py seed_assessments
python manage.py runserver
```

### Deploying

The Heroku release phase now automatically runs `python manage.py migrate --no-input` so new tables are applied before the web dyno boots. If you deploy to another platform, be sure to run migrations (at least `python manage.py migrate behavioral_assessments`) before running the new import commands.

## Running Tests

By default tests run against SQLite so they can execute anywhere (CI, Heroku review apps) without needing database privileges. No extra setup is required locally:

```bash
python manage.py test
```

If you need to point tests at a specific database, set `TEST_DATABASE_URL`. To force SQLite explicitly (useful on platforms where the default Postgres user cannot create databases), set:

```bash
export TEST_USE_SQLITE=1  # default
```

or

```bash
export TEST_DATABASE_URL=postgres://user:pass@host:5432/disposable_test_db
```

When `TEST_DATABASE_URL` is provided it takes precedence; otherwise SQLite (`test.sqlite3`) is used automatically.

## Email Configuration

The app reads standard Django `EMAIL_*` settings from the environment. For local/dev:

```bash
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=localhost
export EMAIL_PORT=1025
export EMAIL_USE_TLS=0
export EMAIL_HOST_USER=""
export EMAIL_HOST_PASSWORD=""
export DEFAULT_FROM_EMAIL="Sira Hiring <talent@sira.com>"
```

For Heroku, set config vars once (replace values with your provider/API key):

```bash
heroku config:set \
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend \
  EMAIL_HOST=smtp.sendgrid.net \
  EMAIL_PORT=587 \
  EMAIL_HOST_USER=apikey \
  EMAIL_HOST_PASSWORD=YOUR_SENDGRID_KEY \
  EMAIL_USE_TLS=1 \
  EMAIL_USE_SSL=0 \
  DEFAULT_FROM_EMAIL="Sira Hiring <talent@sira.com>"
```

After configuring, every invite (marketing CTA, console, API) automatically emails the candidate with their unique assessment link.
