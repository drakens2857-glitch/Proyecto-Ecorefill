import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore, auth
from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_app = None
_init_tried = False
_init_error = None


def get_firebase_app():
    global _firebase_app, _init_tried, _init_error

    if _init_tried and _firebase_app is not None:
        return _firebase_app

    _init_tried = True

    # Opción 1: archivo JSON local (para correr en computadora)
    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    if not cred_path:
        cred_path = 'serviceAccountKey.json'

    if os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            print(f"[Firebase] ✅ Conectado via archivo: {cred_path}")
            _init_error = None
            return _firebase_app
        except Exception as e:
            _init_error = str(e)
            print(f"[Firebase] ❌ Error al cargar archivo '{cred_path}': {e}")

    # Opción 2: variable de entorno (para Replit / producción)
    raw = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
    if raw:
        print(f"[Firebase] JSON encontrado, longitud: {len(raw)} chars, inicio: {raw[:30]!r}")
        try:
            cred_dict = json.loads(raw)
            required = ['type', 'project_id', 'private_key', 'client_email']
            missing = [k for k in required if k not in cred_dict]
            if missing:
                _init_error = f"JSON incompleto, faltan campos: {missing}"
                print(f"[Firebase] ❌ {_init_error}")
            else:
                if not firebase_admin._apps:
                    cred = credentials.Certificate(cred_dict)
                    _firebase_app = firebase_admin.initialize_app(cred)
                else:
                    _firebase_app = firebase_admin.get_app()
                print(f"[Firebase] ✅ Conectado al proyecto: {cred_dict.get('project_id')}")
                _init_error = None
                return _firebase_app
        except json.JSONDecodeError as e:
            _init_error = f"JSON inválido: {e}. Contenido inicia con: {raw[:80]!r}"
            print(f"[Firebase] ❌ {_init_error}")
        except Exception as e:
            _init_error = str(e)
            print(f"[Firebase] ❌ Error al inicializar: {e}")
    else:
        if not _init_error:
            _init_error = (
                "No se encontraron credenciales de Firebase.\n"
                "  ▶ Local: coloca 'serviceAccountKey.json' en la carpeta eco_refill/\n"
                "  ▶ Replit: configura el secret FIREBASE_SERVICE_ACCOUNT_JSON"
            )
            print(f"[Firebase] ❌ {_init_error}")

    return None


def get_firebase_status():
    app = get_firebase_app()
    return {
        'connected': app is not None,
        'error': _init_error
    }


def get_firestore_client():
    app = get_firebase_app()
    if app is None:
        raise RuntimeError(_init_error or "Firebase no está configurado.")
    return firestore.client()


def verify_firebase_token(id_token):
    app = get_firebase_app()
    if app is None:
        raise RuntimeError(_init_error or "Firebase no está configurado.")
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception:
        return None


def get_user_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    return verify_firebase_token(token)


def is_admin(uid):
    try:
        db = get_firestore_client()
        user_ref = db.collection('users').document(uid)
        doc = user_ref.get()
        if doc.exists:
            return doc.to_dict().get('rol') == 'administrador'
        return False
    except Exception:
        return False
