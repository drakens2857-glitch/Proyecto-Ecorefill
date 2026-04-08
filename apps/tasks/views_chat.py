from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .authentication import FirebaseAuthentication  # ✔ ahora sí funciona
from firebase_utils import get_firestore_client
from firebase_admin import firestore

db = get_firestore_client()


class ChatHistorialApiView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            mensajes_ref = (
                db.collection("chathistorial")
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(20)
                .stream()
            )

            historial = []

            for doc in mensajes_ref:
                data = doc.to_dict()

                # ✅ Convertir timestamp a string (MUY IMPORTANTE)
                timestamp = data.get("timestamp")
                if timestamp:
                    timestamp = timestamp.isoformat()

                historial.append({
                    "id": doc.id,
                    "usuario_id": data.get("usuario_id"),
                    "mensaje": data.get("mensaje"),
                    "timestamp": timestamp
                })

            # ✅ Orden correcto: viejo → nuevo
            historial.reverse()

            return Response(historial, status=status.HTTP_200_OK)

        except Exception as e:
            print("🔥 Error obteniendo historial:", e)  # log para backend

            return Response(
                {"error": "Error al obtener historial"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
