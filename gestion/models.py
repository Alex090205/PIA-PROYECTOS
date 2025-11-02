from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


# === PERFIL DE USUARIO ===
class Perfil(models.Model):
    """
    Extiende el modelo User para definir roles (Administrador o Empleado)
    y opcionalmente un puesto o area.
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
    rfc = models.CharField(
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z&]{3,4}\d{6}[A-Z0-9]{3}$',
                message='RFC invalido. Debe cumplir el formato oficial (12 o 13 caracteres).',
                code='invalid_rfc',
            )
        ],
    )
    direccion = models.TextField(blank=True, null=True)
    correo = models.EmailField(max_length=100, blank=True)
    telefono = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(regex=r'^\d{10}$', message='El telefono debe tener 10 digitos.', code='invalid_phone')],
    )

    def __str__(self):
        return self.nombre

    def clean(self):
        super().clean()
        rfc_norm = (self.rfc or '').strip().upper()
        if rfc_norm:
            qs = Cliente.objects.filter(rfc__iexact=rfc_norm)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'rfc': 'Ya existe un cliente con ese RFC.'})

    def save(self, *args, **kwargs):
        if self.rfc is not None:
            self.rfc = self.rfc.strip().upper()
        super().save(*args, **kwargs)


# === PROYECTO ===
class Proyecto(models.Model):
    """
    Define los proyectos de la empresa y su relacion con clientes y administradores.
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
    cantidad_h = models.IntegerField()
    situacion = models.CharField(max_length=3, choices=SITUACION_CHOICES, default='ACT')

    # Relacion: un proyecto pertenece a un cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='proyectos'
    )

    # Relacion: varios administradores pueden supervisar un proyecto
    administradores = models.ManyToManyField(
        User,
        limit_choices_to={'is_staff': True},
        related_name='proyectos_administrados',
        blank=True
    )
    empleados = models.ManyToManyField(
        User,
        through='AsignacionProyecto',
        related_name='proyectos_como_empleado',
        blank=True,
        limit_choices_to={'is_staff': False}
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
        limit_choices_to={'is_staff': False},
        related_name='registros_horas'
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='registros_horas'
    )
    fecha = models.DateField()
    horas = models.IntegerField()
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.empleado.username} - {self.horas}h en {self.proyecto.nombre}"


# === ACTIVIDAD (BITACORA DE ACCIONES) ===
class Actividad(models.Model):
    """
    Registra acciones realizadas en el sistema (alta, edicion, eliminacion, etc.).
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.accion} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"


# === ASIGNACION DE PROYECTO A EMPLEADO ===
class AsignacionProyecto(models.Model):
    """
    Relacion Empleado <-> Proyecto con metadatos (rol, activo, fechas).
    """
    ROL_CHOICES = [
        ('DEV', 'Desarrollador'),
        ('PM', 'Project Manager'),
        ('QA', 'QA / Tester'),
        ('OT', 'Otro'),
    ]

    empleado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': False},
        related_name='asignaciones'
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    rol_en_proyecto = models.CharField(max_length=3, choices=ROL_CHOICES, default='OT')
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateField(auto_now_add=True)
    fecha_baja = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['empleado', 'proyecto'],
                condition=models.Q(activo=True),
                name='uq_asignacion_activa_por_empleado_proyecto'
            )
        ]

    def __str__(self):
        estado = 'Activo' if self.activo else 'Baja'
        return f"{self.empleado.username} -> {self.proyecto.nombre} ({estado})"


class PerfilEmpleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    primer_nombre = models.CharField(max_length=150)
    segundo_nombre = models.CharField(max_length=150, blank=True)
    primer_apellido = models.CharField(max_length=150)
    segundo_apellido = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.primer_nombre} {self.primer_apellido}"