import os
from urllib.parse import unquote

import yaml
import requests
from django.conf import settings
from django.http import Http404
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

from django_sy_framework.linker.utils import link_instance_from_request
from note.load_from_github import get_storage_service, get_service_names, run_initiator
from note.models import (
    Note,
    NoteStorageServiceModel,
    prepare_to_search,
)
from note.serializers import (
    NoteCreateViewSerializer,
    NoteEditViewSerializer,
    NoteStorageServiceSerializer, ERROR_NAME_MESSAGE,
)


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


@extend_schema(
    tags=['Заметки'],
)
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
def note_hook(request):  # TODO: метод хука планируется перенести в адаптер базы. Сейчас хук не работает
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


class NoteEditorView(APIView):
    @staticmethod
    def get(request, quoted_title=None):
        source = request.GET.get('source') or request.COOKIES.get('source')
        if quoted_title is None:
            if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            link_to = request.GET.get('link_to')
            if link_to:
                source = f'.{link_to}'
                if not NoteStorageServiceModel.objects.filter(source=source).first():
                    storage = NoteStorageServiceModel(
                        service='DjangoServer',
                        description=f'База знаний для внешнего "{link_to}"',
                        user=request.user,
                        source=source,
                    )
                    storage.save()

            context = {'note': None, 'source': source}
            return render(request, 'note/note_editor.html', context)

        with get_storage_service(source) as (uploader, source):
            note = uploader.get(unquote(quoted_title))

        if not note:
            raise Http404('Заметка не найдена')

        _, content_md = separate_yaml(note['content'])
        context = {
            'note': {'title': note['title'], 'content': note['content'], 'content_html': markdownify(content_md)},
            'source': source,
        }
        return render(request, 'note/note_editor.html', context)

    @staticmethod
    def put(request, quoted_title):
        """
        Метод редактирования существующей заметки.

        Обязателен как минимум один из параметров в теле: `new_content` или `new_title`.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = NoteEditViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(quoted_title)
        new_title = data.get('title')
        new_content = data.get('content')

        if title.startswith('.'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'title': [ERROR_NAME_MESSAGE]})

        with get_storage_service(data['source']) as (uploader, _):
            if not uploader.get(title=title):
                return Response(status=status.HTTP_404_NOT_FOUND)

            if new_title and new_title != title and uploader.get(title=new_title):
                response_data = {'title': ['Заметка с таким названием уже существует']}
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)

            updated_fields = uploader.edit(title, new_title, new_content)

        content_yaml, content_md = separate_yaml(new_content)
        return Response(
            status=status.HTTP_200_OK,
            data={'updated_fields': updated_fields, 'content_html': markdownify(content_md)},
        )

    @staticmethod
    def post(request):
        """Метод создания новой заметки"""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = NoteCreateViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = data['title']
        content = data['content']
        source = data['source']

        with get_storage_service(source) as (uploader, _):
            if uploader.get(title=title):
                response_data = {'title': ['Заметка с таким названием уже существует']}
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)

            uploader.add(title, content)

            link_to = request.GET.get('link_to') or (source[1:] if source.startswith('.project-') else None)
            if link_to:
                instance = Note.objects.filter(title=title, storage_uuid=uploader.storage_uuid).first()
                link_instance_from_request(instance, link_to)

        content_yaml, content_md = separate_yaml(content)
        return Response(
            status=status.HTTP_200_OK,
            data={'updated_fields': ['title', 'content'], 'content_html': markdownify(content_md)},
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
                service_maps[subclass_name] = []
                for field_name, field_map in service_map['properties'].items():
                    service_maps[subclass_name].append({'name': field_name, 'map': field_map})

        context = {
            'storage_services': list(storages),
            'service_names': list(NoteStorageServiceModel.CHOICES_SERVICE),
            'service_maps': service_maps,
        }
        return render(request, 'note/note_storage_services.html', context)

    @staticmethod
    def post(request, pk=None):
        """The view edit a storage or create a new storage if pk=0"""
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
        command = request.data['command']
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
