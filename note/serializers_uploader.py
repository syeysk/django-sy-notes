from rest_framework import serializers


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


class UploaderGithubSerializer(serializers.Serializer):
    owner = serializers.CharField(label='Имя пользователя')
    repo = serializers.CharField(label='Название репозитория')
    branch = serializers.CharField(label='Наименование ветки')
    directory = serializers.CharField(label='Директория, в которой хранятся заметки')
