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


from firebase_admin import firestore
from firebase_utils import get_firestore_client, verify_firebase_token

def crear_tarea(token_firebase: str, titulo: str, descripcion: str = ""):
    try:
        # 1. Obtener el UID real del usuario (ej: rc8atA...)
        user = verify_firebase_token(token_firebase)
        if not user:
            return {"error": "Token inválido"}
        
        db = get_firestore_client()
        uid_real = user['uid']

        # 2. Diccionario con los nombres de campos EXACTOS de tu captura manual
        data = {
            "titulo": titulo,
            "descripcion": descripcion,
            "estado": "pendiente",
            "prioridad": "media",
            "producto": "Limpiador Multiusos",
            "cantidad": 1,
            "unidad": "litros",
            # IMPORTANTE: Firebase requiere este objeto para poder listar las tareas
            "fecha_creacion": firestore.SERVER_TIMESTAMP,
            "fecha_actualizacion": firestore.SERVER_TIMESTAMP,
            "creado_por_uid": uid_real, # Nombre exacto del campo manual
            "creado_por_nombre": user.get('name', 'Frankin villalba')
        }

        # 3. Guardar obligatoriamente en 'tasks'
        doc_ref = db.collection("tasks").add(data)

        return {
            "id": doc_ref[1].id,
            "mensaje": "¡Logrado! La tarea ya está en la misma carpeta que las manuales."
        }
    except Exception as e:
        return {"error": str(e)}
def eliminar_tarea(token_firebase: str, tarea_id: str):
    """Elimina una tarea de la colección 'tasks'."""
    try:
        # Verificamos que el usuario tenga permiso
        user = verify_firebase_token(token_firebase)
        if not user: return {"error": "No autorizado"}
        
        db = get_firestore_client()
        # Eliminamos de la colección 'tasks' (no 'tareas')
        db.collection("tasks").document(tarea_id).delete()
        return {"mensaje": f"Tarea {tarea_id} eliminada correctamente"}
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
