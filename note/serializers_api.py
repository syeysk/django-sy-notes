from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


class NoteSearchViewSerializer(serializers.Serializer):
    FIELD_ALL = 'all'
    FIELD_TITLE = 'title'
    FIELD_CONTENT = 'content'
    FIELDS_CHOICES = (
        (FIELD_ALL, 'оба поля'),
        (FIELD_TITLE, 'имя заметки'),
        (FIELD_CONTENT, 'тело заметки'),
    )

    SEARCH_BY_ALL = 'all'
    SEARCH_BY_TITLE = 'title'
    SEARCH_BY_CONTENT = 'content'
    SEARCH_BYS_CHOICES = (
        (SEARCH_BY_ALL, 'оба поля'),
        (SEARCH_BY_TITLE, 'имя заметки'),
        (SEARCH_BY_CONTENT, 'тело заметки'),
    )

    OPERATOR_OR = 'or'
    OPERATOR_AND = 'and'
    OPERATORS_CHOICES = (
        (OPERATOR_OR, 'или'),
        (OPERATOR_AND, 'и'),
    )
    fields = serializers.ChoiceField(required=False, default=FIELD_TITLE, choices=FIELDS_CHOICES, help_text='Возвращаемые поля')
    operator = serializers.ChoiceField(required=False, default=OPERATOR_OR, choices=OPERATORS_CHOICES, help_text='Логический оператор поиска по полям')
    limit = serializers.IntegerField(min_value=1, max_value=100,  help_text='Количество результатов на странице', required=False, default=10)
    offset = serializers.IntegerField(min_value=0, help_text='Смещение результатов', required=False, default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.update(
            {'search-by': serializers.ChoiceField(required=False, default=self.SEARCH_BY_ALL, choices=self.SEARCH_BYS_CHOICES, help_text='Поиск по полям')}
        )


class NoteAddViewSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=20000, required=True)

    @extend_schema_field(OpenApiTypes.STR)
    def get_content(self, _):
        return 'содержимое заметки'


class NoteEditViewSerializer(serializers.Serializer):
    new_title = serializers.CharField(max_length=255, required=False, help_text='Новое имя заметки')
    new_content = serializers.CharField(max_length=20000, required=False, help_text='Новое содержимое заметки')

    def validate(self, data):
        if not data.get('new_title') and not data.get('new_content'):
            raise serializers.ValidationError("required new_title or new_content, or both")

        return data


class NoteResponseSerializer(serializers.Serializer):
    """Сериализатор успешного ответа"""
    content = serializers.CharField(max_length=20000, help_text='Содержимое заметки')
    title = serializers.CharField(max_length=255, help_text='Имя заметки')
    source = serializers.CharField(max_length=20, help_text='Название базы')


class NoteSearchNoteResponseSerializer(serializers.Serializer):
    """Сериализатор заметки"""
    content = serializers.CharField(max_length=20000, help_text='Содержимое заметки. Наличие поля зависит от параметра `fields`')
    title = serializers.CharField(max_length=255, help_text='Имя заметки. Наличие поля зависит от параметра `fields`')


class NoteSearchResponseSerializer(serializers.Serializer):
    """Сериализатор результатов поиска заметки"""
    count = serializers.IntegerField(min_value=0, help_text='Количество всех найденных заметок')
    limit = serializers.IntegerField(min_value=1, max_value=100,  help_text='Количество результатов на странице')
    offset = serializers.IntegerField(min_value=0, help_text='Смещение результатов')
    source = serializers.CharField(max_length=20, help_text='Название базы')
    path = serializers.CharField(max_length=100, help_text='Путь к заметке на Github-хранилище')
    results = NoteSearchNoteResponseSerializer()
