from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    titulo = serializers.CharField(max_length=200)
    descripcion = serializers.CharField()
    estado = serializers.ChoiceField(
        choices=['pendiente', 'en_proceso', 'completada', 'PENDIENTE'], # Añadí PENDIENTE por si acaso
        default='pendiente'
    )
    prioridad = serializers.ChoiceField(
        choices=['baja', 'media', 'alta', 'Baja', 'Media', 'Alta'],
        default='media'
    )
    producto = serializers.CharField(max_length=100, required=False, allow_blank=True)
    cantidad = serializers.FloatField(required=False, default=0)
    unidad = serializers.CharField(max_length=20, required=False, default='litros')
    creado_por_uid = serializers.CharField(read_only=True)
    creado_por_nombre = serializers.CharField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True, required=False)
    fecha_actualizacion = serializers.DateTimeField(read_only=True, required=False)

    def to_representation(self, instance):
        """
        Esta función se encarga de 'traducir' los campos de Firestore 
        al formato que espera tu Frontend antes de enviarlos.
        """
        # Si la instancia es un diccionario (común en Firestore)
        data = instance if isinstance(instance, dict) else instance.__dict__
        
        # NORMALIZACIÓN: Si el ID viene con otro nombre, lo movemos a creado_por_uid
        if 'usuario_id' in data and not data.get('creado_por_uid'):
            data['creado_por_uid'] = data['usuario_id']
        elif 'uid' in data and not data.get('creado_por_uid'):
            data['creado_por_uid'] = data['uid']
            
        # Aseguramos que el estado siempre sea reconocible (ej. minúsculas)
        if 'estado' in data:
            data['estado'] = data['estado'].lower()

        return super().to_representation(data)


class TaskCreateSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=200)
    descripcion = serializers.CharField()
    estado = serializers.ChoiceField(
        choices=['pendiente', 'en_proceso', 'completada'],
        default='pendiente'
    )
    prioridad = serializers.ChoiceField(
        choices=['baja', 'media', 'alta'],
        default='media'
    )
    producto = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    cantidad = serializers.FloatField(required=False, default=0)
    unidad = serializers.CharField(max_length=20, required=False, default='litros')


class TaskUpdateSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=200, required=False)
    descripcion = serializers.CharField(required=False)
    estado = serializers.ChoiceField(
        choices=['pendiente', 'en_proceso', 'completada'],
        required=False
    )
    prioridad = serializers.ChoiceField(
        choices=['baja', 'media', 'alta'],
        required=False
    )
    producto = serializers.CharField(max_length=100, required=False, allow_blank=True)
    cantidad = serializers.FloatField(required=False)
    unidad = serializers.CharField(max_length=20, required=False)
