from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

from note.models import Note


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
    fields = serializers.ChoiceField(
        required=False, default=FIELD_TITLE, choices=FIELDS_CHOICES, help_text='Возвращаемые поля',
    )
    operator = serializers.ChoiceField(
        required=False, default=OPERATOR_OR, choices=OPERATORS_CHOICES, help_text='Логический оператор поиска по полям',
    )
    count_on_page = serializers.IntegerField(
        min_value=1, max_value=100,  help_text='Количество результатов на странице', required=False, default=10,
    )
    page_number = serializers.IntegerField(
        min_value=0, help_text='Номер страницы', required=False, default=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        search_by_field = serializers.ChoiceField(
            required=False, default=self.SEARCH_BY_ALL, choices=self.SEARCH_BYS_CHOICES, help_text='Поиск по полям',
        )
        self.fields.update(
            {'search-by': search_by_field}
        )


class NoteAddViewSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=20000, required=True)

    @extend_schema_field(OpenApiTypes.STR)
    def get_content(self, _):
        return 'содержимое заметки'


class NoteEditViewSerializer(serializers.ModelSerializer):
    new_title = serializers.CharField(source='title', required=False, help_text='Новое имя заметки')
    new_content = serializers.CharField(source='content', required=False, help_text='Новое содержимое заметки')

    def validate(self, data):
        if not data.get('title') and not data.get('content'):
            raise serializers.ValidationError("required new_title or new_content, or both")

        return data

    class Meta:
        model = Note
        fields = ['new_title', 'new_content']


class NoteResponseSerializer(serializers.Serializer):
    """Сериализатор успешного ответа"""
    content = serializers.CharField(max_length=20000, help_text='Содержимое заметки')
    title = serializers.CharField(max_length=255, help_text='Имя заметки')
    source = serializers.CharField(max_length=20, help_text='Название базы')


class ErroResponseSerializer(serializers.Serializer):
    """Сериализатор ошибки со стороны клиента"""
    detail = serializers.CharField(max_length=100, help_text='Тесто ошибки')


class NoteSearchNoteResponseSerializer(serializers.Serializer):
    """Сериализатор заметки"""
    content = serializers.CharField(
        max_length=20000, help_text='Содержимое заметки. Наличие поля зависит от параметра `fields`',
    )
    title = serializers.CharField(max_length=240, help_text='Имя заметки. Наличие поля зависит от параметра `fields`')
    url = serializers.CharField(max_length=100, help_text='URL к заметке в базе')


class NoteSearchResponseSerializer(serializers.Serializer):
    """Сериализатор результатов поиска заметки"""
    count = serializers.IntegerField(min_value=0, help_text='Количество всех найденных заметок')
    pages = serializers.IntegerField(min_value=0, help_text='Количество страниц')
    count_on_page = serializers.IntegerField(
        min_value=1, max_value=100,  help_text='Количество результатов на странице',
    )
    page_number = serializers.IntegerField(min_value=0, help_text='Номер страницы')
    source = serializers.CharField(max_length=20, help_text='Название базы')
    results = NoteSearchNoteResponseSerializer()
