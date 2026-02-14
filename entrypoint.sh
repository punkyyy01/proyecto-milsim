#!/bin/bash
set -e

echo "=== Esperando base de datos... ==="
python manage.py check --database default

echo "=== Aplicando migraciones... ==="
python manage.py migrate --noinput

echo "=== Recopilando archivos estáticos... ==="
python manage.py collectstatic --noinput

echo "=== Configurando permisos ERP... ==="
python manage.py setup_erp_permissions 2>/dev/null || true

echo "=== Iniciando servidor... ==="
exec "$@"
