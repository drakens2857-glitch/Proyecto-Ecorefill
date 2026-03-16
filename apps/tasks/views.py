from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer
from firebase_utils import get_firestore_client, get_user_from_token, is_admin

class TaskListCreateView(APIView):
    @extend_schema(summary="Listar mis tareas", tags=["Tareas"])
    def get(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        db = get_firestore_client()

        # Si es Admin, traemos todo de 'tasks' y 'tareas'
        if is_admin(uid):
            tasks_manual = db.collection('tasks').order_by('fecha_creacion', direction='DESCENDING').stream()
            tasks_ia = db.collection('tareas').stream()
            all_docs = list(tasks_manual) + list(tasks_ia)
        else:
            # BUSQUEDA HÍBRIDA: Buscamos por los dos nombres de campo posibles
            # 1. Buscar en 'tasks' con nombre de campo manual
            q1 = db.collection('tasks').where('creado_por_uid', '==', uid).stream()
            # 2. Buscar en 'tasks' con nombre de campo de la IA
            q2 = db.collection('tasks').where('usuario_id', '==', uid).stream()
            # 3. Buscar en la colección 'tareas' (donde la IA guardó antes)
            q3 = db.collection('tareas').where('usuario_id', '==', uid).stream()
            
            all_docs = list(q1) + list(q2) + list(q3)

        # Usamos un diccionario para evitar tareas duplicadas por ID
        tasks_dict = {}
        for t in all_docs:
            data = t.to_dict()
            data['id'] = t.id
            tasks_dict[t.id] = data

        # El Serializer unificará 'usuario_id' -> 'creado_por_uid' antes de enviar
        serializer = TaskSerializer(list(tasks_dict.values()), many=True)
        return Response({'total': len(tasks_dict), 'tareas': serializer.data})

    @extend_schema(request=TaskCreateSerializer, summary="Crear tarea", tags=["Tareas"])
    def post(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'No autorizado.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        db = get_firestore_client()
        serializer = TaskCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            user_doc = db.collection('users').document(uid).get()
            user_nombre = user_doc.to_dict().get('nombre', 'Frankin villalba') if user_doc.exists else 'Frankin villalba'
            
            now = datetime.now(timezone.utc).isoformat()
            task_data = {
                **serializer.validated_data,
                'creado_por_uid': uid, # Guardamos siempre con el nombre correcto
                'creado_por_nombre': user_nombre,
                'fecha_creacion': now,
                'fecha_actualizacion': now
            }
            # Guardamos siempre en 'tasks' para mantener el orden
            doc_ref = db.collection('tasks').document()
            doc_ref.set(task_data)
            return Response({'id': doc_ref.id, **task_data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class TaskDetailView(APIView):
    def _get_task_ref(self, uid, task_id):
        db = get_firestore_client()
        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()
        if not task_doc.exists:
            return None, Response({'error': 'No existe'}, status=status.HTTP_404_NOT_FOUND)
        
        data = task_doc.to_dict()
        if not is_admin(uid) and data.get('creado_por_uid') != uid:
            return None, Response({'error': 'Sin permiso'}, status=status.HTTP_403_FORBIDDEN)
        return task_ref, None

    def get(self, request, task_id):
        token_data = get_user_from_token(request)
        task_ref, error_res = self._get_task_ref(token_data['uid'], task_id)
        if error_res: return error_res
        
        task_data = task_ref.get().to_dict() | {'id': task_id}
        serializer = TaskSerializer(task_data)
        return Response(serializer.data)

    def patch(self, request, task_id):
        token_data = get_user_from_token(request)
        task_ref, error_res = self._get_task_ref(token_data['uid'], task_id)
        if error_res: return error_res

        serializer = TaskUpdateSerializer(data=request.data)
        if serializer.is_valid():
            update_data = serializer.validated_data
            update_data['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
            task_ref.update(update_data)
            return Response({'message': 'Actualizado'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id):
        token_data = get_user_from_token(request)
        task_ref, error_res = self._get_task_ref(token_data['uid'], task_id)
        if error_res: return error_res
        task_ref.delete()
        return Response({'message': 'Eliminado'})

class AllTasksView(APIView):
    def get(self, request):
        token_data = get_user_from_token(request)
        if not is_admin(token_data['uid']):
            return Response({'error': 'Solo admin'}, status=status.HTTP_403_FORBIDDEN)
        
        db = get_firestore_client()
        tasks_query = db.collection('tasks').stream()
        raw_tasks = [t.to_dict() | {'id': t.id} for t in tasks_query]
        serializer = TaskSerializer(raw_tasks, many=True)
        return Response(serializer.data)
