import json
from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from coreapp.models import Proyecto, Tarea

User = get_user_model()

class ProyectoTareaIntegrationTest(TestCase):
    def setUp(self):
        # Configuración común para todas las pruebas
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            rol='jefe_proyectos'  # Asumiendo que tienes este campo
        )
        self.client.login(username='testuser', password='testpass')

    def test_crear_proyecto_y_tarea(self):
        # Paso 1: Crear proyecto (similar a ProyectoCreateView)
        response = self.client.post(
            reverse('proyecto_create'),  # Nombre de tu URL para crear proyectos
            data={
                'nombre': 'Proyecto Test',
                'descripcion': 'Descripción',
                'responsable': self.user.id
            }
        )
        self.assertEqual(response.status_code, 302)
        proyecto = Proyecto.objects.get(nombre='Proyecto Test')

        # Paso 2: Crear tarea (usando tu API crear_tarea_api)
        response = self.client.post(
            reverse('crear_tarea_api', args=[proyecto.id]),
            data=json.dumps({
                'titulo': 'Tarea Test',
                'descripcion': 'Descripción',
                'prioridad': 'alta',
                'asignado_a': self.user.id,  # Campo requerido en tu modelo
                'fecha_tope': '2024-12-31T00:00:00Z'  # Ajusta el formato según necesites
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        tarea = Tarea.objects.get(titulo='Tarea Test')
        self.assertEqual(tarea.proyecto.id, proyecto.id)


