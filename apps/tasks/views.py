from datetime import datetime, timezone
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .serializers import TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer
from firebase_utils import get_firestore_client, get_user_from_token, is_admin

# Importamos el servicio de IA
import ia_service 

class TaskListCreateView(APIView):
    @extend_schema(summary="Listar mis tareas", tags=["Tareas"])
    def get(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        db = get_firestore_client()

        if is_admin(uid):
            # Admin ve todo
            tasks_manual = db.collection('tasks').order_by('fecha_creacion', direction='DESCENDING').stream()
            tasks_ia = db.collection('tareas').stream()
            all_docs = list(tasks_manual) + list(tasks_ia)
        else:
            # Usuario ve sus tareas manuales y las creadas por IA
            q1 = db.collection('tasks').where('creado_por_uid', '==', uid).stream()
            q2 = db.collection('tareas').where('usuario_id', '==', uid).stream()
            all_docs = list(q1) + list(q2)

        tasks_dict = {}
        for t in all_docs:
            data = t.to_dict()
            data['id'] = t.id
            tasks_dict[t.id] = data

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
            user_nombre = user_doc.to_dict().get('nombre', 'Usuario Eco-Refill') if user_doc.exists else 'Usuario Eco-Refill'
            
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
            return Response({'id': doc_ref.id, **task_data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskDetailView(APIView):
    def _get_task_ref(self, uid, task_id):
        db = get_firestore_client()
        # Intentar buscar en la colección manual
        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()
        
        # Si no existe, buscar en la colección de la IA
        if not task_doc.exists:
            task_ref = db.collection('tareas').document(task_id)
            task_doc = task_ref.get()

        if not task_doc.exists:
            return None, Response({'error': 'La tarea no existe'}, status=status.HTTP_404_NOT_FOUND)
        
        data = task_doc.to_dict()
        owner_id = data.get('creado_por_uid') or data.get('usuario_id')
        
        if not is_admin(uid) and owner_id != uid:
            return None, Response({'error': 'No tienes permiso para ver esta tarea'}, status=status.HTTP_403_FORBIDDEN)
            
        return task_ref, None

    def get(self, request, task_id):
        token_data = get_user_from_token(request)
        if not token_data: return Response({'error': 'Sesión expirada'}, status=401)
        
        task_ref, error_res = self._get_task_ref(token_data['uid'], task_id)
        if error_res: return error_res
        
        task_data = task_ref.get().to_dict() | {'id': task_id}
        serializer = TaskSerializer(task_data)
        return Response(serializer.data)

    def patch(self, request, task_id):
        token_data = get_user_from_token(request)
        if not token_data: return Response({'error': 'Sesión expirada'}, status=401)

        task_ref, error_res = self._get_task_ref(token_data['uid'], task_id)
        if error_res: return error_res

        serializer = TaskUpdateSerializer(data=request.data)
        if serializer.is_valid():
            update_data = serializer.validated_data
            update_data['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
            task_ref.update(update_data)
            return Response({'message': 'Tarea actualizada correctamente'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id):
        token_data = get_user_from_token(request)
        if not token_data: return Response({'error': 'Sesión expirada'}, status=401)

        task_ref, error_res = self._get_task_ref(token_data['uid'], task_id)
        if error_res: return error_res
        
        task_ref.delete()
        return Response({'message': 'Tarea eliminada correctamente'})

class AllTasksView(APIView):
    def get(self, request):
        token_data = get_user_from_token(request)
        if not token_data or not is_admin(token_data['uid']):
            return Response({'error': 'Acceso restringido a administradores'}, status=status.HTTP_403_FORBIDDEN)
        
        db = get_firestore_client()
        tasks_query = db.collection('tasks').stream()
        raw_tasks = [t.to_dict() | {'id': t.id} for t in tasks_query]
        serializer = TaskSerializer(raw_tasks, many=True)
        return Response({'tareas': serializer.data})

# ---------------------------------------------------------
# ÚNICO ENDPOINT PARA LA IA (CORREGIDO)
# ---------------------------------------------------------

@csrf_exempt
def ia_chat_endpoint(request):
    """
    Endpoint puente para procesar mensajes con Gemini.
    Extrae el token del header Authorization: Bearer <token>
    """
    if request.method == 'POST':
        try:
            # 1. Leer cuerpo del mensaje
            data = json.loads(request.body)
            mensaje = data.get('mensaje')
            
            # 2. Extraer token de forma segura (Bearer ...)
            auth_header = request.headers.get('Authorization')
            token = None
            if auth_header and " " in auth_header:
                token = auth_header.split(' ')[1]
            else:
                token = auth_header # Caso de respaldo

            if not mensaje or not token:
                return JsonResponse({'respuesta': 'Error: Debes iniciar sesión para usar el chat.'}, status=400)

            # 3. Llamada al servicio de IA
            # IMPORTANTE: Asegúrate de que ia_service.procesar_chat_ia(mensaje, token) exista
            resultado = ia_service.procesar_chat_ia(mensaje, token)
            
            # 4. Formatear respuesta para el app.js
            # Si ia_service ya devuelve un dict {'respuesta': ...}, lo pasamos directo.
            # Si devuelve solo un string, lo envolvemos.
            if isinstance(resultado, dict):
                return JsonResponse(resultado)
            else:
                return JsonResponse({'respuesta': resultado})
            
        except Exception as e:
            logging.error(f"Error en Chat IA: {str(e)}")
            return JsonResponse({'respuesta': f'Lo siento, hubo un error en el servidor: {str(e)}'}, status=500)
    
    return JsonResponse({'respuesta': 'Método no permitido'}, status=405)
class EstadisticasView(APIView):
    def get(self, request):
        token_data = get_user_from_token(request)
        if not token_data:
            return Response({'error': 'Token inválido'}, status=status.HTTP_401_UNAUTHORIZED)

        uid = token_data['uid']
        db = get_firestore_client()

        # 1. Obtener tareas según rol
        if is_admin(uid):
            tasks_manual = db.collection('tasks').stream()
            tasks_ia = db.collection('tareas').stream()
            docs = list(tasks_manual) + list(tasks_ia)
        else:
            q1 = db.collection('tasks').where('creado_por_uid', '==', uid).stream()
            q2 = db.collection('tareas').where('usuario_id', '==', uid).stream()
            docs = list(q1) + list(q2)

        # 2. Inicializar contadores
        total_tareas = 0
        completadas = 0
        en_proceso = 0
        pendientes = 0

        # 3. Procesar tareas
        for doc in docs:
            total_tareas += 1
            data = doc.to_dict()

            estado = data.get('estado', 'pendiente').lower()

            print("ESTADO:", estado)  # 👈 DEBUG

            if estado in ['completada']:
                completadas += 1
            elif estado in ['en proceso', 'en_proceso']:
                en_proceso += 1
            else:
                pendientes += 1
        # 4. Calcular porcentaje
        if total_tareas > 0:
            porcentaje = int((completadas / total_tareas) * 100)
        else:
            porcentaje = 0

        # 5. Respuesta
        return Response({
            'total': total_tareas,
            'completadas': completadas,
            'en_proceso': en_proceso,
            'pendientes': pendientes,
            'porcentaje_completado': porcentaje
        })
