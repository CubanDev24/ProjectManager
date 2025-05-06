from django.contrib.auth.forms import UserCreationForm
from .models import (Usuario)
from django import forms
from .models import Proyecto, Tarea, ComentarioTarea, DocumentoTarea,ArchivoComentario, MeetingComment, Bug, Documento
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
User = get_user_model()

class UsuarioForm(UserCreationForm):
    rol = forms.ChoiceField(choices=Usuario.ROLES, label="Rol", required=True)
    class Meta:
        model = Usuario
        fields = ('rol', 'first_name', 'username', 'email', 'password1', 'password2')


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'})
    )
    first_name = forms.CharField(
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'})
    )

    # Campo rol usando las opciones definidas en el modelo
    rol = forms.ChoiceField(
        required=True,
        choices=Usuario.ROLES,
        initial='desarrollador',
        label="Tipo de Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'rol', 'password1', 'password2']

        # Personalización de widgets para los campos heredados
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalización de mensajes de ayuda/placeholder
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})


class PerfilForm(UserChangeForm):
    password = None  # Eliminamos el campo de contraseña del formulario

    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'imagen_perfil')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'responsable']
        labels = {
            'nombre': 'Nombre del Proyecto',
            'descripcion': 'Descripción',
            'responsable': 'Responsable',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtramos solo usuarios con rol de jefe de proyectos para ser responsables
        self.fields['responsable'].queryset = User.objects.filter(rol='jefe_proyectos')

class ProyectoUpdateForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'estado', 'responsable', 'presupuesto', 'recursos']
        labels = {
            'nombre': 'Nombre del Proyecto',
            'descripcion': 'Descripción',
            'estado': 'Estado',
            'responsable': 'Responsable',
            'presupuesto': 'Presupuesto',
            'recursos': 'Recursos',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'recursos': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = User.objects.filter(rol='jefe_proyectos')

class AgregarIntegranteForm(forms.ModelForm):
    integrantes = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True,
        label="Seleccionar nuevos integrantes"
    )

    class Meta:
        model = Proyecto
        fields = ['integrantes']

    def __init__(self, *args, **kwargs):
        proyecto = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if proyecto:
            # Excluir usuarios que ya son integrantes
            self.fields['integrantes'].queryset = User.objects.exclude(
                id__in=proyecto.integrantes.values_list('id', flat=True)
            ).order_by('first_name', 'last_name')


class RemoverIntegranteForm(forms.Form):
    integrantes = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Seleccionar integrantes a remover"
    )

    def __init__(self, *args, **kwargs):
        proyecto = kwargs.pop('proyecto', None)
        super().__init__(*args, **kwargs)
        if proyecto:
            self.fields['integrantes'].queryset = proyecto.integrantes.exclude(
                id=proyecto.responsable.id  # No permitir remover al responsable
            ).order_by('first_name', 'last_name')


class TareaForm(forms.ModelForm):
    def __init__(self, *args, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        if proyecto:
            self.fields['asignado_a'].queryset = proyecto.integrantes.all()

        # Personalizar los campos de selección
        self.fields['prioridad'].widget = forms.Select(choices=Tarea.PRIORIDADES)
        self.fields['estado'].widget = forms.Select(choices=Tarea.ESTADOS_TAREA)

        # Mejorar la apariencia de los campos
        self.fields['fecha_tope'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-input'
        })
        self.fields['descripcion'].widget = forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-input'
        })

    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'prioridad', 'estado', 'asignado_a', 'fecha_tope']


class DocumentoTareaForm(forms.ModelForm):
    class Meta:
        model = DocumentoTarea
        fields = ['archivo', 'nombre']


class ComentarioTareaForm(forms.ModelForm):
    class Meta:
        model = ComentarioTarea
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 3}),
        }


class ArchivoComentarioForm(forms.ModelForm):
    class Meta:
        model = ArchivoComentario
        fields = ['archivo', 'nombre']


