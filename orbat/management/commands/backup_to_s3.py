"""
Management command: backup_to_s3
================================
Genera un volcado de la base de datos (SQLite o PostgreSQL) y lo sube
a un bucket de AWS S3.  Las credenciales se leen exclusivamente de
variables de entorno para no comprometer secretos en el código fuente.

Variables de entorno requeridas:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_STORAGE_BUCKET_NAME

Variables opcionales:
  - AWS_S3_REGION_NAME      (default: us-east-1)
  - AWS_S3_BACKUP_PREFIX    (default: backups/)
  - BACKUP_RETENTION_DAYS   (default: 0 = sin limpieza automática)

Uso:
  python manage.py backup_to_s3
"""

import gzip
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger("orbat.backup")


class Command(BaseCommand):
    help = (
        "Genera un backup de la base de datos y lo sube a AWS S3. "
        "Soporta SQLite y PostgreSQL."
    )

    # ------------------------------------------------------------------
    # Helpers de configuración
    # ------------------------------------------------------------------
    def _get_env(self, name: str, default: str | None = None, required: bool = False) -> str:
        """Lee una variable de entorno; lanza error si es requerida y falta."""
        value = os.environ.get(name, default)
        if required and not value:
            raise CommandError(
                f"La variable de entorno '{name}' es obligatoria y no está definida."
            )
        return value or ""

    def _get_aws_config(self) -> dict:
        """Retorna las credenciales y configuración de AWS desde el entorno."""
        return {
            "aws_access_key_id": self._get_env("AWS_ACCESS_KEY_ID", required=True),
            "aws_secret_access_key": self._get_env("AWS_SECRET_ACCESS_KEY", required=True),
            "bucket": self._get_env("AWS_STORAGE_BUCKET_NAME", required=True),
            "region": self._get_env("AWS_S3_REGION_NAME", default="us-east-1"),
            "prefix": self._get_env("AWS_S3_BACKUP_PREFIX", default="backups/"),
        }

    # ------------------------------------------------------------------
    # Detección del motor de base de datos
    # ------------------------------------------------------------------
    def _get_db_engine(self) -> str:
        """Devuelve 'sqlite' o 'postgresql' según la configuración activa."""
        engine = settings.DATABASES["default"]["ENGINE"]
        if "sqlite" in engine:
            return "sqlite"
        if "postgresql" in engine or "postgis" in engine:
            return "postgresql"
        raise CommandError(
            f"Motor de base de datos no soportado para backup: {engine}"
        )

    # ------------------------------------------------------------------
    # Volcados
    # ------------------------------------------------------------------
    def _dump_sqlite(self, dest_path: str) -> None:
        """Copia el archivo SQLite al destino (volcado binario)."""
        db_path = str(settings.DATABASES["default"]["NAME"])
        if not os.path.isfile(db_path):
            raise CommandError(f"No se encontró el archivo SQLite en: {db_path}")

        logger.info("Copiando archivo SQLite: %s → %s", db_path, dest_path)
        shutil.copy2(db_path, dest_path)

    def _dump_postgresql(self, dest_path: str) -> None:
        """Ejecuta pg_dump y guarda la salida SQL en *dest_path*."""
        db = settings.DATABASES["default"]

        # Construir entorno con PGPASSWORD para evitar prompt interactivo
        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]

        cmd = [
            "pg_dump",
            "--no-owner",
            "--no-privileges",
            "--format=plain",
        ]

        if db.get("HOST"):
            cmd += ["--host", db["HOST"]]
        if db.get("PORT"):
            cmd += ["--port", str(db["PORT"])]
        if db.get("USER"):
            cmd += ["--username", db["USER"]]

        cmd.append(db["NAME"])

        logger.info("Ejecutando pg_dump para la base '%s'…", db["NAME"])
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=600,  # 10 min máximo
            )
        except FileNotFoundError:
            raise CommandError(
                "pg_dump no se encontró en el PATH del sistema. "
                "Asegúrate de que las herramientas de cliente de PostgreSQL estén instaladas."
            )
        except subprocess.TimeoutExpired:
            raise CommandError("pg_dump excedió el tiempo máximo de ejecución (10 min).")
        except subprocess.CalledProcessError as exc:
            raise CommandError(f"pg_dump falló (código {exc.returncode}): {exc.stderr}")

        with open(dest_path, "w", encoding="utf-8") as fh:
            fh.write(result.stdout)

    # ------------------------------------------------------------------
    # Compresión
    # ------------------------------------------------------------------
    @staticmethod
    def _gzip_file(src_path: str) -> str:
        """Comprime *src_path* con gzip y devuelve la ruta del .gz resultante."""
        gz_path = src_path + ".gz"
        with open(src_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        # Eliminar el archivo sin comprimir
        os.remove(src_path)
        return gz_path

    # ------------------------------------------------------------------
    # Subida a S3
    # ------------------------------------------------------------------
    @staticmethod
    def _upload_to_s3(file_path: str, aws_cfg: dict, object_key: str) -> str:
        """Sube *file_path* a S3 y devuelve la URI s3://bucket/key."""
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise CommandError(
                "La librería boto3 no está instalada. "
                "Ejecuta: pip install boto3"
            )

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_cfg["aws_access_key_id"],
            aws_secret_access_key=aws_cfg["aws_secret_access_key"],
            region_name=aws_cfg["region"],
        )

        full_key = f"{aws_cfg['prefix']}{object_key}"
        s3_uri = f"s3://{aws_cfg['bucket']}/{full_key}"

        logger.info("Subiendo %s → %s …", file_path, s3_uri)
        try:
            s3_client.upload_file(
                Filename=file_path,
                Bucket=aws_cfg["bucket"],
                Key=full_key,
                ExtraArgs={"ServerSideEncryption": "AES256"},
            )
        except (BotoCoreError, ClientError) as exc:
            raise CommandError(f"Error al subir a S3: {exc}")

        return s3_uri

    # ------------------------------------------------------------------
    # Limpieza local
    # ------------------------------------------------------------------
    @staticmethod
    def _cleanup(tmp_dir: str) -> None:
        """Elimina el directorio temporal y todo su contenido."""
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
            logger.info("Directorio temporal eliminado: %s", tmp_dir)

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        self.stdout.write("═" * 60)
        self.stdout.write(" Backup de base de datos → AWS S3")
        self.stdout.write("═" * 60)

        tmp_dir: str | None = None

        try:
            # 1. Leer configuración AWS
            aws_cfg = self._get_aws_config()

            # 2. Detectar motor
            engine = self._get_db_engine()
            self.stdout.write(f"  Motor detectado: {engine}")

            # 3. Preparar directorio temporal
            tmp_dir = tempfile.mkdtemp(prefix="django_backup_")
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")

            if engine == "sqlite":
                dump_filename = f"backup_{timestamp}.sqlite3"
                dump_path = os.path.join(tmp_dir, dump_filename)
                self._dump_sqlite(dump_path)
            else:
                dump_filename = f"backup_{timestamp}.sql"
                dump_path = os.path.join(tmp_dir, dump_filename)
                self._dump_postgresql(dump_path)

            dump_size_mb = os.path.getsize(dump_path) / (1024 * 1024)
            self.stdout.write(
                f"  Volcado generado: {dump_filename} ({dump_size_mb:.2f} MB)"
            )

            # 4. Comprimir
            gz_path = self._gzip_file(dump_path)
            gz_size_mb = os.path.getsize(gz_path) / (1024 * 1024)
            gz_filename = os.path.basename(gz_path)
            self.stdout.write(
                f"  Comprimido: {gz_filename} ({gz_size_mb:.2f} MB)"
            )

            # 5. Subir a S3
            s3_uri = self._upload_to_s3(gz_path, aws_cfg, gz_filename)

            # 6. Éxito
            self.stdout.write(self.style.SUCCESS(
                f"\n  ✔ Backup subido correctamente: {s3_uri}"
            ))
            logger.info("Backup completado con éxito: %s", s3_uri)

        except CommandError:
            # Re-lanzar para que Django muestre el error limpiamente
            raise

        except Exception as exc:
            logger.exception("Error inesperado durante el backup")
            raise CommandError(f"Error inesperado: {exc}")

        finally:
            # 7. Limpieza del directorio temporal (siempre)
            if tmp_dir:
                self._cleanup(tmp_dir)
                self.stdout.write("  Archivos temporales eliminados.")

        self.stdout.write("═" * 60)
