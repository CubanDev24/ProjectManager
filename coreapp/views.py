from datetime import timezone
from django.urls import reverse
from .models import Proyecto, Tarea, DocumentoTarea, ComentarioTarea, ArchivoComentario
from .forms import (
    TareaForm, DocumentoTareaForm, ComentarioTareaForm,
    ArchivoComentarioForm, CambiarEstadoTareaForm, BugForm, CambiarEstadoBugForm, DocumentoForm, RemoverIntegranteForm,
    PerfilForm, RegistroForm
)
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import UsuarioForm, MeetingCommentForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Proyecto, MeetingComment, Bug, Documento, Usuario
from .forms import ProyectoForm, ProyectoUpdateForm, AgregarIntegranteForm
from django.contrib import messages
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.utils import timezone
import json
from .models import Proyecto, Tarea, DocumentoTarea, ComentarioTarea
from .forms import TareaForm, DocumentoTareaForm, ComentarioTareaForm, ArchivoComentarioForm, CambiarEstadoTareaForm
from django.contrib.auth import login

# Create your views here.
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_usuario')  # Redirigir a la página de inicio o donde prefieras
    else:
        form = UsuarioForm()

    return render(request, 'usuarios/crear_usuario.html', {'form': form})


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirige a la página principal después del registro
    else:
        form = RegistroForm()

    return render(request, 'usuarios/registro.html', {'form': form})


@login_required
def actualizar_perfil(request):
    usuario = request.user

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Perfil actualizado correctamente',
                'imagen_url': usuario.imagen_perfil.url if usuario.imagen_perfil else None
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors.as_json()
            }, status=400)

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)

def landing_page(request):
    return render(request, 'landing_page.html')


def info_page(request):
    return render(request, 'info.html')

def home(request):
    proyecto_form=ProyectoForm()
    # Proyectos del usuario
    proyectos = Proyecto.objects.filter(
        Q(responsable=request.user) | Q(integrantes=request.user)
    ).distinct()

    # Estadísticas rápidas
    active_projects_count = proyectos.filter(estado='en_progreso').count()
    pending_tasks_count = Tarea.objects.filter(
        asignado_a=request.user,
        estado='pendiente'
    ).count()

    completed_tasks_count = Tarea.objects.filter(
        asignado_a=request.user,
        estado='completada'
    ).count()
    total_tasks_count = Tarea.objects.filter(asignado_a=request.user).count()
    completion_percentage = (completed_tasks_count / total_tasks_count * 100) if total_tasks_count > 0 else 0

    today_tasks_count = Tarea.objects.filter(
        asignado_a=request.user,
        fecha_tope=timezone.now().date()
    ).count()

    # Tareas del usuario
    user_pending_tasks = Tarea.objects.filter(
        asignado_a=request.user,
        estado='pendiente'
    ).order_by('-fecha_creacion')[:3]

    # Notificaciones (usando comentarios como ejemplo)
    notifications = ComentarioTarea.objects.filter(
        tarea__asignado_a=request.user
    ).order_by('-fecha_creacion')[:3]

    # Datos para gráficos
    project_status_data = Proyecto.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')

    monthly_tasks_data = Tarea.objects.filter(
        asignado_a=request.user
    ).annotate(
        month=TruncMonth('fecha_creacion')
    ).values('month').annotate(
        completadas=Count('id', filter=Q(estado='completada')),
        pendientes=Count('id', filter=Q(estado='pendiente'))
    ).order_by('month')[:6]

    # Procesar datos para los gráficos
    project_status_labels = [item['estado'] for item in project_status_data]
    project_status_values = [item['total'] for item in project_status_data]

    monthly_tasks_months = [item['month'].strftime("%b %Y") for item in monthly_tasks_data]
    monthly_tasks_completed = [item['completadas'] for item in monthly_tasks_data]
    monthly_tasks_pending = [item['pendientes'] for item in monthly_tasks_data]

    context = {
        'active_projects_count': active_projects_count,
        'pending_tasks_count': pending_tasks_count,
        'completion_percentage': completion_percentage,
        'today_tasks_count': today_tasks_count,
        'user_pending_tasks': user_pending_tasks,
        'notifications': notifications,
        'project_status_labels': json.dumps(project_status_labels),
        'project_status_values': json.dumps(project_status_values),
        'monthly_tasks_months': json.dumps(monthly_tasks_months),
        'monthly_tasks_completed': json.dumps(monthly_tasks_completed),
        'monthly_tasks_pending': json.dumps(monthly_tasks_pending),
        'proyectos': proyectos,
        'proyecto_form': proyecto_form,
    }

    return render(request, 'dashboard/home.html',context)

