from django.db import models
from django.contrib.auth.models import User

# Nivel 1: Regimiento
class Regimiento(models.Model):
    nombre = models.CharField(max_length=100, default="75th Ranger Regiment")
    descripcion = models.TextField(blank=True, verbose_name="Misión / Historia")
    comandante = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Nombre del CO del Regimiento"
    )
    
    class Meta:
        verbose_name = "1. Regimiento"
        verbose_name_plural = "1. Regimientos"

    def __str__(self):
        return self.nombre
    
    def total_efectivos(self):
        # Cuenta miembros activos del regimiento y su estructura subordinada
        return Miembro.objects.filter(
            models.Q(escuadra__peloton__compania__regimiento=self) | 
            models.Q(regimiento=self),
            activo=True
        ).distinct().count()

# Nivel 2: Compañía
class Compania(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Alpha Company")
    regimiento = models.ForeignKey(
        Regimiento, 
        on_delete=models.CASCADE, 
        related_name="companias"
    )
    logo = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="URL del escudo"
    )

    class Meta:
        verbose_name = "2. Compañía"
        verbose_name_plural = "2. Compañías"

    def __str__(self):
        return f"Cía. {self.nombre}"

# Nivel 3: Pelotón
class Peloton(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: 1er Pelotón")
    compania = models.ForeignKey(
        Compania, 
        on_delete=models.CASCADE, 
        related_name="pelotones"
    )

    class Meta:
        verbose_name = "3. Pelotón"
        verbose_name_plural = "3. Pelotones"

    def __str__(self):
        return f"{self.nombre} [{self.compania.nombre}]"

# Nivel 4: Escuadra
class Escuadra(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Escuadra 1-1")
    peloton = models.ForeignKey(
        Peloton, 
        on_delete=models.CASCADE, 
        related_name="escuadras"
    )
    indicativo_radio = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Ej: Viking 1-1"
    )

    class Meta:
        verbose_name = "4. Escuadra"
        verbose_name_plural = "4. Escuadras"

    def __str__(self):
        return f"{self.peloton.compania.nombre} | {self.nombre}"

# Catálogo académico
class Rango(models.TextChoices):
    # Oficiales
    COL = 'COL', 'Coronel (COL)'
    LTC = 'LTC', 'Teniente Coronel (LTC)'
    MAJ = 'MAJ', 'Mayor (MAJ)'
    CPT = 'CPT', 'Capitán (CPT)'
    LT1 = '1LT', 'Teniente Primero (1LT)'
    LT2 = '2LT', 'Teniente Segundo (2LT)'
    # Warrant Officers
    CW5 = 'CW5', 'Chief Warrant Officer 5'
    CW4 = 'CW4', 'Chief Warrant Officer 4'
    CW3 = 'CW3', 'Chief Warrant Officer 3'
    CW2 = 'CW2', 'Chief Warrant Officer 2'
    WO1 = 'WO1', 'Warrant Officer 1'
    # Suboficiales
    CSM = 'CSM', 'Sargento Mayor de Comando (CSM)'
    SGM = 'SGM', 'Sargento Mayor (SGM)'
    SG1 = '1SG', 'Sargento Primero (1SG)'
    MSG = 'MSG', 'Sargento Maestro (MSG)'
    SFC = 'SFC', 'Sargento de Primera Clase (SFC)'
    SSG = 'SSG', 'Sargento de Estado Mayor (SSG)'
    SGT = 'SGT', 'Sargento (SGT)'
    # Tropa
    CPL = 'CPL', 'Cabo (CPL)'
    SPC = 'SPC', 'Especialista (SPC)'
    PFC = 'PFC', 'Soldado de Primera (PFC)'
    PV2 = 'PV2', 'Soldado (PV2)'
    PV1 = 'PV1', 'Recluta (PV1)'

class Curso(models.Model):
    sigla = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return f"[{self.sigla}] {self.nombre}"

# Personal
class Miembro(models.Model):
    # Identidad y sistema
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_milsim = models.CharField(max_length=100, verbose_name="Nick")
    rango = models.CharField(
        max_length=5, 
        choices=Rango.choices, 
        default=Rango.PV1
    )
    rol = models.CharField(max_length=100, default="Fusilero")
    
    # Asignación en la estructura (HQ o escuadra)
    regimiento = models.ForeignKey(Regimiento, on_delete=models.SET_NULL, null=True, blank=True)
    compania = models.ForeignKey(Compania, on_delete=models.SET_NULL, null=True, blank=True)
    peloton = models.ForeignKey(Peloton, on_delete=models.SET_NULL, null=True, blank=True)
    escuadra = models.ForeignKey(Escuadra, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Estado y datos extra
    activo = models.BooleanField(default=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    discord_id = models.CharField(max_length=50, blank=True)
    steam_id = models.CharField(max_length=50, blank=True)
    cursos = models.ManyToManyField(Curso, blank=True)
    notas_admin = models.TextField(blank=True, null=True, verbose_name="Notas de Administración")

    class Meta:
        verbose_name = "Operador"
        verbose_name_plural = "5. Personal"
        ordering = ['-rango', 'nombre_milsim']

    def __str__(self):
        return f"[{self.rango}] {self.nombre_milsim}"