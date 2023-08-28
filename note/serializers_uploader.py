from rest_framework import serializers


class UploaderTypesenseSerializer(serializers.Serializer):
    PROTOCOL_HTTPS = 'https'
    PROTOCOL_HTTP = 'http'
    CHOICES_PROTOCOL = (
        (PROTOCOL_HTTPS, 'HTTPS'),
        (PROTOCOL_HTTP, 'HTTP'),
    )
    server = serializers.URLField(help_text='Сервер', default='localhost')
    port = serializers.IntegerField(help_text='Порт', default=8108)
    protocol = serializers.ChoiceField(help_text='Протокол', choices=CHOICES_PROTOCOL, default=PROTOCOL_HTTP)
    api_key = serializers.CharField(help_text='Ключ API')


class UploaderFirestoreSerializer(serializers.Serializer):
    certificate = serializers.JSONField(help_text='Сертификат доступа', default=dict())


class UploaderGithubSerializer(serializers.Serializer):
    owner = serializers.CharField(help_text='Имя пользователя')
    repo = serializers.CharField(help_text='Название репозитория')
    branch = serializers.CharField(help_text='Наименование ветки')
    directory = serializers.CharField(help_text='Директория, в которой хранятся заметки')


class UploaderDjangoServerSerializer(serializers.Serializer):
    path = serializers.CharField(help_text='Путь')
