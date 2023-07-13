import os
from urllib.parse import unquote

import yaml
import requests
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.views import View
from drf_spectacular.utils import extend_schema
from markdownify.templatetags.markdownify import markdownify
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework import status

from note.credentials import args_uploader
from note.load_from_github import prepare_to_search, get_root_url, get_uploader
from note.models import Note
from note.models import NoteStorageServiceModel
from note.serializers import NoteEditViewSerializer
from note.serializers import NoteStorageServiceSerializer


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
def note_hook(request):
    """Хук для обновления заметок на сервере из принятого Pull Request'а на Github"""
    data = {'files': {}}
    action = request._request.headers.get('X-Github-Event')
    if action == 'push':
        repository = request.data.get('repository')
        repo_name = repository.get('name')
        owner_name = repository.get('owner').get('name')
        if owner_name != settings.GITHUB_OWNER or repo_name != settings.GITHUB_REPO:
            return Response(status=status.HTTP_200_OK, data={'message': 'repository or owner name has no access'})

        link = get_root_url(owner=owner_name, repo=repo_name, raw=True)
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
                url = f'{link}/{file}'
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
    def get(request, quoted_title):
        note = get_object_or_404(Note, title=unquote(quoted_title))
        content_yaml, content_md = separate_yaml(note.content)
        context = {'note': {'title': note.title, 'content': note.content, 'content_html': markdownify(content_md)}}
        return render(request, 'pages/note_editor.html', context)

    @staticmethod
    def post(request, quoted_title):
        """
        Метод редактирования существующей заметки.

        Обязателен как минимум один из параметров в теле: `new_content` или `new_title`.
        """
        #self.authenticate()
        serializer = NoteEditViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(quoted_title) #data.get('title')
        new_title = data.get('new_title')
        new_content = data.get('new_content')

        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        if not uploader.get(title=title):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if new_title and new_title != title and uploader.get(title=new_title):
            response_data = {'detail': 'Заметка с таким названием уже существует'}
            return Response(status=status.HTTP_200_OK, data=response_data)

        updated_fields = uploader.edit(title, new_title, new_content)
        content_yaml, content_md = separate_yaml(new_content)
        return Response(
            status=status.HTTP_200_OK,
            data={'updated_fields': updated_fields, 'content_html': markdownify(content_md)},
        )


class NoteListView(View):
    def get(self, request):
        page_number = request.GET.get('p', '1')
        page_number = int(page_number) if page_number.isdecimal() else 1

        notes = Note.objects.all()
        paginator = Paginator(notes, 20)
        page = paginator.page(page_number)
        context = {
            'notes': page.object_list,
            'last_page': paginator.num_pages,
            'current_page': page_number,
            'next_page': page_number + 1,
            'prev_page': page_number - 1,
        }
        return render(request, 'pages/note_list.html', context)


class NoteStorageServiceListView(View):
    def get(self, request):
        storages = NoteStorageServiceModel.objects.order_by('-pk')
        if request.user.is_authenticated:
            storages = storages.filter(user=request.user).values('service', 'description', 'is_default', 'source', 'pk')
        else:
            storages = storages.values('service', 'description', 'source', 'pk')

        storages.extend([
            {'service': 'Typesense', 'description': 'моя первая база', 'is_default': False, 'source': 'first', 'pk': 1},
            {'service': 'Firebase', 'description': 'мой дневник', 'is_default': True, 'source': 'dairy', 'pk': 2},
            {'service': 'Typesense', 'description': 'для поиска по холстам', 'is_default': False, 'source': 'for_searching', 'pk': 3},
        ])

        context = {
            'storage_services': storages,
        }
        return render(request, 'pages/note_storage_services.html', context)

    def post(self, request, pk=None):
        if pk:
            instance = NoteStorageServiceModel.objects.get(pk=pk)
            serializer = NoteStorageServiceSerializer(instance, data=request.data)
        else:
            serializer = NoteStorageServiceSerializer(data=request.data)

        serializer.save()

        response_data = {}
        return Response(status=status.HTTP_200_OK, data=response_data)
