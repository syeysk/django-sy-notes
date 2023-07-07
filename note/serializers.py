from rest_framework import serializers


class NoteEditViewSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, help_text='Текущее имя заметки')
    new_title = serializers.CharField(max_length=255, required=False, help_text='Новое имя заметки')
    new_content = serializers.CharField(max_length=20000, required=False, help_text='Новое содержимое заметки')

    def validate(self, data):
        if not data.get('new_title') and not data.get('new_content'):
            raise serializers.ValidationError("required new_title or new_content, or both")

        return data


class UploaderTypesenseSerializer(serializers.Serializer):
    PROTOCOL_HTTPS = 'https'
    PROTOCOL_HTTP = 'http'
    CHOICES_PROTOCOL = (
        (PROTOCOL_HTTPS, 'HTTPS'),
        (PROTOCOL_HTTP, 'HTTP'),
    )
    server = serializers.URLField(label='Сервер', default='localhost')
    port = serializers.IntegerField(label='Порт', default=8108)
    protocol = serializers.ChoiceField(label='Протокол', choices=CHOICES_PROTOCOL, default=PROTOCOL_HTTP)
    api_key = serializers.CharField(label='Ключ API')


class UploaderFirestoreSerializer(serializers.Serializer):
    certificate = serializers.JSONField(label='Сертификат доступа', default='{}')
