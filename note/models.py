import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.shortcuts import resolve_url

from django_sy_framework.linker.models import Linker
from note.adapters import get_service_names
from note.validators import FilenameValidator


def prepare_to_search(value):
    return value.lower().replace('ё', 'е')


class Note(models.Model):
    storage = models.ForeignKey(
        'note.NoteStorageServiceModel',
        null=False,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    title = models.CharField(
        verbose_name='Заголовок',
        max_length=240,
        null=False,
        db_index=True,
        validators=(FilenameValidator(),),
    )
    content = models.TextField(verbose_name='Текст', null=False)
    search_content = models.TextField(verbose_name='Текст для поиска', null=False)
    search_title = models.TextField(verbose_name='Заголовок для поиска', max_length=240, null=False, db_index=True)
    linker = GenericRelation(Linker, related_query_name='note')
    user = models.ForeignKey(get_user_model(), null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @property
    def url(self):
        return '{}{}'.format(settings.SITE_URL, resolve_url('note_editor2', self.storage.source, self.title))

    @property
    def url_new(self):
        return '{}{}'.format(settings.SITE_URL, resolve_url('note_create', settings.DEFAULT_SOURCE_CODE))

    class Meta:
        db_table = 'app_note_note'
        verbose_name = 'Заметка'
        verbose_name_plural = 'Заметки'
        constraints = [
            models.UniqueConstraint(fields=('storage', 'title'), name='unique_note_storage_title')
        ]
        indexes = [
            models.Index(fields=('storage',), name='index_note_storage'),
        ]

    def fetch_search_fields(self):
        self.search_content = prepare_to_search(self.content)
        self.search_title = prepare_to_search(self.title)


class ImageNote(models.Model):
    UPLOAD_TO = 'note'
    note = models.ForeignKey(Note, null=False, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=UPLOAD_TO)


class NoteStorageServiceModel(models.Model):
    CHOICES_SERVICE = get_service_names()
    service = models.CharField(verbose_name='Внешний сервис базы', max_length=30, choices=CHOICES_SERVICE, blank=False)
    credentials = models.JSONField(verbose_name='Данные для подключения', default=dict)
    description = models.CharField(verbose_name='Комментарий', max_length=100, default='')
    is_default = models.BooleanField(
        verbose_name='Является ли база по-умолчанию?',
        help_text=(
            'Если да, то эта база будет использовано при открытии страницы списка заметок,'
            ' а также при редактировании заметки'
        ),
        default=False,
    )
    user = models.ForeignKey(get_user_model(), null=False, on_delete=models.CASCADE)
    source = models.CharField(
        verbose_name='Уникальный идентификатор',
        max_length=30,
        unique=True,
        db_index=True,
        help_text='Используется для указания базы при поиске, редактировании и отображении заметок',
        validators=(FilenameValidator(),),
    )
    uuid = models.UUIDField(null=False, blank=False, unique=True, default=uuid.uuid4)

    def __str__(self):
        return self.source

    class Meta:
        verbose_name = 'База заметок'
        verbose_name_plural = 'Базы заметок'
