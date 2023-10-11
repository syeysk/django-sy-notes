from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from django_sy_framework.linker.utils import link_instance_from_request
from note.models import Note, NoteStorageServiceModel
from utils.constants import (
    API,
    BEFORE_CREATE,
    BEFORE_DELETE_GETTING_ADAPTER,
    BEFORE_DELETE,
    BEFORE_UPDATE,
    BEFORE_UPDATE_GETTING_ADAPTER,
    BEFORE_CREATE_GETTING_ADAPTER,
    BEFORE_OPEN_CREATE_PAGE,
    BEFORE_OPEN_VIEW_PAGE,
    CREATED,
    DELETED,
    UPDATED,
    WEB,
)
from rest_framework.exceptions import PermissionDenied

HOOK_METHOD_NAMES = {
    BEFORE_OPEN_CREATE_PAGE: 'before_open_create_page',
    BEFORE_OPEN_VIEW_PAGE: 'before_open_view_page',
    BEFORE_CREATE_GETTING_ADAPTER: 'before_create_getting_adapter',
    BEFORE_CREATE: 'before_create',
    CREATED: 'created',
    BEFORE_UPDATE_GETTING_ADAPTER: 'before_update_getting_adapter',
    BEFORE_UPDATE: 'before_update',
    UPDATED: 'updated',
    BEFORE_DELETE_GETTING_ADAPTER: 'before_delete_getting_adapter',
    BEFORE_DELETE: 'before_delete',
    DELETED: 'deleted',
}


class LinkerHook:
    @staticmethod
    def before_open_create_page(context, meta):
        if context == WEB:
            link_to = meta.request.GET.get('link_to')
            if link_to:
                meta.source = f'.{link_to}'

    @staticmethod
    def before_create_getting_adapter(context, meta):
        if context == WEB:
            link_to = meta.request.GET.get('link_to')
            if link_to:
                meta.source = f'.{link_to}'
                if not NoteStorageServiceModel.objects.filter(source=meta.source).first():
                    storage = NoteStorageServiceModel(
                        service='DjangoServer',
                        description=f'База знаний для внешнего "{link_to}"',
                        user=meta.request.user,
                        source=meta.source,
                    )
                    storage.save()

    @staticmethod
    def created(context, meta):
        source = meta.source
        if context == WEB:
            link_to = meta.request.GET.get('link_to') or (source[1:] if source.startswith('.project-') else None)
            if link_to:
                instance = Note.objects.filter(title=meta.title, storage=meta.adapter.storage).first()
                link_instance_from_request(instance, link_to)


class AccessHook:
    @staticmethod
    def has_access_to_storage(request, storage):
        user = request.user
        return user.is_superuser or user == storage.user or storage.source == settings.DEFAULT_SOURCE_CODE

    @staticmethod
    def has_access_to_note(request, meta):
        user = request.user
        return user.is_superuser or meta.user is None or isinstance(meta.user, AnonymousUser) or user == meta.user

    def before_open_view_page(self, context, meta):
        if context == WEB:
            storage = NoteStorageServiceModel.objects.filter(source=meta.source).first()
            if not self.has_access_to_storage(meta.request, storage):
                meta.has_access_to_edit = False
            elif not self.has_access_to_note(meta.request, meta):
                meta.has_access_to_edit = False

    def before_create(self, context, meta):
        if context in (WEB, API):
            if not self.has_access_to_storage(meta.request, meta.adapter.storage):
                raise PermissionDenied('Нет прав для создания заметки в базе другого пользователя')

    def before_update(self, context, meta):
        if context in (WEB, API):
            if not self.has_access_to_storage(meta.request, meta.adapter.storage):
                raise PermissionDenied('Нет прав для редактирования заметки в базе другого пользователя')
            elif not self.has_access_to_note(meta.request, meta):
                raise PermissionDenied('Нет прав для редактирования заметки другого пользователя')

    def before_delete(self, context, meta):
        if context in (WEB, API):
            if not self.has_access_to_storage(meta.request, meta.adapter.storage):
                raise PermissionDenied('Нет прав для удаления заметки в базе другого пользователя')
            elif not self.has_access_to_note(meta.request, meta):
                raise PermissionDenied('Нет прав для удаления заметки другого пользователя')


def note_hook(lifecycle, context, meta):
    hook_classes = [AccessHook, LinkerHook]
    hook_method_name = HOOK_METHOD_NAMES[lifecycle]
    for hook_class in hook_classes:
        if hasattr(hook_class, hook_method_name):
            hook = hook_class()
            getattr(hook, hook_method_name)(context, meta)
