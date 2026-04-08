import os
import django

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Configurar settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Inicializar Django
django.setup()

# Importar routing DESPUÉS de setup
import apps.tasks.routing

# App HTTP
django_asgi_app = get_asgi_application()

# Configuración final
application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.tasks.routing.websocket_urlpatterns
        )
    ),
})