def tareas(request):
    # Obtener todos los proyectos donde el usuario es responsable o integrante (para el dropdown)
    proyectos = Proyecto.objects.filter(
        Q(responsable=request.user) |
        Q(integrantes=request.user)
    ).distinct()

    # Obtener parámetros de filtrado del request
    proyecto_id = request.GET.get('proyecto')
    estado = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')

    # Obtener las tareas del usuario actual
    tareas = Tarea.objects.filter(asignado_a=request.user)

    # Aplicar filtros si existen
    if proyecto_id:
        tareas = tareas.filter(proyecto_id=proyecto_id)
    if estado:
        tareas = tareas.filter(estado=estado)
    if prioridad:
        tareas = tareas.filter(prioridad=prioridad)

    # Obtener los proyectos del usuario para el sidebar (responsable o integrante)
    proyectos_usuario = Proyecto.objects.filter(
        Q(responsable=request.user) |
        Q(integrantes=request.user)
    ).distinct()

    # Preparar el contexto
    context = {
        'proyecto_form': ProyectoForm(),
        'proyectos': proyectos,
        'proyectos_usuario': proyectos_usuario,
        'tareas': tareas,
        'Tarea': Tarea,  # Para acceder a las opciones de estado y prioridad
    }
    return render(request, 'dashboard/tareas.html',context)


class ProyectoListView(LoginRequiredMixin, ListView):
    model = Proyecto
    template_name = 'proyectos/proyecto_list.html'
    context_object_name = 'proyectos'
    paginate_by = 10

    def get_queryset(self):
        # Filtrar proyectos según el rol del usuario
        user = self.request.user
        if user.rol == 'jefe_proyectos':
            return Proyecto.objects.filter(responsable=user) | Proyecto.objects.filter(integrantes=user)
        return Proyecto.objects.filter(integrantes=user)


class ProyectoDetailView(LoginRequiredMixin, DetailView):
    model = Proyecto
    template_name = 'dashboard/proyecto_detail.html'
    context_object_name = 'proyecto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['integrantes'] = self.object.integrantes.all()
        context['proyecto_update_form'] = ProyectoUpdateForm(instance=self.object)
        context['proyecto_form'] = ProyectoForm()


        # Agregar filtro personalizado para el template
        from django.template.defaulttags import register
        @register.filter
        def get_item(dictionary, key):
            return dictionary.get(key, 0)

        return context


class ProyectoCreateView(LoginRequiredMixin, CreateView):
    model = Proyecto
    form_class = ProyectoForm
    template_name = 'proyectos/proyecto_form.html'
    success_url = reverse_lazy('proyecto_list')

    def form_valid(self, form):
        form.instance.estado = 'no_iniciado'
        response = super().form_valid(form)
        messages.success(self.request, 'Proyecto creado exitosamente!')
        return response


