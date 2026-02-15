#!/bin/bash
# build_files.sh - Script de build para Vercel
# Se ejecuta durante el proceso de construcción de Vercel

echo "=== Instalando dependencias ==="
pip install -r requirements.txt

echo "=== Recopilando archivos estáticos ==="
python manage.py collectstatic --noinput

echo "=== Build completado ==="