# forms.py
class CambiarEstadoTareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['estado']

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_choices(usuario)

    def set_choices(self, usuario):
        if usuario and usuario.rol == 'jefe_proyectos':
            self.fields['estado'].choices = [
                ('pendiente', 'Pendiente'),
                ('en_progreso', 'En Progreso'),
                ('completada', 'Completada'),
                ('rechazada', 'Rechazada'),
                ('aprobada', 'Aprobada'),
            ]
        else:
            self.fields['estado'].choices = [
                ('pendiente', 'Pendiente'),
                ('en_progreso', 'En Progreso'),
                ('completada', 'Completada'),
            ]

    def clean_estado(self):
        estado = self.cleaned_data.get('estado')
        current_estado = self.instance.estado if self.instance else None

        # Validaciones adicionales según tu lógica de negocio
        if current_estado == 'completada' and estado == 'en_progreso':
            raise forms.ValidationError("No se puede revertir a 'En Progreso' desde 'Completada'")

        return estado

class MeetingCommentForm(forms.ModelForm):
    class Meta:
        model = MeetingComment
        fields = ['comment', 'is_meeting_link', 'meeting_url']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Escribe tu comentario...'
            }),
            'is_meeting_link': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'meeting_url': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'https://meet.google.com/abc-xyz-123'
            })
        }


class BugForm(forms.ModelForm):
    def __init__(self, *args, proyecto=None, **kwargs):
        # Remover reportado_por de los campos iniciales si existe
        if 'reportado_por' in kwargs.get('initial', {}):
            del kwargs['initial']['reportado_por']

        super().__init__(*args, **kwargs)

        if proyecto:
            self.fields['asignado_a'].queryset = proyecto.integrantes.all()


        # Eliminar el campo reportado_por del formulario si existe
        if 'reportado_por' in self.fields:
            del self.fields['reportado_por']

        # Personalizar los campos de selección
        self.fields['prioridad'].widget = forms.Select(choices=Bug.PRIORIDADES_BUG)
        self.fields['estado'].widget = forms.Select(choices=Bug.ESTADOS_BUG)
        self.fields['tipo'].widget = forms.Select(choices=Bug.TIPOS_BUG)

        # Mejorar la apariencia de los campos
        self.fields['fecha_tope'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-input'
        })
        self.fields['descripcion'].widget = forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-input'
        })
        self.fields['pasos_reproducir'].widget = forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-input',
            'placeholder': 'Describe los pasos necesarios para reproducir el bug...'
        })

    class Meta:
        model = Bug
        # No incluir reportado_por en los campos del formulario
        fields = ['titulo', 'descripcion', 'pasos_reproducir', 'tipo', 'prioridad', 'estado', 'asignado_a',
                  'fecha_tope']


class CambiarEstadoBugForm(forms.ModelForm):
    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        # Limitar las opciones de estado según el estado actual
        if self.instance:
            estado_actual = self.instance.estado
            opciones_estado = []

            if estado_actual == 'reportado':
                opciones_estado = [
                    ('reportado', 'Reportado'),
                    ('asignado', 'Asignado'),
                    ('rechazado', 'Rechazado')
                ]
            elif estado_actual == 'asignado':
                opciones_estado = [
                    ('asignado', 'Asignado'),
                    ('en_progreso', 'En Progreso'),
                    ('rechazado', 'Rechazado')
                ]
            elif estado_actual == 'en_progreso':
                opciones_estado = [
                    ('en_progreso', 'En Progreso'),
                    ('resuelto', 'Resuelto'),
                    ('rechazado', 'Rechazado')
                ]
            elif estado_actual == 'resuelto':
                opciones_estado = [
                    ('resuelto', 'Resuelto'),
                    ('verificado', 'Verificado'),
                    ('rechazado', 'Rechazado')
                ]
            elif estado_actual == 'verificado':
                opciones_estado = [
                    ('verificado', 'Verificado'),
                    ('cerrado', 'Cerrado')
                ]

            self.fields['estado'].widget = forms.Select(choices=opciones_estado)

    class Meta:
        model = Bug
        fields = ['estado']


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nombre', 'tipo', 'archivo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, proyecto=None, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proyecto = proyecto
        self.usuario = usuario