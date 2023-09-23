from django.conf import settings

from django_sy_framework.linker.utils import link_instance_from_request
from django_sy_framework.utils.exceptions import Http403
from note.models import Note
from utils.constants import BEFORE_CREATE, BEFORE_EDIT, CREATED, WEB


def standart_has_access(request, source, adapter):
    return request.user == adapter.storage.user or source == settings.DEFAULT_SOURCE_CODE


def note_hook(lifecycle, context, note, adapter, request):
    if lifecycle == BEFORE_EDIT and context == WEB:
        source, title, new_title, new_content = note
        if not standart_has_access(request, source, adapter):
            raise Http403('Нет прав для редактирования данной заметки')

    elif lifecycle == BEFORE_CREATE and context == WEB:
        source, title, content = note
        if not standart_has_access(request, source, adapter):
            raise Http403('Нет прав для создания заметки в данной базе')

    elif lifecycle == CREATED and context == WEB:
        source, title, _ = note
        link_to = request.GET.get('link_to') or (source[1:] if source.startswith('.project-') else None)
        if link_to:
            instance = Note.objects.filter(title=title, storage=adapter.storage).first()
            link_instance_from_request(instance, link_to)
