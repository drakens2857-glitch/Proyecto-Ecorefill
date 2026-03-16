from django.urls import path
from .views import TaskListCreateView, TaskDetailView, AllTasksView

urlpatterns = [
    path('', TaskListCreateView.as_view(), name='tasks-list-create'),
    path('all/', AllTasksView.as_view(), name='all-tasks'),
    path('<str:task_id>/', TaskDetailView.as_view(), name='task-detail'),
]
