release: python manage.py migrate --no-input && python manage.py setup_site
web: gunicorn config.wsgi --log-file -