def proyecto_roles(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    roles = {}

    # El responsable siempre es jefe de proyectos
    if proyecto.responsable:
        roles[str(proyecto.responsable.id)] = 'jefe_proyectos'

    # Los demás integrantes
    for integrante in proyecto.integrantes.all():
        if str(integrante.id) not in roles:  # No sobrescribir el rol del responsable
            roles[str(integrante.id)] = integrante.rol.lower()  # Convertir a minúsculas para consistencia

    return JsonResponse(roles)

class ProyectoUpdateView(LoginRequiredMixin, UpdateView):
    model = Proyecto
    form_class = ProyectoUpdateForm
    template_name = 'proyectos/proyecto_form.html'
    success_url = reverse_lazy('proyecto_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Proyecto actualizado exitosamente!')
        return response


@login_required
def gestionar_equipo(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Verificar permisos (solo jefe de proyecto o superuser)


    # Formulario para agregar integrantes
    agregar_form = AgregarIntegranteForm(request.POST or None, instance=proyecto)

    # Formulario para remover integrantes
    remover_form = RemoverIntegranteForm(request.POST or None, proyecto=proyecto)

    if request.method == 'POST':
        if 'agregar_integrantes' in request.POST and agregar_form.is_valid():
            nuevos_integrantes = agregar_form.cleaned_data['integrantes']
            proyecto.integrantes.add(*nuevos_integrantes)
            messages.success(request, f'Se agregaron {len(nuevos_integrantes)} integrantes al proyecto.')
            return redirect('gestionar_equipo', proyecto_id=proyecto.id)

        elif 'remover_integrantes' in request.POST and remover_form.is_valid():
            integrantes_a_remover = remover_form.cleaned_data['integrantes']
            count = integrantes_a_remover.count()
            proyecto.integrantes.remove(*integrantes_a_remover)
            messages.success(request, f'Se removieron {count} integrantes del proyecto.')
            return redirect('gestionar_equipo', proyecto_id=proyecto.id)

    # Obtener todos los integrantes con su información
    integrantes = proyecto.integrantes.all().order_by('first_name', 'last_name')
    no_integrantes = Usuario.objects.exclude(
        Q(id__in=proyecto.integrantes.values_list('id', flat=True)) |
        Q(id=proyecto.responsable.id)
    ).order_by('first_name', 'last_name')

    context = {
        'proyecto_form': ProyectoForm(),
        'proyecto': proyecto,
        'agregar_form': agregar_form,
        'remover_form': remover_form,
        'integrantes': integrantes,
        'no_integrantes': no_integrantes,
        'responsable': proyecto.responsable,
    }
    return render(request, 'dashboard/gestionar_equipo.html', context)


@login_required
def eliminar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)

    # Verificar permisos (solo el responsable puede eliminar)
    if request.user != proyecto.responsable and not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para eliminar este proyecto.')
        return redirect('proyecto_list')

    if request.method == 'POST':
        proyecto.delete()
        messages.success(request, 'Proyecto eliminado exitosamente!')
        return redirect('proyecto_list')

    return render(request, 'proyectos/proyecto_confirm_delete.html', {'proyecto': proyecto})





# Vista principal de tareas
@login_required
@require_http_methods(["GET", "POST"])
def lista_tareas_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Verificar permisos
    if not request.user in proyecto.integrantes.all() and not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No tienes permiso para acceder a este proyecto'}, status=403)
        return render(request, '403.html', status=403)

    # Manejar creación de tareas
    if request.method == 'POST' and 'crear_tarea' in request.POST:
        if request.user.rol != 'jefe_proyectos' and request.user != proyecto.responsable:
            messages.error(request, 'No tienes permiso para crear tareas')
            return redirect('lista_tareas_proyecto', proyecto_id=proyecto.id)

        form = TareaForm(request.POST, proyecto=proyecto)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.proyecto = proyecto
            tarea.save()
            messages.success(request, 'Tarea creada correctamente')
            return redirect('lista_tareas_proyecto', proyecto_id=proyecto.id)
        else:
            messages.error(request, 'Error al crear la tarea')

    # Manejar solicitudes AJAX/API
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        tareas = proyecto.tareas.all().order_by('-prioridad', 'fecha_tope')
        data = [{
            'id': t.id,
            'titulo': t.titulo,
            'titulo_corto': t.titulo_corto,
            'descripcion': t.descripcion,
            'estado': t.estado,
            'get_estado_display': t.get_estado_display(),
            'prioridad': t.prioridad,
            'get_prioridad_display': t.get_prioridad_display(),
            'fecha_creacion': t.fecha_creacion.isoformat(),
            'fecha_tope': t.fecha_tope.isoformat() if t.fecha_tope else None,
            'asignado_a': {
                'id': t.asignado_a.id,
                'nombre_completo': str(t.asignado_a)
            } if t.asignado_a else None,
            'proyecto': {
                'id': proyecto.id,
                'nombre': proyecto.nombre
            },
            'documentos': [{
                'id': d.id,
                'nombre': d.nombre,
                'archivo': d.archivo.url if d.archivo else None
            } for d in t.documentos.all()],
            'comentarios': [{
                'id': c.id,
                'contenido': c.contenido,
                'fecha_creacion': c.fecha_creacion.isoformat(),
                'usuario': {
                    'id': c.usuario.id,
                    'nombre_completo': str(c.usuario)
                },
                'archivos': [{
                    'id': a.id,
                    'nombre': a.nombre,
                    'archivo': a.archivo.url if a.archivo else None
                } for a in c.archivos.all()]
            } for c in t.comentarios.all().order_by('fecha_creacion')]
        } for t in tareas]
        return JsonResponse(data, safe=False)

    # Obtener parámetros de filtrado del request
    estado = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')

    # Obtener las tareas del proyecto
    tareas = proyecto.tareas.all()

    # Aplicar filtros si existen
    if estado:
        tareas = tareas.filter(estado=estado)
    if prioridad:
        tareas = tareas.filter(prioridad=prioridad)

    # Obtener proyectos del usuario para el sidebar (responsable o integrante)
    proyectos_usuario = Proyecto.objects.filter(
        Q(responsable=request.user) |
        Q(integrantes=request.user)
    ).distinct()

    # Manejar solicitudes normales (renderizado inicial)
    tarea_form = TareaForm(proyecto=proyecto)

    context = {
        'proyecto_form': ProyectoForm(),
        'proyecto': proyecto,
        'proyecto_actual': proyecto,
        'proyectos_usuario': proyectos_usuario,
        'tareas': tareas.order_by('-prioridad', 'fecha_tope'),
        'tarea_form': tarea_form,
        'Tarea': Tarea,  # Para acceder a las opciones de estado y prioridad
        'prioridades': Tarea.PRIORIDADES,
        'estados_tarea': Tarea.ESTADOS_TAREA,
        'estado_filtro': estado,
        'prioridad_filtro': prioridad,
    }
    return render(request, 'dashboard/tareas.html', context)


# API para crear tarea
@login_required
@require_http_methods(["POST"])
def crear_tarea_api(request):
    try:
        data = json.loads(request.body)
        proyecto_id = data.get('proyecto')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)

    if not proyecto_id:
        return JsonResponse({'error': 'Se requiere el ID del proyecto'}, status=400)

    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Verificar permisos
    if not request.user in proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para crear tareas en este proyecto'}, status=403)

    form = TareaForm(data, proyecto=proyecto)

    if form.is_valid():
        tarea = form.save(commit=False)
        tarea.proyecto = proyecto
        tarea.save()
        return JsonResponse({
            'success': True,
            'id': tarea.id,
            'titulo': tarea.titulo,
            'estado': tarea.estado,
            'get_estado_display': tarea.get_estado_display(),
            'prioridad': tarea.prioridad,
            'get_prioridad_display': tarea.get_prioridad_display(),
        })

    return JsonResponse({'errors': form.errors}, status=400)



