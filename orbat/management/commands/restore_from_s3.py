"""
Management command: restore_from_s3
================================
Lista backups en S3, permite elegir uno y restaurarlo en la BD
(SQLite o PostgreSQL). Solicita confirmación antes de sobrescribir datos
actuales. Lee credenciales desde variables de entorno.

Uso:
  python manage.py restore_from_s3            # lista y permite elegir
  python manage.py restore_from_s3 --key KEY  # selecciona por argumento
  python manage.py restore_from_s3 --yes --key KEY  # sin prompt de confirm
"""

import gzip
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger("orbat.restore")


class Command(BaseCommand):
    help = (
        "Lista backups disponibles en S3 y restaura el seleccionado "
        "(soporta SQLite y PostgreSQL)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--key",
            dest="key",
            help="Clave completa (u nombre) del objeto en S3 a restaurar",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            dest="yes",
            help="No pedir confirmación antes de sobrescribir la BD",
        )
        parser.add_argument(
            "--list-only",
            action="store_true",
            dest="list_only",
            help="Sólo listar los backups disponibles y salir",
        )

    def _get_env(self, name: str, default: str | None = None, required: bool = False) -> str:
        value = os.environ.get(name, default)
        if required and not value:
            raise CommandError(f"La variable de entorno '{name}' es obligatoria y no está definida.")
        return value or ""

    def _get_aws_config(self) -> dict:
        return {
            "aws_access_key_id": self._get_env("AWS_ACCESS_KEY_ID", required=True),
            "aws_secret_access_key": self._get_env("AWS_SECRET_ACCESS_KEY", required=True),
            "bucket": self._get_env("AWS_STORAGE_BUCKET_NAME", required=True),
            "region": self._get_env("AWS_S3_REGION_NAME", default="us-east-1"),
            "prefix": self._get_env("AWS_S3_BACKUP_PREFIX", default="backups/"),
        }

    def _get_db_engine(self) -> str:
        engine = settings.DATABASES["default"]["ENGINE"]
        if "sqlite" in engine:
            return "sqlite"
        if "postgresql" in engine or "postgis" in engine:
            return "postgresql"
        raise CommandError(f"Motor de base de datos no soportado para restore: {engine}")

    def _list_backups(self, s3_client, aws_cfg: dict) -> list:
        prefix = aws_cfg["prefix"]
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=aws_cfg["bucket"], Prefix=prefix)
        objects = []
        for page in pages:
            for obj in page.get("Contents", []):
                objects.append(obj)
        # Ordenar por fecha descendente
        objects.sort(key=lambda o: o["LastModified"], reverse=True)
        return objects

    def _download_obj(self, s3_client, aws_cfg: dict, key: str, dest_path: str) -> None:
        try:
            s3_client.download_file(aws_cfg["bucket"], key, dest_path)
        except Exception as exc:
            raise CommandError(f"Error descargando {key} desde S3: {exc}")

    def _decompress_gz(self, gz_path: str) -> str:
        if not gz_path.endswith(".gz"):
            return gz_path
        out_path = gz_path[:-3]
        with gzip.open(gz_path, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(gz_path)
        return out_path

    def _restore_sqlite(self, src_db_path: str) -> None:
        db_path = str(settings.DATABASES["default"]["NAME"])
        if not os.path.isfile(src_db_path):
            raise CommandError(f"Archivo SQLite descargado no existe: {src_db_path}")
        # Hacer copia de seguridad de la DB actual antes de sobrescribir
        backup_now = f"{db_path}.pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.bak"
        try:
            if os.path.isfile(db_path):
                shutil.copy2(db_path, backup_now)
            shutil.copy2(src_db_path, db_path)
        except Exception as exc:
            raise CommandError(f"Error al restaurar SQLite: {exc}")

    def _restore_postgresql(self, sql_path: str) -> None:
        db = settings.DATABASES["default"]
        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]

        cmd = [
            "psql",
            "--dbname",
            db["NAME"],
        ]
        if db.get("HOST"):
            cmd += ["--host", db["HOST"]]
        if db.get("PORT"):
            cmd += ["--port", str(db["PORT"]) ]
        if db.get("USER"):
            cmd += ["--username", db["USER"]]

        cmd += ["-f", sql_path]

        try:
            subprocess.run(cmd, env=env, check=True)
        except FileNotFoundError:
            raise CommandError(
                "psql no se encontró en el PATH. Instala cliente PostgreSQL para poder restaurar."
            )
        except subprocess.CalledProcessError as exc:
            raise CommandError(f"Error al ejecutar psql (código {exc.returncode})")

    def handle(self, *args, **options):
        self.stdout.write("═" * 60)
        self.stdout.write(" Restore de base de datos desde AWS S3")
        self.stdout.write("═" * 60)

        aws_cfg = self._get_aws_config()

        try:
            try:
                import boto3
                from botocore.exceptions import BotoCoreError, ClientError
            except ImportError:
                raise CommandError("La librería boto3 no está instalada. Instala boto3 primero.")

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_cfg["aws_access_key_id"],
                aws_secret_access_key=aws_cfg["aws_secret_access_key"],
                region_name=aws_cfg["region"],
            )

            objects = self._list_backups(s3_client, aws_cfg)
            if not objects:
                self.stdout.write("No se encontraron backups en el bucket especificado.")
                return

            # Presentar últimos 5
            top = objects[:5]
            self.stdout.write("Backups disponibles (recientes primero):")
            for idx, obj in enumerate(top, start=1):
                when = obj["LastModified"].astimezone().strftime("%Y-%m-%d %H:%M:%S %Z") if obj.get("LastModified") else "-"
                name = obj["Key"]
                size_kb = obj.get("Size", 0) / 1024
                self.stdout.write(f"  {idx}. {name} — {size_kb:.1f} KB — {when}")

            if options.get("list_only"):
                return

            chosen_key = options.get("key")
            if chosen_key:
                # permitir que el usuario pase sólo el basename
                match = None
                for obj in objects:
                    if obj["Key"] == chosen_key or os.path.basename(obj["Key"]) == chosen_key:
                        match = obj["Key"]
                        break
                if not match:
                    raise CommandError(f"No se encontró un objeto en S3 con clave o nombre: {chosen_key}")
                key_to_restore = match
            else:
                # Preguntar al usuario por índice
                prompt = "Selecciona el número del backup a restaurar (1-%d): " % len(top)
                while True:
                    val = input(prompt).strip()
                    if not val:
                        continue
                    try:
                        n = int(val)
                        if 1 <= n <= len(top):
                            key_to_restore = top[n - 1]["Key"]
                            break
                    except ValueError:
                        pass

            self.stdout.write(f"Seleccionado: {key_to_restore}")

            if not options.get("yes"):
                confirm = input("ADVERTENCIA: Esto sobrescribirá los datos actuales. ¿Estás seguro? [y/N]: ")
                if confirm.lower() not in ("y", "yes"):
                    self.stdout.write("Restauración cancelada por el usuario.")
                    return

            tmp_dir = tempfile.mkdtemp(prefix="django_restore_")
            try:
                filename = os.path.basename(key_to_restore)
                local_gz = os.path.join(tmp_dir, filename)
                self.stdout.write("Descargando desde S3...")
                self._download_obj(s3_client, aws_cfg, key_to_restore, local_gz)

                self.stdout.write("Descomprimiendo archivo...")
                local_path = self._decompress_gz(local_gz)

                engine = self._get_db_engine()
                self.stdout.write(f"Motor detectado: {engine}")

                if engine == "sqlite":
                    # El archivo descargado puede ser .sqlite3 o .sql; preferimos .sqlite3 reemplazante
                    if not local_path.endswith(".sqlite3") and not local_path.endswith(".sqlite"):
                        raise CommandError("El archivo descargado no parece ser una copia de SQLite (.sqlite, .sqlite3).")
                    self.stdout.write("Restaurando SQLite (se hará copia de seguridad local antes)...")
                    self._restore_sqlite(local_path)
                else:
                    # Postgres: si el archivo es .sql o .sql.gz
                    if not local_path.endswith(".sql"):
                        raise CommandError("El archivo descargado no parece ser un volcado SQL (.sql).")
                    self.stdout.write("Restaurando PostgreSQL vía psql...")
                    self._restore_postgresql(local_path)

                self.stdout.write(self.style.SUCCESS("Restauración completada correctamente."))

            finally:
                # Limpiar
                if tmp_dir and os.path.isdir(tmp_dir):
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                    logger.info("Directorio temporal eliminado: %s", tmp_dir)

        except CommandError:
            raise
        except Exception as exc:
            logger.exception("Error inesperado durante la restauración")
            raise CommandError(f"Error inesperado: {exc}")

        self.stdout.write("═" * 60)
