from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
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
    producto = serializers.CharField(max_length=100, required=False, allow_blank=True)
    cantidad = serializers.FloatField(required=False, default=0)
    unidad = serializers.CharField(max_length=20, required=False, default='litros')
    creado_por_uid = serializers.CharField(read_only=True)
    creado_por_nombre = serializers.CharField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_actualizacion = serializers.DateTimeField(read_only=True)

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