# API para detalles de tarea
@login_required
def detalle_tarea_api(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Verificar permisos
    if not request.user in tarea.proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para ver esta tarea'}, status=403)

    data = {
        'id': tarea.id,
        'titulo': tarea.titulo,
        'descripcion': tarea.descripcion,
        'titulo_corto': tarea.titulo_corto,
        'estado': tarea.estado,
        'get_estado_display': tarea.get_estado_display(),
        'prioridad': tarea.prioridad,
        'get_prioridad_display': tarea.get_prioridad_display(),
        'fecha_creacion': tarea.fecha_creacion.isoformat(),
        'fecha_tope': tarea.fecha_tope.isoformat() if tarea.fecha_tope else None,
        'asignado_a': {
            'id': tarea.asignado_a.id,
            'nombre_completo': str(tarea.asignado_a)
        } if tarea.asignado_a else None,
        'proyecto': {
            'id': tarea.proyecto.id,
            'nombre': tarea.proyecto.nombre
        },
        'documentos': [{
            'id': d.id,
            'nombre': d.nombre,
            'archivo': d.archivo.url if d.archivo else None
        } for d in tarea.documentos.all()],
        'comentarios': [{
            'id': c.id,
            'contenido': c.contenido,
            'fecha_creacion': c.fecha_creacion.isoformat(),
            'usuario': {
                'id': c.usuario.id,
                'nombre_completo': str(c.usuario)
            },
            'archivos': [{
                'id': a.id,
                'nombre': a.nombre,
                'archivo': a.archivo.url if a.archivo else None
            } for a in c.archivos.all()]
        } for c in tarea.comentarios.all().order_by('fecha_creacion')]
    }
    return JsonResponse(data)



# API para editar tarea
@login_required
@require_http_methods(["PUT"])
def editar_tarea_api(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Verificar permisos
    if not request.user in tarea.proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para editar esta tarea'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)

    form = TareaForm(data, instance=tarea, proyecto=tarea.proyecto)

    if form.is_valid():
        tarea = form.save()
        return JsonResponse({
            'success': True,
            'id': tarea.id,
            'titulo': tarea.titulo,
            'estado': tarea.estado,
            'get_estado_display': tarea.get_estado_display(),
            'prioridad': tarea.prioridad,
            'get_prioridad_display': tarea.get_prioridad_display(),
        })

    return JsonResponse({'errors': form.errors}, status=400)


# API para eliminar tarea
@login_required
@require_http_methods(["DELETE"])
def eliminar_tarea_api(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Verificar permisos
    if request.user.rol != 'jefe_proyectos' and request.user != tarea.proyecto.responsable:
        return JsonResponse({
            'success': False,
            'error': 'No tienes permiso para eliminar esta tarea'
        }, status=403)

    try:
        tarea.delete()
        return JsonResponse({
            'success': True,
            'message': 'Tarea eliminada correctamente'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Vista para agregar documento
@login_required
@require_POST
def agregar_documento_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Verificar permisos
    if not request.user in tarea.proyecto.integrantes.all() and not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No tienes permiso'}, status=403)
        return render(request, '403.html', status=403)

    form = DocumentoTareaForm(request.POST, request.FILES)

    if form.is_valid():
        documento = form.save(commit=False)
        documento.tarea = tarea
        documento.subido_por = request.user
        documento.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'documento': {
                    'id': documento.id,
                    'nombre': documento.nombre,
                    'archivo': documento.archivo.url if documento.archivo else None
                }
            })

        messages.success(request, 'Documento agregado exitosamente!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'errors': form.errors}, status=400)
        messages.error(request, 'Error al agregar el documento.')

    return redirect('detalle_tarea', tarea_id=tarea.id)


# Vista para agregar comentario
@login_required
@require_POST
def agregar_comentario_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Verificar permisos
    if not request.user in tarea.proyecto.integrantes.all() and not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No tienes permiso'}, status=403)
        return render(request, '403.html', status=403)

    form = ComentarioTareaForm(request.POST)

    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.tarea = tarea
        comentario.usuario = request.user
        comentario.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comentario': {
                    'id': comentario.id,
                    'contenido': comentario.contenido,
                    'fecha_creacion': comentario.fecha_creacion.isoformat(),
                    'usuario': {
                        'id': request.user.id,
                        'nombre_completo': str(request.user)
                    }
                }
            })

        messages.success(request, 'Comentario agregado exitosamente!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'errors': form.errors}, status=400)
        messages.error(request, 'Error al agregar el comentario.')

    return redirect('detalle_tarea', tarea_id=tarea.id)


# Vista para cambiar estado de tarea
@csrf_exempt
@require_POST
def cambiar_estado_tarea(request, task_id):
    try:
        tarea = Tarea.objects.get(id=task_id)
        form = CambiarEstadoTareaForm(
            request.POST,
            instance=tarea,
            usuario=request.user
        )

        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'new_status': tarea.get_estado_display(),
                'status_class': f'status-{tarea.estado}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se puede revertir a (En Progreso) desde (Completada)',
                'errors': form.errors
            }, status=400)

    except Tarea.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tarea no encontrada'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



