# Proyecto Milsim - Gestión ORBAT

Resumen rápido
- Proyecto Django para gestionar la jerarquía ORBAT (Regimiento → Compañía → Pelotón → Escuadra → Miembros).

Requisitos
- Python 3.11+ (recomendado)
- Virtualenv

Instalación local
```bash
# activar tu virtualenv
& venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # editar valores si es necesario
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ejecutar tests
```bash
python manage.py test
```

Docker (básico)
```bash
docker build -t milsim .
docker run -e DJANGO_SECRET_KEY=change -p 8000:8000 milsim
```

Notas
- `gestion_milsim/settings.py` usa `python-dotenv` para cargar `.env`.
- Añade secretos reales en producción y pon `DJANGO_DEBUG=False`.
- Considera usar WhiteNoise o un servidor de archivos estáticos en producción.
