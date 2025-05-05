from django.contrib import admin
from .models import Usuario, Proyecto, Tarea, Bug, Documento, MeetingComment

# Register your models here.
admin.site.register(Usuario)
admin.site.register(Proyecto)
admin.site.register(Tarea)
admin.site.register(Bug)
admin.site.register(Documento)
admin.site.register(MeetingComment)
