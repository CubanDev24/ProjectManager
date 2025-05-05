from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    tareas,
    crear_usuario,
    ProyectoListView,
    ProyectoDetailView,
    ProyectoCreateView,
    ProyectoUpdateView,
    eliminar_proyecto,
    meeting_chat,
    personal_dashboard,
    get_user_tasks,
    landing_page,
    info_page
)
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', landing_page, name='landing'),
    path('info/', info_page, name='info'),
    path('home/', home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name ='usuarios/login2.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registro/', views.registro, name='registro'),
    path('actualizar-perfil/', views.actualizar_perfil, name='actualizar_perfil'),
    path('proyectos/lista', ProyectoListView.as_view(), name='proyecto_list'),
    path('crear/', ProyectoCreateView.as_view(), name='proyecto_create'),
    path('proyecto/<int:pk>/', ProyectoDetailView.as_view(), name='proyecto_detail'),
    path('<int:pk>/editar/', ProyectoUpdateView.as_view(), name='proyecto_update'),
    path('proyectos/<int:proyecto_id>/equipo/', views.gestionar_equipo, name='gestionar_equipo'),
    path('<int:pk>/eliminar/', eliminar_proyecto, name='proyecto_delete'),
    path('tareas/', tareas, name='tareas'),
    # Lista de tareas de un proyecto


    # Documentos y comentarios (tradicional)
    path('tarea/<int:tarea_id>/agregar-documento/', views.agregar_documento_tarea, name='agregar_documento_tarea'),
    path('tarea/<int:tarea_id>/agregar-comentario/', views.agregar_comentario_tarea, name='agregar_comentario_tarea'),

    # Cambiar estado (tradicional)
    path('tarea/<int:tarea_id>/cambiar-estado/', views.cambiar_estado_tarea, name='cambiar_estado_tarea'),

    # API Endpoints
    path('api/proyecto/<int:proyecto_id>/roles/', views.proyecto_roles, name='proyecto_roles'),

    path('api/proyecto/<int:proyecto_id>/tareas/', views.lista_tareas_proyecto, name='api_tareas_proyecto'),
    path('api/tarea/', views.crear_tarea_api, name='api_crear_tarea'),
    path('api/tarea/<int:tarea_id>/', views.detalle_tarea_api, name='api_detalle_tarea'),
    path('api/tarea/<int:tarea_id>/editar/', views.editar_tarea_api, name='api_editar_tarea'),
    path('api/tarea/<int:tarea_id>/eliminar/', views.eliminar_tarea_api, name='api_eliminar_tarea'),
    path('api/tarea/<int:tarea_id>/comentarios/', views.agregar_comentario_tarea, name='api_agregar_comentario'),
    path('api/tarea/<int:task_id>/cambiar-estado/', views.cambiar_estado_tarea, name='api_cambiar_estado'),
    path('meeting-chat/', meeting_chat, name='meeting_chat'),
    path('personal_dashboard/', personal_dashboard, name='personal_dashboard'),
    path('get_user_tasks/', get_user_tasks, name='get_user_tasks'),

    # seccion de rutas para los bugs
    path('proyectos/<int:proyecto_id>/bugs/', views.lista_bugs_proyecto, name='lista_bugs_proyecto'),
    path('api/bugs/crear/<int:proyecto_id>/', views.crear_bug_api, name='crear_bug_api'),
    path('api/bugs/<int:bug_id>/', views.detalle_bug_api, name='detalle_bug_api'),
    path('api/bugs/editar/<int:bug_id>/', views.editar_bug_api, name='editar_bug_api'),
    path('api/bugs/estado/<int:bug_id>/', views.cambiar_estado_bug, name='cambiar_estado_bug'),
    path('api/bugs/eliminar/<int:bug_id>/', views.eliminar_bug_api, name='eliminar_bug_api'),

    # seccion para las rutas de los documentos
path('proyecto/<int:proyecto_id>/documentos/', views.documentos_proyecto, name='documentos_proyecto'),
path('documentos/<int:documento_id>/descargar/', views.descargar_documento, name='descargar_documento'),
path('api/documentos/<int:documento_id>/eliminar/', views.eliminar_documento_api, name='eliminar_documento_api'),
path('documentos/<int:documento_id>/ver/', views.ver_documento, name='ver_documento'),
path('api/documentos/<int:documento_id>/', views.documento_api, name='documento_api'),

]



