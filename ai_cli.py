import time, getpass, requests
from google import genai
from google.genai import types
from firebase_utils import get_firestore_client, verify_firebase_token
from google.cloud.firestore_v1.base_query import FieldFilter

# 1. Función de login (Mantiene la llamada HTTP porque es necesaria para el auth)
def login_usuario():
    print("--- Login de usuario ---")
    email = input("Email: "); password = getpass.getpass("Contraseña: ")
    url_login = "http://127.0.0.1:8000/api/users/login/"
    try: 
        res = requests.post(url_login, json={"email": email, "password" : password})
        if res.status_code == 200: print("✅ Logeado correctamente"); return res.json().get('token')
        print(f"❌ Error: {res.json().get('error')}")
    except Exception: print("❌ Error de conexión")
    return None

# --- HERRAMIENTAS DIRECTAS A FIREBASE (Evitan Error 500) ---

def consultar_mis_tareas(token_firebase: str):
    """Consulta Firestore directamente. Úsala siempre antes de borrar."""
    try:
        user = verify_firebase_token(token_firebase)
        if not user: return {"error": "Token inválido"}
        db = get_firestore_client(); docs = db.collection('tareas').where(filter=FieldFilter("usuario_id", "==", user['uid'])).stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e: return {"error": str(e)}

def crear_tarea(token_firebase: str, titulo: str, descripcion: str = ""):
    """Crea una tarea directamente en Firestore."""
    try:
        user = verify_firebase_token(token_firebase)
        if not user: return {"error": "Token inválido"}
        db = get_firestore_client(); data = {"titulo": titulo, "descripcion": descripcion, "usuario_id": user['uid'], "completada": False}
        doc_ref = db.collection('tareas').add(data); return {"id": doc_ref[1].id, "status": "Éxito"}
    except Exception as e: return {"error": str(e)}

def eliminar_tarea(token_firebase: str, tarea_id: str):
    """Borra un documento de Firestore por su ID."""
    try: db = get_firestore_client(); db.collection('tareas').document(tarea_id).delete(); return {"mensaje": "Eliminado correctamente"}
    except Exception as e: return {"error": str(e)}

# --- CONFIGURACIÓN IA ---

API_key = "AIzaSyBQ0G-jdWJllT99TfzQfGcw--JjYyVMhIM"
client = genai.Client(api_key=API_key); modelo_id = "gemini-2.0-flash"

token = login_usuario()

if token:
    print("IA: Hola Frankin, puedo gestionar tus tareas en Eco-Refill.")
    instruccion = f"Tu token es: {token}. REGLAS: 1. Usa el token siempre. 2. Para borrar, consulta primero para ver el ID real."
    chat = client.chats.create(model=modelo_id, config=types.GenerateContentConfig(tools=[consultar_mis_tareas, crear_tarea, eliminar_tarea], system_instruction=instruccion))

    while True:
        user_input = input("\nTu: ")
        if user_input.lower() in ['salir', 'exit', 'chao']: break
        try: 
            response = chat.send_message(user_input)
            print(f"IA: {response.text}") if response.text else print("IA: [Acción completada]")
        except Exception as e:
            if "429" in str(e): print("IA: [Límite alcanzado] Espera 60s..."); time.sleep(60)
            else: print(f"IA: Error: {e}")