from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


class NoteAddViewSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=20000, required=True)

    @extend_schema_field(OpenApiTypes.STR)
    def get_content(self, _):
        return 'содержимое заметки'

class NoteEditViewSerializer(serializers.Serializer):
    new_title = serializers.CharField(max_length=255, required=False)
    new_content = serializers.CharField(max_length=20000, required=False)

    def validate(self, data):
        if not data.get('new_title') and not data.get('new_content'):
            raise serializers.ValidationError("required new_title or new_content, or both")

        return data


class NoteResponseSerializer(serializers.Serializer):
    """Сериализатор успешного ответа"""
    content = serializers.CharField(max_length=20000)
    title = serializers.CharField(max_length=255)
    source = serializers.CharField(max_length=20)
