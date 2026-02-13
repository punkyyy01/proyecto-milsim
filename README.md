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

Seguridad de cuentas (implementado)
- Los usuarios normales (staff no superusuario) no pueden cambiar credenciales desde el admin.
- El enlace de edición de perfil en la barra superior del admin fue removido para evitar cambios de cuenta desde UI.
- `Usuarios` y `Grupos` se muestran en el panel, pero están en modo solo lectura (sin crear, editar ni borrar).

Permisos ERP (implementado)
- Comando base: `python manage.py setup_erp_permissions`
- Crea/actualiza grupos: `CREADOR_ERP`, `ALTO_MANDO_ERP`, `OFICIAL_ERP`, `SARGENTO_ERP`, `CONSULTA_ERP`.
- Asigna por defecto `CREADOR_ERP` a `Emi` (o al usuario indicado con `--emi-username`).
- Asignación masiva opcional por grupo:
	- `python manage.py setup_erp_permissions --assign OFICIAL_ERP:juan,maria --assign CONSULTA_ERP:ana`

Auditoría (implementado)
- Ruta: `/admin/auditoria/`
- Incluye filtros por texto, usuario, modelo, acción, rango de fechas y accesos rápidos (`Hoy`, `Últimos 7 días`).
- Exportación CSV respetando filtros activos.

Variables recomendadas para Heroku
- `DJANGO_SECRET_KEY`: clave secreta larga y única.
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=tu-app.herokuapp.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-app.herokuapp.com`
- `DATABASE_URL` (Heroku Postgres)
- `DJANGO_LOG_LEVEL=INFO` (o `WARNING` en producción estable)

Backups y operación (Heroku Postgres)
- Programar backups automáticos de Postgres.
- Probar restauración periódica en entorno de staging.
- Rotar claves/secrets cuando haya cambios de personal o incidentes.

Compatibilidad local/ngrok
- Tu flujo actual de pruebas (`runserver` + ngrok) sigue soportado.
- En `DEBUG=True`, se permiten hosts `*.ngrok-free.app` y `*.ngrok.io`.
- Los cambios de CI no afectan la ejecución local.
