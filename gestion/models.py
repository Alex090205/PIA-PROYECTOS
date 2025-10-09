from django.db import models
from django.contrib.auth.models import User


# === PERFIL DE USUARIO ===
class Perfil(models.Model):
    """
    Extiende el modelo User para definir roles (Administrador o Empleado)
    y opcionalmente un puesto o área.
    """
    TIPO_CHOICES = [
        ('Administrador', 'Administrador'),
        ('Empleado', 'Empleado'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='Empleado')
    puesto = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.tipo})"


# === CLIENTE ===
class Cliente(models.Model):
    """
    Representa a los clientes relacionados con los proyectos.
    """
    nombre = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, unique=True)
    direccion = models.TextField(blank=True, null=True)
    correo = models.EmailField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre


# === PROYECTO ===
class Proyecto(models.Model):
    """
    Define los proyectos de la empresa y su relación con clientes y administradores.
    """
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
    cantidad_h = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Horas Presupuestadas"
    )
    situacion = models.CharField(max_length=3, choices=SITUACION_CHOICES, default='ACT')

    # Relación: un proyecto pertenece a un cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='proyectos'
    )

    # Relación: varios administradores pueden supervisar un proyecto
    administradores = models.ManyToManyField(
        User,
        limit_choices_to={'is_staff': True},
        related_name='proyectos_administrados',
        blank=True
    )

    def __str__(self):
        return self.nombre


# === REGISTRO DE HORAS ===
class RegistroHoras(models.Model):
    """
    Registra las horas trabajadas por los empleados en proyectos.
    """
    empleado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': False},  # Solo usuarios que NO son staff
        related_name='registros_horas'
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='registros_horas'
    )
    fecha = models.DateField()
    horas = models.DecimalField(max_digits=5, decimal_places=2)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.empleado.username} - {self.horas}h en {self.proyecto.nombre}"


# === ACTIVIDAD (BITÁCORA DE ACCIONES) FALTA DEFINIR FUNCION===
class Actividad(models.Model):
    """
    Registra acciones realizadas en el sistema (alta, edición, eliminación, etc.)
    para fines de auditoría o seguimiento administrativo.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.accion} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
