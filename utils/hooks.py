from django.conf import settings

from django_sy_framework.linker.utils import link_instance_from_request
from note.models import Note, NoteStorageServiceModel
from utils.constants import (
    BEFORE_CREATE,
    BEFORE_UPDATE,
    BEFORE_CREATE_GETTING_ADAPTER,
    BEFORE_OPEN_CREATE_PAGE,
    BEFORE_OPEN_VIEW_PAGE,
    CREATED,
    WEB,
)
from rest_framework.exceptions import PermissionDenied


def standart_has_access(request, source, storage):
    return request.user == storage.user or source == settings.DEFAULT_SOURCE_CODE


def note_hook(lifecycle, context, meta):
    source = meta.source
    request = meta.request
    if lifecycle == BEFORE_OPEN_CREATE_PAGE and context == WEB:
        link_to = request.GET.get('link_to')
        if link_to:
            meta.source = f'.{link_to}'

    elif lifecycle == BEFORE_OPEN_VIEW_PAGE and context == WEB:
        storage = NoteStorageServiceModel.objects.filter(source=source).first()
        if not standart_has_access(request, source, storage):
            meta.has_access_to_edit = False

    elif lifecycle == BEFORE_CREATE_GETTING_ADAPTER and context == WEB:
        link_to = request.GET.get('link_to')
        if link_to:
            meta.source = f'.{link_to}'
            if not NoteStorageServiceModel.objects.filter(source=source).first():
                storage = NoteStorageServiceModel(
                    service='DjangoServer',
                    description=f'База знаний для внешнего "{link_to}"',
                    user=request.user,
                    source=meta.source,
                )
                storage.save()

    elif lifecycle == BEFORE_CREATE and context == WEB:
        if not standart_has_access(request, source, meta.adapter.storage):
            raise PermissionDenied('Нет прав для создания заметки в базе другого пользователя')

    elif lifecycle == CREATED and context == WEB:
        link_to = request.GET.get('link_to') or (source[1:] if source.startswith('.project-') else None)
        if link_to:
            instance = Note.objects.filter(title=meta.title, storage=meta.adapter.storage).first()
            link_instance_from_request(instance, link_to)

    elif lifecycle == BEFORE_UPDATE and context == WEB:
        if not standart_has_access(request, source, meta.adapter.storage):
            raise PermissionDenied('Нет прав для редактирования заметки в базе другого пользователя')
