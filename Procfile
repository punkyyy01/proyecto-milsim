release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn gestion_milsim.wsgi:application --log-file -
