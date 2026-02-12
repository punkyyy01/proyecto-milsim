from django.db import models

# 1. EL MANDO (SINGLETON)
class Regimiento(models.Model):
    nombre = models.CharField(max_length=100, default="75th Ranger RGT")
    
    class Meta:
        verbose_name = "Sede del Mando"
        verbose_name_plural = "1. Mando Central"

    def __str__(self):
        return self.nombre

# 2. ACADEMIA Y CURSOS
class Fase(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Fase de Instrucción"
        verbose_name_plural = "Instrucción: Fases"

    def __str__(self):
        return self.nombre

class Curso(models.Model):
    sigla = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    fase = models.ForeignKey(Fase, on_delete=models.CASCADE, related_name="cursos")

    class Meta:
        verbose_name = "Curso / Especialidad"
        verbose_name_plural = "Instrucción: Cursos"

    def __str__(self):
        return f"[{self.sigla}] {self.nombre}"

# 3. UNIDADES
class Compania(models.Model):
    nombre = models.CharField(max_length=100)
    regimiento = models.ForeignKey(Regimiento, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Compañía"
        verbose_name_plural = "2. Compañías"

    def __str__(self):
        return self.nombre

class Escuadra(models.Model):
    nombre = models.CharField(max_length=100)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Escuadra"
        verbose_name_plural = "3. Escuadras"

    def __str__(self):
        return f"{self.nombre} ({self.compania.nombre})"

# 4. PERSONAL
class Miembro(models.Model):
    nombre_milsim = models.CharField(max_length=100)
    rango = models.CharField(max_length=50)
    escuadra = models.ForeignKey(Escuadra, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)
    cursos = models.ManyToManyField(Curso, blank=True)

    class Meta:
        verbose_name = "Soldado"
        verbose_name_plural = "4. Personal"

    def __str__(self):
        return f"{self.rango} {self.nombre_milsim}"