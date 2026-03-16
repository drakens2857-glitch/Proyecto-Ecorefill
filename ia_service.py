import logging
import time
from decouple import config

from google import genai
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from firebase_utils import get_firestore_client, verify_firebase_token
from google.cloud.firestore_v1.base_query import FieldFilter


# -----------------------------
# FUNCIONES DE TAREAS
# -----------------------------

def consultar_mis_tareas(token):

    user = verify_firebase_token(token)

    if not user:
        return {"error": "Token inválido"}

    db = get_firestore_client()

    docs = db.collection("tareas").where(
        filter=FieldFilter("usuario_id", "==", user["uid"])
    ).stream()

    tareas = [{"id": d.id, **d.to_dict()} for d in docs]

    return tareas


def crear_tarea(token, titulo):

    user = verify_firebase_token(token)

    if not user:
        return {"error": "Token inválido"}

    db = get_firestore_client()

    data = {
        "titulo": titulo,
        "descripcion": "",
        "usuario_id": user["uid"],
        "completada": False
    }

    doc_ref = db.collection("tareas").add(data)

    return {"mensaje": "Tarea creada", "id": doc_ref[1].id}


def eliminar_tarea(token, tarea_id):

    user = verify_firebase_token(token)

    if not user:
        return {"error": "Token inválido"}

    db = get_firestore_client()

    db.collection("tareas").document(tarea_id).delete()

    return {"mensaje": "Tarea eliminada"}


# -----------------------------
# CHAT IA
# -----------------------------

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def chat_con_ia(request):

    try:

        mensaje = request.data.get("mensaje", "").lower()

        if not mensaje:
            return Response({"error": "Mensaje vacío"}, status=400)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split(" ")[1] if " " in auth_header else None

        if not token:
            return Response({"error": "Token no proporcionado"}, status=401)

        # evitar rate limit
        time.sleep(1)

        # -----------------------------
        # INTENCIONES DEL USUARIO
        # -----------------------------

        if "ver" in mensaje and "tarea" in mensaje:

            tareas = consultar_mis_tareas(token)

            return Response({
                "respuesta": "Estas son tus tareas",
                "tareas": tareas
            })


        if "crear" in mensaje or "crea" in mensaje:

            titulo = mensaje.replace("crear", "").replace("crea", "").replace("tarea", "").strip()

            if not titulo:
                return Response({"respuesta": "¿Qué tarea deseas crear?"})

            tarea = crear_tarea(token, titulo)

            return Response({
                "respuesta": f"Tarea creada: {titulo}",
                "tarea": tarea
            })


        if "eliminar" in mensaje or "elimina" in mensaje:

            partes = mensaje.split()

            tarea_id = partes[-1]

            eliminar_tarea(token, tarea_id)

            return Response({
                "respuesta": "Tarea eliminada correctamente"
            })


        # -----------------------------
        # RESPUESTA NORMAL DE IA
        # -----------------------------

        client = genai.Client(
            api_key=config("GEMINI_API_KEY")
        )

        system_prompt = """
Eres el asistente del sistema Eco-Refill.
Ayudas al usuario con reciclaje y gestión de tareas.
Responde de forma clara y corta.
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{system_prompt}\nUsuario: {mensaje}"
        )

        return Response({
            "respuesta": response.text
        })


    except Exception as e:

        logging.error("ERROR IA: %s", str(e))

        if "429" in str(e):
            return Response(
                {"error": "Demasiadas solicitudes a la IA. Intenta en unos segundos."},
                status=429
            )

        return Response({"error": str(e)}, status=500)
