from django.urls import path, include
from django.views.generic import TemplateView
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# IMPORTS
from apps.tasks.views import ia_chat_endpoint
from apps.tasks.views_chat import ChatHistorialApiView  # 🔥 ESTE FALTABA

def firebase_status(request):
    from firebase_utils import get_firebase_status
    status = get_firebase_status()
    return JsonResponse(status)

urlpatterns = [
    # Frontend y Documentación
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/status/', firebase_status, name='firebase-status'),

    # Endpoints de las Apps
    path('api/users/', include('apps.users.urls')),
    path('api/tasks/', include('apps.tasks.urls')),

    # Chat IA
    path('api/ia/chat/', ia_chat_endpoint, name='chat_ia'),

    # Historial chat
    path('api/chat/historial/', ChatHistorialApiView.as_view(), name='chat_historial'),
]
