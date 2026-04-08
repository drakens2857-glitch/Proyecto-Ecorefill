# apps/tasks/urls.py
from django.urls import path
from .views import (
    TaskListCreateView,
    TaskDetailView,
    AllTasksView,
    ia_chat_endpoint,
    EstadisticasView
)

urlpatterns = [
    # 📊 ESTADÍSTICAS (PRIMERO)
    path('estadisticas/', EstadisticasView.as_view(), name='estadisticas'),

    # 📋 LISTAR Y CREAR
    path('', TaskListCreateView.as_view(), name='tasks-list-create'),

    # 👑 ADMIN
    path('all/', AllTasksView.as_view(), name='all-tasks'),

    # 🤖 IA
    path('ia/chat/', ia_chat_endpoint, name='ia_chat'),

    # 🔍 DETALLE (SIEMPRE DE ÚLTIMO)
    path('<str:task_id>/', TaskDetailView.as_view(), name='task-detail'),
]
