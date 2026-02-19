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

Gestión de Usuarios (nuevo)
- Ruta administrativa: `/admin/usuarios/` (acceso UI para crear/editar/eliminar usuarios).
- Acciones disponibles: crear usuario, editar (incluye cambiar contraseña), eliminar, alternar `is_superuser` y alternar `is_active`.
- Acceso restringido: solo miembros del grupo `CREADOR_ERP` (o `creador` legacy) o superusuarios pueden acceder.
- Seguridad: todas las acciones mutantes requieren `POST` con `{% csrf_token %}` y están registradas en la auditoría (`LogEntry`).
- Validaciones aplicadas: formato estricto de username, validación de contraseñas mediante los validators de Django, y whitelist de grupos ERP para evitar inyección de grupos arbitrarios.
- Protección: no puedes eliminarte a ti mismo ni quitarte el estatus de superusuario o desactivarte desde esta interfaz.

Crear/actualizar grupos ERP (ya disponible)
- Ejecuta `python manage.py setup_erp_permissions` para crear/actualizar los grupos ERP y asignar permisos.
- Para asignar un usuario específico al grupo `CREADOR_ERP` al crear los grupos usa `--emi-username`.
- Ejemplo de asignación masiva: `python manage.py setup_erp_permissions --assign OFICIAL_ERP:juan,maria`.

Legacy
- La ruta legacy `/admin/user-tools/` ahora redirige a `/admin/usuarios/` y requiere autenticación de `staff`.

ORBAT público
- La vista ORBAT visual está disponible públicamente en `/orbat/` sin requerir login. El panel admin (`/admin/`) mantiene la protección por credenciales.

Seguridad aplicada (resumen técnico)
- Toggles y acciones mutantes via POST + `@require_POST`.
- Validación de username con regex: `^[a-zA-Z0-9_.\-@+]{1,150}$`.
- Validación de contraseña usando `django.contrib.auth.password_validation.validate_password`.
- Auditoría: todas las operaciones de gestión de usuarios registran entradas en `django.contrib.admin.models.LogEntry`.
- Logging adicional para accesos denegados y acciones mutantes con `logger`.
- Truncado de parámetros de búsqueda para evitar abusos (p. ej. `q` limitado a 200 caracteres).

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
