import json

from rest_framework import serializers

from note.models import NoteStorageServiceModel


class NoteEditViewSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=30, help_text='Имя хранилища')
    new_title = serializers.CharField(max_length=255, required=False, help_text='Новое имя заметки')
    new_content = serializers.CharField(max_length=20000, required=False, help_text='Новое содержимое заметки')

    def validate(self, data):
        if not data.get('new_title') and not data.get('new_content'):
            raise serializers.ValidationError('required new_title or new_content, or both')

        return data


class NoteCreateViewSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=30, help_text='Имя хранилища')
    title = serializers.CharField(max_length=255, help_text='Имя заметки')
    content = serializers.CharField(max_length=20000, help_text='Содержимое заметки')


class NoteStorageServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteStorageServiceModel
        fields = ['service', 'description', 'is_default', 'source', 'credentials']

    def validate(self, data):
        from note.load_from_github import service_name_to_class

        uploader_class = service_name_to_class(data['service'])
        if hasattr(uploader_class, 'serializer'):
            serializer = uploader_class.serializer(data=data['credentials'])
            serializer.is_valid(raise_exception=False)
            if serializer.errors:
                raise serializers.ValidationError({'credentials': json.dumps(serializer.errors)})

        return data
