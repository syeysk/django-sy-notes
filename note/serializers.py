from rest_framework import serializers

from note.models import NoteStorageServiceModel

ERROR_NAME_MESSAGE = (
    'Имена, начинающиеся с ".", зарезервированы для автоматизированного использования'
    ' и недоступны для создания/изменения'
)


class NoteEditViewSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=30, help_text='Название базы')
    title = serializers.CharField(max_length=255, help_text='Новое имя заметки')
    content = serializers.CharField(max_length=20000, help_text='Новое содержимое заметки')

    def validate_title(self, value):
        if value.startswith('.'):
            raise serializers.ValidationError([ERROR_NAME_MESSAGE])

        return value


class NoteCreateViewSerializer(serializers.Serializer):
    def validate_title(self, value):
        if value.startswith('.'):
            raise serializers.ValidationError([ERROR_NAME_MESSAGE])

        return value

    source = serializers.CharField(max_length=30, help_text='Название базы')
    title = serializers.CharField(max_length=255, help_text='Название заметки')
    content = serializers.CharField(max_length=20000, help_text='Содержимое заметки')


class NoteStorageServiceSerializer(serializers.ModelSerializer):
    def validate_source(self, value):
        if value.startswith('.') or (self.instance.source.startswith('.') if self.instance else False):
            raise serializers.ValidationError([ERROR_NAME_MESSAGE])

        return value

    class Meta:
        model = NoteStorageServiceModel
        fields = ['service', 'description', 'is_default', 'source', 'credentials']

    def validate(self, data):
        from note.adapters import service_name_to_class

        uploader_class = service_name_to_class(data['service'])
        if hasattr(uploader_class, 'serializer'):
            serializer = uploader_class.serializer(data=data['credentials'])
            serializer.is_valid(raise_exception=False)
            if serializer.errors:
                raise serializers.ValidationError({'credentials': serializer.errors})

        return data
