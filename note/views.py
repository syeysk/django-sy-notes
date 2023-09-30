import datetime
import zipfile
import os
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import unquote

import yaml
import requests
from django.conf import settings
from django.core.files.images import ImageFile
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views import View
from drf_spectacular.utils import extend_schema
from markdownify.templatetags.markdownify import markdownify
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView
from rest_framework import status

from django_sy_framework.utils.logger import logger
from note.adapters import get_storage_service, get_service_names, run_initiator
from note.models import (
    ImageNote,
    Note,
    NoteStorageServiceModel,
    prepare_to_search,
)
from note.serializers import (
    ERROR_NAME_MESSAGE,
    NoteCreateViewSerializer,
    NoteEditViewSerializer,
    NoteStorageServiceSerializer,
)
from utils.constants import (
    BEFORE_CREATE,
    BEFORE_CREATE_GETTING_ADAPTER,
    BEFORE_OPEN_CREATE_PAGE,
    BEFORE_OPEN_VIEW_PAGE,
    BEFORE_UPDATE,
    BEFORE_UPDATE_GETTING_ADAPTER,
    CREATED,
    UPDATED,
    WEB,
)
from utils.hooks import note_hook


def separate_yaml(content):
    content = content.strip()
    lines = content.split('\n')
    is_yaml = lines and lines[0] == '---'
    data_yaml = {}
    if is_yaml:
        yaml_length = 4
        for line in lines[1:]:
            if line == '---':
                break

            yaml_length += len(line) + 1

        data_yaml = yaml.load(content[:yaml_length], yaml.SafeLoader)
        content = content[yaml_length + 4:].lstrip()

    return data_yaml, content


@dataclass
class CreatedNote:
    source: str
    title: str
    content: str
    request: 'django.http.HttpRequest' = None
    adapter: 'note.adapters.base_adapter.BaseAdapter' = None


@dataclass
class UpdatedNote:
    source: str
    title: str
    new_title: str
    new_content: str
    request: 'django.http.HttpRequest' = None
    adapter: 'note.adapters.base_adapter.BaseAdapter' = None


@dataclass
class CreatePageNote:
    source: str
    request: 'django.http.HttpRequest' = None


@dataclass
class ViewPageNote:
    source: str
    title: str
    content: str
    request: 'django.http.HttpRequest' = None
    has_access_to_edit: bool = True


@extend_schema(
    tags=['Заметки'],
)
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
def note_hook_old(request):  # TODO: метод хука планируется перенести в адаптер базы. Сейчас хук не работает
    """Хук для обновления заметок на сервере из принятого Pull Request'а на Github"""
    data = {'files': {}}
    action = request._request.headers.get('X-Github-Event')
    if action == 'push':
        repository = request.data.get('repository')
        repo_name = repository.get('name')
        owner_name = repository.get('owner').get('name')
        if owner_name != settings.GITHUB_OWNER or repo_name != settings.GITHUB_REPO:
            return Response(status=status.HTTP_200_OK, data={'message': 'repository or owner name has no access'})

        session = requests.Session()
        prefix = settings.GITHUB_DIRECTORY
        removed = data['files'].setdefault('removed', set())
        added = data['files'].setdefault('added', set())
        modified = data['files'].setdefault('modified', set())
        for commit in request.data['commits']:
            data.setdefault('l', []).append({})
            for action_type, files in data['files'].items():
                for file in commit[action_type]:
                    if not file.startswith(prefix):
                        continue

                    data['l'][-1].setdefault(action_type, []).append(file)
                    if action_type == 'removed':
                        if file in removed:
                            removed.remove(file)

                        if file in modified:
                            modified.remove(file)

                        files.add(file)
                    elif action_type == 'modified':
                        if file not in added:
                            modified.add(file)
                    elif action_type == 'added':
                        if file in removed:
                            removed.remove(file)

                        files.add(file)

        for action_type, files in data['files'].items():
            for file in files:
                title, _ = os.path.splitext(os.path.basename(file))
                url = UploaderGithub.URL_ARCHIVE.format()
                if action_type == 'removed':
                    Note.objects.filter(title=title).delete()
                elif action_type == 'modified':
                    request = session.get(url)
                    content = request.text
                    note = Note.objects.filter(title=title).first()
                    note.content = content
                    note.search_content = prepare_to_search(content)
                    note.save()
                elif action_type == 'added':
                    request = session.get(url)
                    content = request.text
                    note = Note(
                        title=title,
                        search_title=prepare_to_search(title),
                        content=content,
                        search_content=prepare_to_search(content),
                    )
                    note.save()

        return Response(status=status.HTTP_200_OK, data=data)


