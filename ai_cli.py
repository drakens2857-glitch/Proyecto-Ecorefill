import time
import getpass
import requests

from decouple import config
from google import genai
from google.genai import types

from firebase_utils import get_firestore_client
from google.cloud.firestore_v1.base_query import FieldFilter


# --------------------------------
# CONFIGURACIÓN IA
# --------------------------------

API_KEY = config("GEMINI_API_KEY")
MODELO_ID = "gemini-2.0-flash"


# --------------------------------
# 1. LOGIN DE USUARIO
# --------------------------------

def login_usuario():

    print("\n--- Login Eco-Refill ---")

    email = input("Email: ")
    password = getpass.getpass("Contraseña: ")

    url_login = "http://127.0.0.1:8000/api/users/login/"

    try:

        res = requests.post(
            url_login,
            json={
                "email": email,
                "password": password
            }
        )

        if res.status_code == 200:

            print("✅ Login exitoso")

            return res.json().get("token")

        print("❌ Error:", res.json().get("error"))

    except Exception as e:

        print("❌ Error de conexión:", e)

    return None


# --------------------------------
# 2. TOOLS PARA GEMINI
# --------------------------------

def consultar_mis_tareas(token_firebase: str):
    """Obtiene las tareas del usuario"""

    try:

        db = get_firestore_client()

        docs = db.collection("tasks") \
            .where(filter=FieldFilter("usuario_id", "==", token_firebase)) \
            .stream()

        tareas = []

        for d in docs:

            tareas.append({
                "id": d.id,
                **d.to_dict()
            })

        return tareas

    except Exception as e:

        return {"error": str(e)}


def crear_tarea(token_firebase: str, titulo: str, descripcion: str = ""):

    db = get_firestore_client()

    data = {
        "titulo": titulo,
        "descripcion": descripcion,
        "estado": "pendiente",
        "prioridad": "media",
        "producto": "",
        "cantidad": 0,
        "unidad": "litros",
        "fecha_creacion": time.strftime("%Y-%m-%d"),
        "creado_por_uid": token_firebase,
        "creado_por_nombre": "IA"
    }

    doc_ref = db.collection("tasks").add(data)

    return {
        "id": doc_ref[1].id,
        "mensaje": "Tarea creada correctamente"
    }
def eliminar_tarea(token_firebase: str, tarea_id: str):
    """Elimina una tarea"""

    try:

        db = get_firestore_client()

        db.collection("tasks").document(tarea_id).delete()

        return {
            "mensaje": f"Tarea {tarea_id} eliminada correctamente"
        }

    except Exception as e:

        return {"error": str(e)}


# --------------------------------
# 3. INICIAR ASISTENTE
# --------------------------------

def iniciar_asistente():

    token = login_usuario()

    if not token:
        return

    client = genai.Client(api_key=API_KEY)

    instrucciones = f"""
Eres el asistente de tareas del sistema Eco-Refill.

Token del usuario:
{token}

Herramientas disponibles:

consultar_mis_tareas
crear_tarea
eliminar_tarea

Reglas importantes:

1 Usa siempre el token en el parámetro token_firebase
2 Antes de eliminar tareas debes consultar la lista
3 Confirma siempre la acción realizada
4 Habla en español
"""

    chat = client.chats.create(

        model=MODELO_ID,

        config=types.GenerateContentConfig(

            tools=[
                consultar_mis_tareas,
                crear_tarea,
                eliminar_tarea
            ],

            system_instruction=instrucciones
        )
    )

    print("\n🤖 IA: Hola. Puedo ayudarte a gestionar tus tareas.")


    while True:

        user_input = input("\nTú: ")

        if user_input.lower() in ["salir", "exit", "adios", "adiós"]:
            print("🤖 IA: Hasta luego")
            break

        try:

            response = chat.send_message(user_input)

            if response.text:

                print(f"\n🤖 IA: {response.text}")

            else:

                print("\n🤖 IA: Acción ejecutada correctamente")

            time.sleep(2)

        except Exception as e:

            if "429" in str(e):

                print("⚠️ Límite de cuota alcanzado. Esperando 60 segundos...")
                time.sleep(60)

            else:

                print("❌ Error:", e)


# --------------------------------
# EJECUCIÓN
# --------------------------------

if __name__ == "__main__":

    iniciar_asistente()
