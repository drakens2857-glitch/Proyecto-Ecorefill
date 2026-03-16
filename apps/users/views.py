import requests
import cloudinary
import cloudinary.uploader
from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from django.conf import settings

from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer, UpdateUserSerializer
from firebase_utils import get_firestore_client, verify_firebase_token, get_user_from_token, is_admin
import firebase_admin
from firebase_admin import auth as firebase_auth


def setup_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=RegisterSerializer,
        summary="Registrar usuario",
        description="Registra un nuevo usuario en Firebase Auth y Firestore.",
        tags=["Usuarios"]
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        email = data['email']
        password = data['password']
        nombre = data['nombre']
        rol = data['rol']

        try:
            db = get_firestore_client()
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            user_record = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=nombre
            )
            uid = user_record.uid

            user_data = {
                'uid': uid,
                'email': email,
                'nombre': nombre,
                'rol': rol,
                'foto_url': '',
                'fecha_registro': datetime.now(timezone.utc).isoformat()
            }
            db.collection('users').document(uid).set(user_data)

            return Response(
                {'message': 'Usuario registrado exitosamente.', 'uid': uid, 'email': email, 'nombre': nombre, 'rol': rol},
                status=status.HTTP_201_CREATED
            )
        except firebase_admin._auth_utils.EmailAlreadyExistsError:
            return Response({'error': 'Ya existe una cuenta con este correo.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=LoginSerializer,
        summary="Iniciar sesión",
        description="Inicia sesión con email y contraseña usando Firebase Auth REST API.",
        tags=["Usuarios"]
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        api_key = settings.FIREBASE_WEB_API_KEY

        if not api_key:
            return Response(
                {'error': 'FIREBASE_WEB_API_KEY no configurada.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}'
        payload = {
            'email': data['email'],
            'password': data['password'],
            'returnSecureToken': True
        }

        try:
            resp = requests.post(url, json=payload)
            resp_data = resp.json()

            if resp.status_code != 200:
                msg = resp_data.get('error', {}).get('message', 'Error de autenticación')
                return Response({'error': msg}, status=status.HTTP_401_UNAUTHORIZED)

            id_token = resp_data.get('idToken')
            uid = resp_data.get('localId')
            refresh_token = resp_data.get('refreshToken')

            try:
                db = get_firestore_client()
                user_doc = db.collection('users').document(uid).get()
                user_info = user_doc.to_dict() if user_doc.exists else {}
            except Exception:
                user_info = {}

            return Response({
                'message': 'Sesión iniciada correctamente.',
                'idToken': id_token,
                'token': id_token,
                'refreshToken': refresh_token,
                'uid': uid,
                'email': data['email'],
                'nombre': user_info.get('nombre', ''),
                'rol': user_info.get('rol', 'trabajador'),
                'foto_url': user_info.get('foto_url', '')
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(APIView):
    @extend_schema(
        summary="Ver mi perfil",
        description="Retorna el perfil del usuario autenticado incluyendo sus tareas.",
        tags=["Usuarios"]
    )
    def get(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido o no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        try:
            db = get_firestore_client()
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        user_data = user_doc.to_dict()
        tasks_query = db.collection('tasks').where('creado_por_uid', '==', uid).stream()
        tasks = [t.to_dict() | {'id': t.id} for t in tasks_query]

        return Response({
            'perfil': user_data,
            'total_tareas': len(tasks),
            'tareas': tasks
        })


class UploadPhotoView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Subir foto de perfil",
        description="Sube una imagen a Cloudinary y guarda la URL en el perfil del usuario.",
        tags=["Usuarios"]
    )
    def post(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido o no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        file = request.FILES.get('foto')
        if not file:
            return Response({'error': 'No se envió ninguna imagen.'}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.CLOUDINARY_CLOUD_NAME:
            return Response({'error': 'Cloudinary no está configurado.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            setup_cloudinary()
            result = cloudinary.uploader.upload(
                file,
                folder='eco_refill/perfiles',
                public_id=f'user_{uid}',
                overwrite=True,
                resource_type='image',
                transformation=[
                    {'width': 300, 'height': 300, 'crop': 'fill', 'gravity': 'face'}
                ]
            )
            foto_url = result.get('secure_url', '')

            db = get_firestore_client()
            db.collection('users').document(uid).update({'foto_url': foto_url})

            return Response({'message': 'Foto subida correctamente.', 'foto_url': foto_url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AllUsersView(APIView):
    @extend_schema(
        summary="Ver todos los usuarios (Admin)",
        description="Solo accesible para administradores. Retorna todos los perfiles de trabajadores.",
        tags=["Administrador"]
    )
    def get(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido o no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        try:
            db = get_firestore_client()
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not is_admin(uid):
            return Response({'error': 'Acceso denegado. Solo administradores.'}, status=status.HTTP_403_FORBIDDEN)

        users_query = db.collection('users').stream()
        users = [u.to_dict() for u in users_query]

        return Response({'total': len(users), 'usuarios': users})


class UpdateUserView(APIView):
    @extend_schema(
        request=UpdateUserSerializer,
        summary="Actualizar usuario (Admin)",
        description="Permite al administrador actualizar el rol o nombre de un usuario.",
        tags=["Administrador"]
    )
    def patch(self, request, uid):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido o no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        requester_uid = token_data['uid']
        try:
            db = get_firestore_client()
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not is_admin(requester_uid):
            return Response({'error': 'Acceso denegado. Solo administradores.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UpdateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        update_data = {k: v for k, v in serializer.validated_data.items()}
        if not update_data:
            return Response({'error': 'No hay datos para actualizar.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            db.collection('users').document(uid).update(update_data)
            return Response({'message': 'Usuario actualizado correctamente.', 'uid': uid, 'cambios': update_data})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteUserView(APIView):
    @extend_schema(
        summary="Eliminar usuario (Admin)",
        description="Permite al administrador eliminar un usuario del sistema.",
        tags=["Administrador"]
    )
    def delete(self, request, uid):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido o no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        requester_uid = token_data['uid']
        try:
            db = get_firestore_client()
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not is_admin(requester_uid):
            return Response({'error': 'Acceso denegado. Solo administradores.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            firebase_auth.delete_user(uid)
            db.collection('users').document(uid).delete()
            tasks_query = db.collection('tasks').where('creado_por_uid', '==', uid).stream()
            for task in tasks_query:
                task.reference.delete()
            return Response({'message': f'Usuario {uid} eliminado correctamente.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
