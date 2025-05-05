from django.core.files.uploadedfile import SimpleUploadedFile
from coreapp.models import Documento
from django.test import TestCase
from django.contrib.auth import get_user_model
from coreapp.models import Proyecto
from django.urls import reverse

User = get_user_model()

class DocumentoViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='docuser', password='testpass123')
        self.proyecto = Proyecto.objects.create(nombre="Proyecto Doc", responsable=self.user)
        self.documento = Documento.objects.create(
            proyecto=self.proyecto,
            archivo=SimpleUploadedFile("test.txt", b"Contenido de prueba"),
            subido_por=self.user
        )

    def test_ver_documento_autorizado(self):
        """Usuario integrante puede ver documentos."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('ver_documento', args=[self.documento.id]))
        self.assertEqual(response.status_code, 200)

    def test_ver_documento_no_autorizado(self):
        """Usuario no autorizado recibe 403."""
        otro_user = User.objects.create_user(username='nodocuser', password='testpass123')
        self.client.force_login(otro_user)
        response = self.client.get(reverse('ver_documento', args=[self.documento.id]))
        self.assertEqual(response.status_code, 403)

class ProyectoCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='testpass123', rol='jefe_proyectos')
        self.url = reverse('proyecto_create')

    def test_crear_proyecto(self):
        """Usuario con rol 'jefe_proyectos' puede crear proyectos."""
        self.client.force_login(self.user)
        data = {
            "nombre": "Nuevo Proyecto",
            "descripcion": "Descripción",
            "responsable": self.user.id
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirección tras éxito
        self.assertTrue(Proyecto.objects.filter(nombre="Nuevo Proyecto").exists())