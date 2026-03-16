from django.urls import path, include
from django.views.generic import TemplateView
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
import ia_service  # Importamos tu archivo de la raíz

def firebase_status(request):
    from firebase_utils import get_firebase_status
    status = get_firebase_status()
    return JsonResponse(status)

urlpatterns = [
    
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/status/', firebase_status, name='firebase-status'),

    # Apps
    path('api/users/', include('apps.users.urls')),
    path('api/tasks/', include('apps.tasks.urls')),

    # Chat IA - CORREGIDO
    path('api/ia/chat/', ia_service.chat_con_ia, name='chat_ia'),
]
