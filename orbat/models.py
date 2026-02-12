from django.db import models
from django.contrib.auth.models import User

# --- 1. NIVEL: REGIMIENTO ---
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
        # Cuenta todos los miembros activos en toda la cadena de mando
        return Miembro.objects.filter(
            models.Q(escuadra__peloton__compania__regimiento=self) | 
            models.Q(regimiento=self),
            activo=True
        ).distinct().count()

# --- 2. NIVEL: COMPAÑÍA ---
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

# --- 3. NIVEL: PELOTÓN ---
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

# --- 4. NIVEL: ESCUADRA ---
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

# --- 5. ACADEMIA ---
class Rango(models.TextChoices):
    COL = 'COL', 'Coronel (COL)'
    LTC = 'LTC', 'Teniente Coronel (LTC)'
    MAJ = 'MAJ', 'Mayor (MAJ)'
    CPT = 'CPT', 'Capitán (CPT)'
    LT1 = 'LT1', 'Teniente Primero (1LT)'
    LT2 = 'LT2', 'Teniente Segundo (2LT)'
    CW5 = 'CW5', 'Chief Warrant Officer 5'
    CW4 = 'CW4', 'Chief Warrant Officer 4'
    WO1 = 'WO1', 'Warrant Officer 1'
    CSM = 'CSM', 'Sargento Mayor de Comando (CSM)'
    SG1 = 'SG1', 'Sargento Primero (1SG)'
    SFC = 'SFC', 'Sargento de Primera Clase (SFC)'
    SSG = 'SSG', 'Sargento de Estado Mayor (SSG)'
    SGT = 'SGT', 'Sargento (SGT)'
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

# --- 6. PERSONAL ---
class Miembro(models.Model):
    # Identidad y Sistema
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_milsim = models.CharField(max_length=100, verbose_name="Nick")
    rango = models.CharField(
        max_length=5, 
        choices=Rango.choices, 
        default=Rango.PV1
    )
    rol = models.CharField(max_length=100, default="Fusilero")
    
    # ASIGNACIÓN DE NIVEL (HQ o Escuadra)
    # Estos campos son los que faltan en tu base de datos actualmente
    regimiento = models.ForeignKey(Regimiento, on_delete=models.SET_NULL, null=True, blank=True)
    compania = models.ForeignKey(Compania, on_delete=models.SET_NULL, null=True, blank=True)
    peloton = models.ForeignKey(Peloton, on_delete=models.SET_NULL, null=True, blank=True)
    escuadra = models.ForeignKey(Escuadra, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Estado y Datos Extra
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