def safe_markdown(content, source):
    error_message = None
    content_html = None
    content_yaml, content_md = separate_yaml(content)
    content_md = content_md.replace('\r\n', '\n')
    config = {'utils.md_extensions.apply_source:ApplySourceExtension': {'source': source}}
    try:
        content_html = markdownify(content_md, dynamic_extension_config=config)
    except Exception as error:
        import logging
        error_message = 'Заметка содержит синтаксическую ошибку'
        logger.error('Ошибка парсинга заметки: %s' % error)

    return content_html, error_message


class NoteView(View):
    @staticmethod
    def get(request, quoted_title=None):
        source = request.GET.get('source') or request.COOKIES.get('source')
        if quoted_title is None:
            if not request.user.is_authenticated:
                return render(request, '401.html')

            meta = CreatePageNote(source, request)
            note_hook(BEFORE_OPEN_CREATE_PAGE, WEB, meta)
            context = {'note': None, 'source': meta.source, 'has_access_to_edit': True}
            return render(request, 'note/note_editor.html', context)

        with get_storage_service(source) as (uploader, source):
            note = uploader.get(unquote(quoted_title))

        if not note:
            raise Http404('Заметка не найдена')

        meta = ViewPageNote(source, note['title'], note['content'], request)
        content_html, error_message = safe_markdown(meta.content, meta.source)
        note_hook(BEFORE_OPEN_VIEW_PAGE, WEB, meta)
        context = {
            'note': {
                'title': meta.title,
                'content': meta.content,
                'content_html': content_html,
                'error_message': error_message,
            },
            'source': meta.source,
            'has_access_to_edit': meta.has_access_to_edit,
        }
        return render(request, 'note/note_editor.html', context)


