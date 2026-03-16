from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    nombre = serializers.CharField(max_length=100)
    rol = serializers.ChoiceField(choices=['trabajador', 'administrador'], default='trabajador')


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.Serializer):
    uid = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    nombre = serializers.CharField(max_length=100)
    rol = serializers.CharField(read_only=True)
    fecha_registro = serializers.DateTimeField(read_only=True)


class UpdateUserSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100, required=False)
    rol = serializers.ChoiceField(choices=['trabajador', 'administrador'], required=False)