@login_required
def meeting_chat(request):
    proyecto_form = ProyectoForm()
    if request.method == 'POST':
        form = MeetingCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user

            # Si es un enlace de meet, validamos el formato
            if comment.is_meeting_link:
                if not comment.meeting_url or 'meet.google.com' not in comment.meeting_url:
                    messages.error(request, 'Por favor ingresa un enlace válido de Google Meet')
                    return redirect('meeting_chat')

            comment.save()
            messages.success(request, 'Comentario publicado')
            return redirect('meeting_chat')
    else:
        form = MeetingCommentForm()

    comments = MeetingComment.objects.all().order_by('-created_at')
    return render(request, 'dashboard/meeting_chat.html', {
        'form': form,
        'comments': comments,
        'proyecto_form': proyecto_form,
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Proyecto, Tarea
from .forms import ProyectoForm


@login_required
def personal_dashboard(request):
    # Obtener todos los proyectos donde el usuario es responsable o integrante (para el dropdown)
    proyectos = Proyecto.objects.filter(
        Q(responsable=request.user) |
        Q(integrantes=request.user)
    ).distinct()

    # Obtener parámetros de filtrado del request
    proyecto_id = request.GET.get('proyecto')
    estado = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')

    # Obtener las tareas del usuario actual
    tareas = Tarea.objects.filter(asignado_a=request.user)

    # Aplicar filtros si existen
    if proyecto_id:
        tareas = tareas.filter(proyecto_id=proyecto_id)
    if estado:
        tareas = tareas.filter(estado=estado)
    if prioridad:
        tareas = tareas.filter(prioridad=prioridad)

    # Obtener los proyectos del usuario para el sidebar (responsable o integrante)
    proyectos_usuario = Proyecto.objects.filter(
        Q(responsable=request.user) |
        Q(integrantes=request.user)
    ).distinct()

    # Preparar el contexto
    context = {
        'proyecto_form': ProyectoForm(),
        'proyectos': proyectos,
        'proyectos_usuario': proyectos_usuario,
        'tareas': tareas,
        'Tarea': Tarea,  # Para acceder a las opciones de estado y prioridad
    }

    return render(request, 'dashboard/personal_dashboard.html', context)



@login_required
def get_user_tasks(request):
    # Obtener tareas del usuario actual (asignadas o donde es responsable)
    tareas = Tarea.objects.filter(
        asignado_a=request.user
    ).select_related('proyecto').order_by('-fecha_creacion')

    # Serializar los datos
    tareas_data = []
    for tarea in tareas:
        tareas_data.append({
            "id": tarea.id,
            "titulo": tarea.titulo,
            "descripcion": tarea.descripcion or "",
            "estado": tarea.estado,
            "get_estado_display": tarea.get_estado_display(),
            "prioridad": tarea.prioridad,
            "get_prioridad_display": tarea.get_prioridad_display(),
            "fecha_creacion": tarea.fecha_creacion.strftime("%Y-%m-%d") if tarea.fecha_creacion else None,
            "fecha_tope": tarea.fecha_tope.strftime("%Y-%m-%d") if tarea.fecha_tope else None,
            "proyecto": {
                "id": tarea.proyecto.id,
                "nombre": tarea.proyecto.nombre,
            },
        })

    return JsonResponse(tareas_data, safe=False)



# Seccion de vistas para los bugs del proyecto
@login_required
@require_http_methods(["GET", "POST"])
def lista_bugs_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Verificar permisos
    if not request.user in proyecto.integrantes.all() and not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No tienes permiso para acceder a este proyecto'}, status=403)
        return render(request, '403.html', status=403)

    # Manejar solicitudes AJAX/API
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        bugs = proyecto.bugs.all().order_by('-prioridad', 'fecha_tope')
        data = [{
            'id': b.id,
            'titulo': b.titulo,
            'descripcion': b.descripcion,
            'pasos_reproducir': b.pasos_reproducir,
            'estado': b.estado,
            'get_estado_display': b.get_estado_display(),
            'prioridad': b.prioridad,
            'get_prioridad_display': b.get_prioridad_display(),
            'tipo': b.tipo,
            'get_tipo_display': b.get_tipo_display(),
            'fecha_creacion': b.fecha_creacion.isoformat(),
            'fecha_tope': b.fecha_tope.isoformat() if b.fecha_tope else None,
            'reportado_por': {
                'id': b.reportado_por.id,
                'nombre_completo': str(b.reportado_por)
            } if b.reportado_por else None,
            'asignado_a': {
                'id': b.asignado_a.id,
                'nombre_completo': str(b.asignado_a)
            } if b.asignado_a else None,
            'proyecto': {
                'id': proyecto.id,
                'nombre': proyecto.nombre
            },
        } for b in bugs]
        return JsonResponse(data, safe=False)

    # Manejar solicitudes normales (renderizado inicial)
    bug_form = BugForm(proyecto=proyecto)

    context = {
        'proyecto_form': ProyectoForm(),
        'proyecto': proyecto,
        'proyecto_actual': proyecto,
        'bug_form': BugForm(proyecto=proyecto),
        'prioridades': list(Bug.PRIORIDADES_BUG),
        'estados_bug': list(Bug.ESTADOS_BUG),
        'tipos_bug': list(Bug.TIPOS_BUG),
    }
    return render(request, 'dashboard/bugs.html', context)

@login_required
@require_http_methods(["POST"])
def crear_bug_api(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Verificar permisos
    if not request.user in proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para reportar bugs en este proyecto'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)

    form = BugForm(data, proyecto=proyecto)

    if form.is_valid():
        bug = form.save(commit=False)
        bug.proyecto = proyecto
        bug.reportado_por = request.user  # Asignar automáticamente el usuario actual
        bug.save()
        return JsonResponse({
            'success': True,
            'id': bug.id,
            'titulo': bug.titulo,
            'estado': bug.estado,
            'get_estado_display': bug.get_estado_display(),
            'prioridad': bug.prioridad,
            'get_prioridad_display': bug.get_prioridad_display(),
            'tipo': bug.tipo,
            'get_tipo_display': bug.get_tipo_display(),
        })

    return JsonResponse({'errors': form.errors}, status=400)

@login_required
def detalle_bug_api(request, bug_id):
    bug = get_object_or_404(Bug, id=bug_id)

    # Verificar permisos
    if not request.user in bug.proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para ver este bug'}, status=403)

    data = {
        'id': bug.id,
        'titulo': bug.titulo,
        'descripcion': bug.descripcion,
        'pasos_reproducir': bug.pasos_reproducir,
        'estado': bug.estado,
        'get_estado_display': bug.get_estado_display(),
        'prioridad': bug.prioridad,
        'get_prioridad_display': bug.get_prioridad_display(),
        'tipo': bug.tipo,
        'get_tipo_display': bug.get_tipo_display(),
        'fecha_creacion': bug.fecha_creacion.isoformat(),
        'fecha_tope': bug.fecha_tope.isoformat() if bug.fecha_tope else None,
        'reportado_por': {
            'id': bug.reportado_por.id,
            'nombre_completo': str(bug.reportado_por)
        } if bug.reportado_por else None,
        'asignado_a': {
            'id': bug.asignado_a.id,
            'nombre_completo': str(bug.asignado_a)
        } if bug.asignado_a else None,
        'proyecto': {
            'id': bug.proyecto.id,
            'nombre': bug.proyecto.nombre
        },

    }
    return JsonResponse(data)

@login_required
@require_http_methods(["PUT"])
def editar_bug_api(request, bug_id):
    bug = get_object_or_404(Bug, id=bug_id)

    # Verificar permisos
    if not request.user in bug.proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para editar este bug'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)

    form = BugForm(data, instance=bug, proyecto=bug.proyecto)

    if form.is_valid():
        bug = form.save()
        return JsonResponse({
            'success': True,
            'id': bug.id,
            'titulo': bug.titulo,
            'estado': bug.estado,
            'get_estado_display': bug.get_estado_display(),
            'prioridad': bug.prioridad,
            'get_prioridad_display': bug.get_prioridad_display(),
            'tipo': bug.tipo,
            'get_tipo_display': bug.get_tipo_display(),
        })

    return JsonResponse({'errors': form.errors}, status=400)

@login_required
@require_POST
def cambiar_estado_bug(request, bug_id):
    bug = get_object_or_404(Bug, id=bug_id)

    # Verificar permisos
    if not request.user in bug.proyecto.integrantes.all() and not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No tienes permiso'}, status=403)
        return render(request, '403.html', status=403)

    form = CambiarEstadoBugForm(request.POST, instance=bug, usuario=request.user)

    if form.is_valid():
        bug = form.save(commit=False)

        if bug.estado == 'resuelto':
            bug.resuelto_por = request.user
            bug.fecha_resuelto = timezone.now()
        elif bug.estado == 'verificado':
            bug.verificado_por = request.user
            bug.fecha_verificacion = timezone.now()

        bug.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'estado': bug.estado,
                'get_estado_display': bug.get_estado_display()
            })

        messages.success(request, 'Estado del bug actualizado exitosamente!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'errors': form.errors}, status=400)
        messages.error(request, 'Error al actualizar el estado del bug.')

    return redirect('detalle_bug', bug_id=bug.id)

@login_required
@require_http_methods(["DELETE"])
def eliminar_bug_api(request, bug_id):
    bug = get_object_or_404(Bug, id=bug_id)

    # Verificar permisos
    if not request.user in bug.proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para eliminar este bug'}, status=403)

    bug.delete()
    return JsonResponse({'success': True})


@login_required
def documentos_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Verificar permisos
    if not request.user in proyecto.integrantes.all() and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    documentos = proyecto.documentos_proyecto.all().order_by('-fecha_subido')
    form = DocumentoForm(proyecto=proyecto, usuario=request.user)

    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, proyecto=proyecto, usuario=request.user)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.subido_por = request.user
            documento.proyecto = proyecto
            documento.save()
            messages.success(request, 'Documento subido correctamente!')
            return JsonResponse({'success': True, 'redirect_url': f'/proyecto/{proyecto.id}/documentos/'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    context = {
        'proyecto_form': ProyectoForm(),
        'proyecto': proyecto,
        'documentos': documentos,
        'form': form,
        'tipos_documento': Documento.TIPOS_DOCUMENTO,
    }
    return render(request, 'dashboard/documentos.html', context)

@login_required
def descargar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)

    # Verificar permisos
    if not request.user in documento.proyecto.integrantes.all() and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    response = FileResponse(documento.archivo.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{documento.archivo.name.split("/")[-1]}"'
    return response

@login_required
@require_http_methods(["DELETE"])
def eliminar_documento_api(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)

    # Verificar permisos (solo jefes de proyecto o el que subió el documento)
    if not (request.user == documento.subido_por or
            request.user == documento.proyecto.jefe_proyecto or
            request.user.is_superuser):
        return JsonResponse({'error': 'No tienes permiso para eliminar este documento'}, status=403)

    try:
        documento.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.http import FileResponse, HttpResponseForbidden
import mimetypes


@login_required
def ver_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)

    # Verificar permisos
    if not request.user in documento.proyecto.integrantes.all() and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para ver este documento")

    # Abrir el archivo en modo binario
    file = documento.archivo.open('rb')

    # Determinar el tipo MIME
    content_type, _ = mimetypes.guess_type(documento.archivo.name)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(file, content_type=content_type)

    # Configurar para visualización en el navegador cuando sea posible
    if content_type in ['application/pdf', 'image/jpeg', 'image/png', 'text/plain']:
        response['Content-Disposition'] = f'inline; filename="{documento.archivo.name.split("/")[-1]}"'
    else:
        # Forzar descarga para tipos no visualizables
        response['Content-Disposition'] = f'attachment; filename="{documento.archivo.name.split("/")[-1]}"'

    return response


# En tu views.py, añade esta vista para la API
@login_required
def documento_api(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)

    # Verificar permisos
    if not request.user in documento.proyecto.integrantes.all() and not request.user.is_superuser:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    data = {
        'id': documento.id,
        'nombre': documento.nombre,
        'tipo': documento.tipo,
        'get_tipo_display': documento.get_tipo_display(),
        'archivo': {
            'name': documento.archivo.name,
            'size': documento.archivo.size,
            'url': documento.archivo.url
        },
        'subido_por': {
            'get_full_name': documento.subido_por.get_full_name()
        },
        'fecha_subido': documento.fecha_subido.isoformat(),
        'can_delete': request.user == documento.subido_por or request.user == documento.proyecto.jefe_proyecto or request.user.is_superuser
    }
    return JsonResponse(data)