class NoteEditView(APIView):
    @staticmethod
    def save_images(source, title, request):
        note = Note.objects.filter(storage__source=source, title=title).first()
        if note:
            for uploaded_image in request.FILES.getlist('images'):
                if not os.path.exists(f'{settings.MEDIA_ROOT}/note/{uploaded_image.name}'):
                    image = ImageNote(note=note, image=ImageFile(uploaded_image, uploaded_image.name))
                    image.save()

    def put(self, request, quoted_title):
        """
        Метод редактирования существующей заметки.

        Обязателен как минимум один из параметров в теле: `content` или `title`.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = NoteEditViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(quoted_title)
        if title.startswith('.'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'title': [ERROR_NAME_MESSAGE]})

        meta = UpdatedNote(data['source'], title, data.get('title'), data.get('content'), request, None)
        note_hook(BEFORE_UPDATE_GETTING_ADAPTER, WEB, meta)
        with get_storage_service(meta.source) as (uploader, source):
            meta.adapter = uploader
            meta.source = source
            if not uploader.get(title=title):
                return Response(status=status.HTTP_404_NOT_FOUND)

            if meta.new_title and meta.new_title != meta.title and uploader.get(title=meta.new_title):
                response_data = {'title': ['Заметка с таким названием уже существует']}
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)

            note_hook(BEFORE_UPDATE, WEB, meta)
            updated_fields = uploader.edit(meta.title, meta.new_title, meta.new_content)
            note_hook(UPDATED, WEB, meta)
            self.save_images(meta.source, title, request)

        content_html, error_message = safe_markdown(meta.new_content, meta.source)
        return Response(
            status=status.HTTP_200_OK,
            data={'updated_fields': updated_fields, 'content_html': content_html, 'error_message': error_message},
        )

    def post(self, request):
        """Метод создания новой заметки"""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = NoteCreateViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        meta = CreatedNote(data['source'], data['title'], data['content'], request, None)
        note_hook(BEFORE_CREATE_GETTING_ADAPTER, WEB, meta)
        with get_storage_service(meta.source) as (uploader, source):
            meta.adapter = uploader
            meta.source = source
            if uploader.get(title=meta.title):
                response_data = {'title': ['Заметка с таким названием уже существует']}
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)

            note_hook(BEFORE_CREATE, WEB, meta)
            uploader.add(meta.title, meta.content)
            note_hook(CREATED, WEB, meta)
            self.save_images(meta.source, meta.title, request)

        content_html, error_message = safe_markdown(meta.content, meta.source)
        return Response(
            status=status.HTTP_200_OK,
            data={'updated_fields': ['title', 'content'], 'content_html': content_html, 'error_message': error_message},
        )


class NoteListView(View):
    def get(self, request):
        search_string = request.GET.get('s')
        page_number = request.GET.get('p', '1')
        page_number = int(page_number) if page_number.isdecimal() else 1
        count_on_page = 20
        source = request.GET.get('source') or request.COOKIES.get('source')

        context = {
            'error': '',
            'source': source,
            'sources': NoteStorageServiceModel.objects.values('source', 'description'),
            'current_page': page_number,
        }

        user = request.user
        if request.user.is_authenticated:
            if source:
                user = None

        try:
            with get_storage_service(source, user) as (uploader, source):
                if search_string:
                    notes, meta = uploader.search(
                        'or', count_on_page, page_number, ['title', 'content'], search_string, search_string,
                    )
                else:
                    notes, meta = uploader.get_list(page_number, count_on_page)

                context.update({
                    'notes': notes,
                    'last_page': meta['num_pages'],
                    'source': source,
                })
                return render(request, 'note/note_list.html', context)
        except Exception as error:
            context['error'] = str(error)
            context['notes'] = []
            context['last_page'] = 0
            return render(request, 'note/note_list.html', context)


class NoteStorageServiceListView(APIView):
    @staticmethod
    def get(request):
        """The view shows the list of storages"""
        storages = NoteStorageServiceModel.objects.order_by('-pk')
        common_values = ['service', 'description', 'source', 'pk']
        if request.user.is_authenticated:
            storages = storages.filter(user=request.user).values('is_default', 'credentials', *common_values)
        else:
            storages = storages.values(*common_values)

        auto_schema = AutoSchema()
        service_maps = {}
        for subclass_name, subclass in get_service_names(True):
            service_serializer = getattr(subclass, 'serializer', None)
            if service_serializer:
                service_map = auto_schema.map_serializer(service_serializer())
                service_maps[subclass_name] = service_map['properties']

        context = {
            'storage_services': list(storages),
            'service_names': list(NoteStorageServiceModel.CHOICES_SERVICE),
            'service_maps': service_maps,
        }
        return render(request, 'note/note_storage_services.html', context)

    @staticmethod
    def post(request, pk=None):
        """The view edits a storage or creates a new storage if pk=0"""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if pk:
            instance = NoteStorageServiceModel.objects.get(pk=pk, user=request.user)
            if request.user.pk != instance.user.pk:
                return Response(status=status.HTTP_403_FORBIDDEN)

            serializer = NoteStorageServiceSerializer(instance, data=request.POST)
            serializer.is_valid(raise_exception=True)
            updated_fields = [
                name for name, value in serializer.validated_data.items() if getattr(instance, name) != value
            ]
            updated_cred_fields = [
                name for name, value in serializer.validated_data['credentials'].items()
                if instance.credentials.get(name) != value
            ]
            serializer.save()
        else:
            serializer = NoteStorageServiceSerializer(data=request.POST)
            serializer.is_valid(raise_exception=True)
            updated_fields = serializer.fields.keys()
            updated_cred_fields = serializer.validated_data['credentials'].keys()
            instance = serializer.save(user=request.user)

        response_data = {
            'id': instance.pk, 'updated_fields': updated_fields, 'updated_cred_fields': updated_cred_fields,
        }
        return Response(status=status.HTTP_200_OK, data=response_data)


class NoteImportExportView(APIView):
    @staticmethod
    def get(request):
        command = request.GET.get('command')
        if command == 'download-archive':
            # information about all compress formats: https://docs.python.org/3/library/archiving.html
            source = request.GET['source-from']
            archive_file = BytesIO()
            with zipfile.ZipFile(archive_file, mode='w') as archive:
                with get_storage_service(source) as (uploader, real_source):
                    if source == real_source:
                        page_number = 1
                        meta = None
                        while meta is None or page_number <= meta['num_pages']:
                            notes, meta = uploader.get_list(page_number, 100)
                            for note in notes:
                                archive.writestr('{}/{}.md'.format(source, note['title']), note['content'])

                            page_number += 1

            response = HttpResponse(archive_file.getvalue(), content_type='application/zip')
            datetime_str = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            response['Content-Disposition'] = f'attachment; filename="notes-{datetime_str}.zip"'
            return response

        storages_from = NoteStorageServiceModel.objects.order_by('-pk').values('description', 'source')
        storages_to = (
            NoteStorageServiceModel.objects
            .filter(user=request.user)
            .order_by('-pk')
            .values('is_default', 'description', 'source')
        ) if request.user.is_authenticated else []
        context = {'storages_from': storages_from, 'storages_to': storages_to}
        return render(request, 'note/note_import_export.html', context)

    def post(self, request):
        # TODO: Использовать web-сокеты для отображения ползунка и статистики на фронте
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        total_count = 0
        command = request.data.get('command')
        if command == 'copy-from-to':
            source_to = request.data['source-to']
            source_from = request.data['source-from']
            for total_count in run_initiator(source_from, source_to):
                ...
        elif command == 'clear':
            source_to = request.data['source-to']
            with get_storage_service(source_to, request.user) as (uploader, source):
                if source == source_to:
                    uploader.clear()
                else:
                    return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'command': ['Неизвестная команда']})

        response_data = {'total_count': total_count}
        return Response(status=status.HTTP_200_OK, data=response_data)
