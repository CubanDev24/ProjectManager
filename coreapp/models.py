from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Count, Q

# Create your models here.
class Usuario(AbstractUser):
    ROLES = [
        ('jefe_proyectos', 'Jefe de Proyectos'),
        ('desarrollador', 'Desarrollador'),
    ]
    rol = models.CharField(max_length=15, choices=ROLES, default='desarrollador')
    imagen_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

    def get_short_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username



User = get_user_model()


class Proyecto(models.Model):
    ESTADOS_PROYECTO = [
        ('no_iniciado', 'No Iniciado'),
        ('en_progreso', 'En Progreso'),
        ('en_pausa', 'En Pausa'),
        ('cancelado', 'Cancelado'),
        ('completado', 'Completado'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre del Proyecto")
    descripcion = models.TextField(verbose_name="Descripción del Proyecto")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_PROYECTO,
        default='no_iniciado',
        verbose_name="Estado del Proyecto"
    )
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='proyectos_responsable',
        verbose_name="Responsable del Proyecto"
    )
    integrantes = models.ManyToManyField(
        User,
        related_name='proyectos_integrante',
        blank=True,
        verbose_name="Integrantes del Proyecto"
    )
    presupuesto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name="Presupuesto del Proyecto"
    )
    recursos = models.TextField(
        null=True,
        blank=True,
        verbose_name="Recursos del Proyecto"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

    def save(self, *args, **kwargs):
        # Si es un nuevo proyecto, asegurarse de que el responsable sea integrante
        if self.pk is None and self.responsable:
            super().save(*args, **kwargs)
            self.integrantes.add(self.responsable)
        else:
            super().save(*args, **kwargs)

    @property
    def tareas_completadas(self):
        return self.tareas.filter(estado='completada')

    @property
    def tareas_por_estado(self):
        return dict(self.tareas.values_list('estado').annotate(count=Count('estado')))



class Tarea(models.Model):
    PRIORIDADES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    ESTADOS_TAREA = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('rechazada', 'Rechazada'),
        ('aprobada', 'Aprobada'),
    ]
    titulo_corto = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Título corto"
    )

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='tareas',
        verbose_name="Proyecto"
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDADES,
        default='media',
        verbose_name="Prioridad"
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS_TAREA,
        default='pendiente',
        verbose_name="Estado"
    )
    asignado_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tareas_asignadas',
        verbose_name="Asignado a"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_tope = models.DateTimeField(verbose_name="Fecha Tope", null=True, blank=True)
    completado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tareas_completadas',
        verbose_name="Completado por"
    )
    fecha_completado = models.DateTimeField(null=True, blank=True)
    aprobado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tareas_aprobadas',
        verbose_name="Aprobado por"
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ['-prioridad', 'fecha_tope']

    def __str__(self):
        return f"{self.titulo} ({self.get_prioridad_display()})"

    def save(self, *args, **kwargs):
        # Generar título corto si está vacío o si el título cambió
        if not self.titulo_corto or (self.pk and self.titulo != Tarea.objects.get(pk=self.pk).titulo):
            palabras = self.titulo.split()[:5]  # Primeras 5 palabras
            self.titulo_corto = ' '.join(palabras).strip()[:50]  # Limitar a 50 caracteres

        super().save(*args, **kwargs)


class DocumentoTarea(models.Model):
    tarea = models.ForeignKey(
        Tarea,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name="Tarea"
    )
    archivo = models.FileField(upload_to='documentos_tareas/', verbose_name="Archivo")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del documento")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Subido por"
    )

    class Meta:
        verbose_name = "Documento de Tarea"
        verbose_name_plural = "Documentos de Tarea"

    def __str__(self):
        return self.nombre


class ComentarioTarea(models.Model):
    tarea = models.ForeignKey(
        Tarea,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name="Tarea"
    )
    contenido = models.TextField(verbose_name="Contenido")
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comentario de Tarea"
        verbose_name_plural = "Comentarios de Tarea"
        ordering = ['fecha_creacion']

    def __str__(self):
        return f"Comentario de {self.usuario.username} en {self.tarea.titulo}"


class ArchivoComentario(models.Model):
    comentario = models.ForeignKey(
        ComentarioTarea,
        on_delete=models.CASCADE,
        related_name='archivos',
        verbose_name="Comentario"
    )
    archivo = models.FileField(upload_to='archivos_comentarios/', verbose_name="Archivo")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del archivo")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Archivo de Comentario"
        verbose_name_plural = "Archivos de Comentario"

    def __str__(self):
        return self.nombre




class MeetingComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_meeting_link = models.BooleanField(default=False)
    meeting_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comentario de {self.user.username} - {self.created_at}"





class Bug(models.Model):
    PRIORIDADES_BUG = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critico', 'Crítico'),
    ]

    ESTADOS_BUG = [
        ('reportado', 'Reportado'),
        ('asignado', 'Asignado'),
        ('en_progreso', 'En Progreso'),
        ('resuelto', 'Resuelto'),
        ('verificado', 'Verificado'),
        ('cerrado', 'Cerrado'),
        ('rechazado', 'Rechazado'),
    ]

    TIPOS_BUG = [
        ('error', 'Error'),
        ('funcional', 'Funcionalidad'),
        ('seguridad', 'Seguridad'),
        ('rendimiento', 'Rendimiento'),
        ('usabilidad', 'Usabilidad'),
        ('otros', 'Otros'),
    ]

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='bugs',
        verbose_name="Proyecto"
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    pasos_reproducir = models.TextField(
        verbose_name="Pasos para Reproducir",
        blank=True,
        null=True
    )
    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDADES_BUG,
        default='media',
        verbose_name="Prioridad"
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS_BUG,
        default='reportado',
        verbose_name="Estado"
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPOS_BUG,
        default='error',
        verbose_name="Tipo de Bug"
    )
    reportado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bugs_reportados',
        verbose_name="Reportado por"
    )
    asignado_a = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bugs_asignados',
        verbose_name="Asignado a"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_tope = models.DateTimeField(verbose_name="Fecha Tope", null=True, blank=True)
    resuelto_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bugs_resueltos',
        verbose_name="Resuelto por"
    )
    fecha_resuelto = models.DateTimeField(null=True, blank=True)
    verificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bugs_verificados',
        verbose_name="Verificado por"
    )
    fecha_verificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Bug"
        verbose_name_plural = "Bugs"
        ordering = ['-prioridad', 'fecha_tope']

    def __str__(self):
        return f"{self.titulo} ({self.get_prioridad_display()})"


class Documento(models.Model):
    REQUISITOS = 'RT'
    PRUEBAS = 'PB'
    INFORME = 'IN'
    DISENO = 'DS'
    OTRO = 'OT'

    TIPOS_DOCUMENTO = [
        (REQUISITOS, 'Requisitos'),
        (PRUEBAS, 'Pruebas'),
        (INFORME, 'Informe'),
        (DISENO, 'Diseño'),
        (OTRO, 'Otro'),
    ]

    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=2, choices=TIPOS_DOCUMENTO, default=OTRO)
    archivo = models.FileField(upload_to='media/documentos/')
    fecha_subido = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='documentos_proyecto')

    def __str__(self):
        return self.nombre

    def get_tipo_display(self):
        return dict(self.TIPOS_DOCUMENTO).get(self.tipo, 'Desconocido')