from django.db import models
from django.contrib.auth.models import User

# === Tabla: Cliente ===
class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, unique=True)
    direccion = models.TextField(blank=True, null=True)
    correo = models.EmailField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre

# === Tabla: Proyecto ===
class Proyecto(models.Model):
    SITUACION_CHOICES = [
        ('ACT', 'Activo'),
        ('PAU', 'Pausado'),
        ('FIN', 'Finalizado'),
        ('CAN', 'Cancelado'),
    ]
    
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicial = models.DateField()
    fecha_final = models.DateField(null=True, blank=True)
    cantidad_h = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, verbose_name="Horas Presupuestadas")
    situacion = models.CharField(max_length=3, choices=SITUACION_CHOICES, default='ACT')

    # --- Relaciones (Tablas Intermedias) ---
    # Tabla: Cliente_Proyecto
    clientes = models.ManyToManyField(Cliente, related_name='proyectos')

    # Tabla: Admin_Proyecto
    administradores = models.ManyToManyField(
        User,
        limit_choices_to={'is_staff': True}, # Solo permite añadir usuarios que sean staff
        related_name='proyectos_administrados'
    )

    def __str__(self):
        return self.nombre

# === Tabla: Registro_Horas ===
class RegistroHoras(models.Model):
    empleado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': False} # Solo permite añadir usuarios que NO sean staff
    )
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    fecha = models.DateField()
    horas = models.DecimalField(max_digits=5, decimal_places=2)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.empleado.username} - {self.horas} horas en '{self.proyecto.nombre}'"