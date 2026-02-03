release: python manage.py migrate --no-input && python manage.py createcachetable 2>/dev/null || true && python manage.py setup_site
web: gunicorn config.wsgi --log-file - --timeout 120
