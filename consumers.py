import json
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from firebase_utils import get_firestore_client
from firebase_admin import firestore
from asgiref.sync import sync_to_async

db = get_firestore_client()

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # 🔥 Sala dinámica (si no viene, usa "general")
        self.room_name = self.scope['url_route']['kwargs'].get('room', 'general')
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            mensaje = data.get('mensaje')
            usuario_id = data.get('usuario_id')

            # ✅ Validación
            if not mensaje or not usuario_id:
                return

            # ✅ Guardar en Firestore
            await self.guardar_mensaje_firestore(usuario_id, mensaje)

            timestamp = str(datetime.datetime.now())

            # ✅ Enviar a todos
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'mensaje': mensaje,
                    'usuario_id': usuario_id,
                    'timestamp': timestamp
                }
            )

        except Exception as e:
            print(f"🔥 Error en receive: {e}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'mensaje': event['mensaje'],
            'usuario_id': event['usuario_id'],
            'timestamp': event.get('timestamp', '')
        }))

    @sync_to_async
    def guardar_mensaje_firestore(self, usuario_id, mensaje):
        try:
            db.collection("chathistorial").add({
                "usuario_id": usuario_id,
                "mensaje": mensaje,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print("🔥 Error Firestore:", e)
