import os
import django

# Configuración del entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_milsim.settings')
django.setup()

from orbat.models import Curso

cursos_data = [
    ("AMU", "Amunicionador"), ("BOOTCAMP", "Entrenamiento Básico"),
    ("CBRS", "Curso Básico de Radio"), ("CIBI", "Curso de Introducción Básica"),
    ("CNB", "Navegación Básica"), ("COD", "Conductor Designado"),
    ("CTC", "Trato Civil"), ("CTM", "Trato Militar"),
    ("IAR", "Introducción Aerotransportada Ranger"), ("IPA", "Introducción a Primeros Auxilios"),
    ("PB", "Pruebas Básicas"), ("CICU", "Combate Urbano Inicial"),
    ("CIA", "Infantería Avanzada"), ("OPNS", "Operador Nocturno"),
    ("MOUT", "Operaciones Urbanas"), ("COB1", "CQB Básico"),
    ("COB2", "CQB Intermedio"), ("AAR", "Ametrallador"),
    ("AT", "Anti Tanque"), ("GRN", "Granadero"),
    ("MTR", "Morterista"), ("EOD-B", "Explosivos Básico"),
    ("ENF", "Enfermero de Campo"), ("PAR", "Paracaidista HALO/HAHO"),
    ("RTO", "Radio Operador"), ("TD", "Tirador Designado"),
    ("ROL", "Introducción al Role Player")
]

for siglas, nombre in cursos_data:
    obj, created = Curso.objects.get_or_create(nombre=nombre, defaults={'siglas': siglas})
    if created:
        print(f"✔️ Creado: {nombre}")
    else:
        print(f"⚠️ Ya existía: {nombre}")

print("\n🚀 ¡Cursos cargados con éxito!")