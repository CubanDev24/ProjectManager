from django.test import TestCase
from django.contrib.auth import get_user_model
from coreapp.models import Proyecto
from coreapp.models import Tarea
User = get_user_model()

class ProyectoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.proyecto = Proyecto.objects.create(
            nombre="Proyecto Test",
            descripcion="Descripción de prueba",
            responsable=self.user
        )

    def test_creacion_proyecto(self):
        """Verifica la creación básica de un proyecto."""
        self.assertEqual(self.proyecto.estado, 'no_iniciado')
        self.assertEqual(str(self.proyecto), "Proyecto Test (No Iniciado)")

    def test_responsable_es_integrante(self):
        """Valida que el responsable se añade automáticamente a los integrantes."""
        self.assertTrue(self.proyecto.integrantes.filter(id=self.user.id).exists())

    def test_estados_validos(self):
        """Prueba los choices de estado."""
        proyecto = Proyecto.objects.get(id=self.proyecto.id)
        proyecto.estado = 'en_progreso'
        proyecto.save()
        self.assertEqual(proyecto.get_estado_display(), "En Progreso")



class TareaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='taskuser', password='testpass123')
        self.proyecto = Proyecto.objects.create(nombre="Proyecto Tarea", responsable=self.user)
        self.tarea = Tarea.objects.create(
            proyecto=self.proyecto,
            titulo="Tarea de prueba",
            descripcion="Descripción de la tarea",
            prioridad='alta',
            asignado_a=self.user
        )

    def test_prioridad_default(self):
        """Verifica la prioridad por defecto (media)."""
        tarea = Tarea.objects.create(proyecto=self.proyecto, titulo="Tarea sin prioridad")
        self.assertEqual(tarea.prioridad, 'media')

    def test_estado_transiciones(self):
        """Prueba cambiar el estado de una tarea."""
        self.tarea.estado = 'completada'
        self.tarea.completado_por = self.user
        self.tarea.save()
        self.assertEqual(self.tarea.get_estado_display(), "Completada")