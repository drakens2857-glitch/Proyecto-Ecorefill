import logging
from decouple import config
from datetime import datetime

from google import genai
from google.genai import types

from firebase_utils import get_firestore_client, verify_firebase_token
from google.cloud.firestore_v1.base_query import FieldFilter

# --------------------------------
# CONFIG
# --------------------------------

API_KEY = config("GEMINI_API_KEY")
MODELO_ID = "gemini-2.0-flash"

client = genai.Client(api_key=API_KEY)

# memoria en RAM
chats_activos = {}

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------
# 🔹 FUNCIONES FIREBASE (CRUD)
# ---------------------------------------------------------

def consultar_mis_tareas(token: str):
    user = verify_firebase_token(token)
    if not user:
        return {"respuesta": "No autorizado"}

    db = get_firestore_client()

    docs = db.collection("tareas") \
        .where(filter=FieldFilter("usuario_id", "==", user["uid"])) \
        .stream()

    tareas = [{"id": d.id, **d.to_dict()} for d in docs]

    return {"respuesta": str(tareas)}


def crear_nueva_tarea(token: str, titulo: str):
    user = verify_firebase_token(token)
    if not user:
        return {"respuesta": "No autorizado"}

    db = get_firestore_client()

    data = {
        "titulo": titulo,
        "descripcion": "Tarea creada por IA",
        "usuario_id": user["uid"],
        "completada": False,
        "fecha_creacion": datetime.now().isoformat()
    }

    doc_ref = db.collection("tareas").add(data)

    return {
        "respuesta": f"Tarea '{titulo}' creada correctamente"
    }


def eliminar_tarea(token: str, titulo: str):
    user = verify_firebase_token(token)
    if not user:
        return {"respuesta": "No autorizado"}

    db = get_firestore_client()

    docs = db.collection("tareas") \
        .where(filter=FieldFilter("usuario_id", "==", user["uid"])) \
        .stream()

    titulo = titulo.lower().strip()

    for d in docs:
        data = d.to_dict()
        titulo_db = data.get("titulo", "").lower().strip()

        # 🔥 comparación flexible
        if titulo in titulo_db or titulo_db in titulo:
            db.collection("tareas").document(d.id).delete()
            return {"respuesta": f"Tarea '{titulo_db}' eliminada"}

    return {"respuesta": "No encontré esa tarea"}

def leer_tarea(token: str, titulo: str):
    user = verify_firebase_token(token)
    if not user:
        return {"respuesta": "No autorizado"}

    db = get_firestore_client()

    docs = db.collection("tareas") \
        .where(filter=FieldFilter("usuario_id", "==", user["uid"])) \
        .stream()

    titulo = titulo.lower().strip()

    for d in docs:
        data = d.to_dict()
        titulo_db = data.get("titulo", "").lower().strip()

        # 🔥 comparación flexible
        if titulo in titulo_db or titulo_db in titulo:
            return {
                "respuesta": f"Tarea: {data['titulo']}\nDescripción: {data['descripcion']}\nEstado: {'Completada' if data['completada'] else 'Pendiente'}"
            }

    return {"respuesta": "No encontré esa tarea"}

def actualizar_tarea(token: str, titulo: str, nuevo_titulo: str):
    user = verify_firebase_token(token)
    if not user:
        return {"respuesta": "No autorizado"}

    db = get_firestore_client()

    docs = db.collection("tareas") \
        .where(filter=FieldFilter("usuario_id", "==", user["uid"])) \
        .stream()

    titulo = titulo.lower().strip()
    nuevo_titulo = nuevo_titulo.strip()

    for d in docs:
        data = d.to_dict()
        titulo_db = data.get("titulo", "").lower().strip()

        # 🔥 comparación flexible
        if titulo in titulo_db or titulo_db in titulo:
            db.collection("tareas").document(d.id).update({
                "titulo": nuevo_titulo,
                "fecha_actualizacion": datetime.now().isoformat()
            })

            return {"respuesta": f"Tarea actualizada a '{nuevo_titulo}'"}

    return {"respuesta": "No encontré esa tarea"}


