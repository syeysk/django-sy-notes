from django.contrib.auth.models import User
from django.db import models


def prepare_to_search(value):
    return value.lower().replace('ё', 'е')


class Note(models.Model):
    title = models.CharField(verbose_name='Заголовок', max_length=255, null=False, db_index=True, unique=True)
    content = models.TextField(verbose_name='Текст', null=False)
    search_content = models.TextField(verbose_name='Текст для поиска', null=False)
    search_title = models.TextField(verbose_name='Заголовок для поиска', max_length=255, null=False, db_index=True)

    class Meta:
        db_table = 'app_note_note'
        verbose_name = 'Заметка'
        verbose_name_plural = 'Заметки'

    def fetch_search_fields(self):
        self.search_content = prepare_to_search(self.content)
        self.search_title = prepare_to_search(self.title)


class NoteStorageServiceModel(models.Model):
    service = models.CharField(verbose_name='Внешний сервис хранилища', choices=None, max_length=30)
    credentials = models.JSONField(verbose_name='Данные для полключения', default=dict)
    description = models.CharField(verbose_name='Комментарий', max_length=100, default='')
    is_default = models.BooleanField(
        verbose_name='Является ли хранилищем по-умолчанию?',
        help_text=(
            'Если да, то это хранилище будет использовано при открытии страницы списка заметок,'
            ' а также при редактировании заметки'
        ),
        default=False,
    )
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    source = models.CharField(
        verbose_name='Уникальный идентификатор',
        max_length=30,
        unique=True,
        db_index=True,
        help_text='Используется для указания хранилища при поиске, редактировании и отображении заметок',
    )

    class Meta:
        verbose_name = 'Хранилище заметок'
        verbose_name_plural = 'Хранилища заметок'
