from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer
from firebase_utils import get_firestore_client, get_user_from_token, is_admin


class TaskListCreateView(APIView):
    @extend_schema(
        summary="Listar mis tareas",
        description="Trabajador: ve sus tareas. Administrador: ve todas las tareas del sistema.",
        tags=["Tareas"]
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

        if is_admin(uid):
            tasks_query = db.collection('tasks').order_by('fecha_creacion', direction='DESCENDING').stream()
        else:
            tasks_query = db.collection('tasks').where('creado_por_uid', '==', uid).stream()

        tasks = [t.to_dict() | {'id': t.id} for t in tasks_query]
        return Response({'total': len(tasks), 'tareas': tasks})

    @extend_schema(
        request=TaskCreateSerializer,
        summary="Crear tarea/solicitud",
        description="Crea una nueva tarea o solicitud de recarga en el sistema.",
        tags=["Tareas"]
    )
    def post(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido o no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        try:
            db = get_firestore_client()
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        serializer = TaskCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_doc = db.collection('users').document(uid).get()
        user_nombre = user_doc.to_dict().get('nombre', 'Desconocido') if user_doc.exists else 'Desconocido'

        now = datetime.now(timezone.utc).isoformat()
        task_data = {
            **serializer.validated_data,
            'creado_por_uid': uid,
            'creado_por_nombre': user_nombre,
            'fecha_creacion': now,
            'fecha_actualizacion': now
        }

        doc_ref = db.collection('tasks').document()
        doc_ref.set(task_data)

        return Response(
            {'message': 'Tarea creada exitosamente.', 'id': doc_ref.id, **task_data},
            status=status.HTTP_201_CREATED
        )


class TaskDetailView(APIView):
    def _get_task_and_check(self, request, task_id):
        token_data = get_user_from_token(request)
        if not token_data:
            return None, None, Response({'error': 'Token inválido o no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        try:
            db = get_firestore_client()
        except RuntimeError as e:
            return None, None, Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()

        if not task_doc.exists:
            return None, None, Response({'error': 'Tarea no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        task_data = task_doc.to_dict()
        admin = is_admin(uid)

        if not admin and task_data.get('creado_por_uid') != uid:
            return None, None, Response({'error': 'No tienes permisos para acceder a esta tarea.'}, status=status.HTTP_403_FORBIDDEN)

        return uid, task_ref, None

    @extend_schema(
        summary="Ver detalle de tarea",
        description="Obtiene el detalle de una tarea específica.",
        tags=["Tareas"]
    )
    def get(self, request, task_id):
        uid, task_ref, err = self._get_task_and_check(request, task_id)
        if err:
            return err
        task_doc = task_ref.get()
        return Response(task_doc.to_dict() | {'id': task_ref.id})

    @extend_schema(
        request=TaskUpdateSerializer,
        summary="Actualizar tarea",
        description="Actualiza los datos de una tarea existente.",
        tags=["Tareas"]
    )
    def patch(self, request, task_id):
        uid, task_ref, err = self._get_task_and_check(request, task_id)
        if err:
            return err

        serializer = TaskUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        update_data = {k: v for k, v in serializer.validated_data.items()}
        if not update_data:
            return Response({'error': 'No hay datos para actualizar.'}, status=status.HTTP_400_BAD_REQUEST)

        update_data['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
        task_ref.update(update_data)

        return Response({'message': 'Tarea actualizada correctamente.', 'id': task_id, 'cambios': update_data})

    @extend_schema(
        summary="Eliminar tarea",
        description="Elimina una tarea del sistema.",
        tags=["Tareas"]
    )
    def delete(self, request, task_id):
        uid, task_ref, err = self._get_task_and_check(request, task_id)
        if err:
            return err

        task_ref.delete()
        return Response({'message': 'Tarea eliminada correctamente.', 'id': task_id})


class AllTasksView(APIView):
    @extend_schema(
        summary="Ver todas las tareas (Admin)",
        description="Solo administradores. Retorna todas las tareas del sistema.",
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

        tasks_query = db.collection('tasks').stream()
        tasks = [t.to_dict() | {'id': t.id} for t in tasks_query]

        return Response({'total': len(tasks), 'tareas': tasks})