def buscar_tarea_por_nombre(token: str, nombre: str):
    user = verify_firebase_token(token)
    if not user:
        return {"respuesta": "No autorizado"}

    db = get_firestore_client()

    docs = db.collection("tareas") \
        .where(filter=FieldFilter("usuario_id", "==", user["uid"])) \
        .stream()

    for d in docs:
        data = d.to_dict()
        if nombre.lower() in data.get("titulo", "").lower():
            return {
                "respuesta": f"Tarea encontrada: {data['titulo']} - {data['descripcion']}"
            }

    return {"respuesta": "No encontré esa tarea"}


# ---------------------------------------------------------
# 🤖 IA CON MEMORIA + FALLBACK
# ---------------------------------------------------------

def procesar_chat_ia(mensaje, token):

    user = verify_firebase_token(token)
    if not user:
        return {"respuesta": "No autorizado"}

    uid = user["uid"]

    if uid not in chats_activos:

        instrucciones = """
Eres un asistente inteligente de Eco-Refill.

Ayudas a gestionar tareas.

Puedes:
- Crear tareas
- Listar tareas
- Eliminar tareas
- Leer tareas
- Actualizar tareas

Habla en español y entiende lenguaje natural.
"""

        chats_activos[uid] = client.chats.create(
            model=MODELO_ID,
            config=types.GenerateContentConfig(
                tools=[
                    consultar_mis_tareas,
                    crear_nueva_tarea,
                    eliminar_tarea,
                    leer_tarea,
                    actualizar_tarea,
                    buscar_tarea_por_nombre
                ],
                system_instruction=instrucciones
            )
        )

    chat = chats_activos[uid]

    try:
        response = chat.send_message(mensaje)

        if response.text:
            return {"respuesta": response.text}

        return {"respuesta": "Acción realizada correctamente"}

    except Exception as e:

        mensaje_lower = mensaje.lower()

        # 🔴 FALLBACK SI GEMINI FALLA
        if "429" in str(e) or "resource_exhausted" in str(e).lower():

            # 🟢 CREAR
            if "crear" in mensaje_lower or "crea" in mensaje_lower:
                titulo = mensaje_lower.replace("crear", "").replace("crea", "").replace("tarea", "").strip()
                return crear_nueva_tarea(token, titulo)

            # 🟢 LISTAR
            if "tareas" in mensaje_lower or "listar" in mensaje_lower:
                return consultar_mis_tareas(token)

            # 🟢 ELIMINAR
            if "eliminar" in mensaje_lower or "borra" in mensaje_lower:
                titulo = mensaje_lower.replace("eliminar", "").replace("borra", "").replace("tarea", "").strip()
                return eliminar_tarea(token, titulo)

            # 🟢 LEER
            if "leer" in mensaje_lower or "ver" in mensaje_lower:
                titulo = mensaje_lower.replace("leer", "").replace("ver", "").replace("tarea", "").strip()
                return leer_tarea(token, titulo)

            # 🟢 ACTUALIZAR (ARREGLADO)
            if " a " in mensaje_lower and any(p in mensaje_lower for p in ["cambiar", "modificar", "actualizar", "renombrar"]):

                texto = mensaje_lower

                for palabra in ["cambiar", "modificar", "actualizar", "renombrar", "la", "tarea"]:
                    texto = texto.replace(palabra, "")

                texto = texto.strip()

                partes = texto.split(" a ")

                if len(partes) == 2:
                    titulo_viejo = partes[0].strip()
                    titulo_nuevo = partes[1].strip()

                    if titulo_viejo and titulo_nuevo:
                        resultado = actualizar_tarea(token, titulo_viejo, titulo_nuevo)

                        # asegurar formato correcto
                        if isinstance(resultado, dict) and "respuesta" in resultado:
                            return resultado
                        else:
                            return {"respuesta": str(resultado)}

                return {"respuesta": "No entendí cómo actualizar la tarea"}
