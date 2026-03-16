import logging
from google import genai
from google.genai import types
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
# Importamos tus utilidades directas para evitar el bloqueo del servidor
from firebase_utils import get_firestore_client, verify_firebase_token
from google.cloud.firestore_v1.base_query import FieldFilter

# --- HERRAMIENTAS DIRECTAS (SIN REQUESTS) ---
def consultar_mis_tareas(token_firebase: str):
    try:
        user = verify_firebase_token(token_firebase)
        if not user: return {"error": "Token inválido"}
        db = get_firestore_client(); docs = db.collection('tareas').where(filter=FieldFilter("usuario_id", "==", user['uid'])).stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e: return {"error": str(e)}

def crear_tarea(token_firebase: str, titulo: str, descripcion: str = ""):
    try:
        user = verify_firebase_token(token_firebase)
        if not user: return {"error": "Token inválido"}
        db = get_firestore_client(); data = {"titulo": titulo, "descripcion": descripcion, "usuario_id": user['uid'], "completada": False}
        doc_ref = db.collection('tareas').add(data); return {"id": doc_ref[1].id, "status": "Éxito"}
    except Exception as e: return {"error": str(e)}

def eliminar_tarea(token_firebase: str, tarea_id: str):
    try:
        db = get_firestore_client(); db.collection('tareas').document(tarea_id).delete(); return {"mensaje": "Eliminado"}
    except Exception as e: return {"error": str(e)}

# --- VISTA PRINCIPAL ---
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def chat_con_ia(request):
    user_prompt = request.data.get('mensaje')
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if ' ' in auth_header else "SIN_TOKEN"
    if not user_prompt: return Response({"error": "Mensaje vacío"}, status=400)
    try:
        client = genai.Client(api_key="AIzaSyBQ0G-jdWJllT99TfzQfGcw--JjYyVMhIM")
        herramientas = [consultar_mis_tareas, crear_tarea, eliminar_tarea]
        system_msg = f"Eres el asistente de Eco-Refill. Tu TOKEN es: {token}. REGLAS: 1. Usa el TOKEN siempre. 2. Confirma acciones."
        config = types.GenerateContentConfig(tools=herramientas, system_instruction=system_msg, automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False))
        response = client.models.generate_content(model="gemini-2.0-flash", contents=user_prompt, config=config)
        # Si la IA solo ejecutó una función y no devolvió texto, enviamos una confirmación
        res_text = response.text if response.text else "Acción procesada correctamente."
        return Response({"respuesta": res_text})
    except Exception as e: return Response({"error": f"Error: {str(e)}"}, status=500)