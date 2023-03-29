from urllib.parse import unquote

from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from note.load_from_github import prepare_to_search, get_uploader, get_root_url
from note.credentials import args_uploader
from note.serializers import (
    NoteAddViewSerializer,
    NoteEditViewSerializer,
    NoteResponseSerializer,
    NoteSearchViewSerializer,
)

source_parametr = OpenApiParameter(
    name='source',
    description='Название базы',
    required=False,
    type=str,
    default=settings.DEFAULT_UPLOADER,
    location=OpenApiParameter.QUERY,
    examples=[
        OpenApiExample('Firestore', value='firestore'),
        OpenApiExample('Typesense', value='typesense'),
        OpenApiExample('This django server', value='django_server'),
    ]
)

query_parametr = OpenApiParameter(
    name='query',
    description='URL-кодированая (уникальная) строка',
    required=False,
    type=str,
    location=OpenApiParameter.PATH,
    examples=[
        OpenApiExample('пример', value='page%2Fname')
    ]
)



class NoteSearchView(APIView):
    """Класс метода поиска заметок"""

    @extend_schema(
        tags=['Заметки'],
        parameters=[
            source_parametr,
            NoteSearchViewSerializer,
            query_parametr,
        ],
    )
    def get(self, request, query):
        """Метод для поиска заметок"""
        serializer = NoteSearchViewSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
    
        query = unquote(query)
        search_by = data['search-by']
        fields = data['fields']
        file_name = query if search_by in ('title', 'all') else None
        file_content = query if search_by in ('content', 'all') else None
        fields = ('title', 'content') if fields == 'all' else (fields,)
    
        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        response_data = uploader.search(
            operator=data['operator'],
            limit=data['limit'],
            offset=data['offset'],
            fields=fields,
            file_name=file_name,
            file_content=file_content,
        )
        response_data['source'] = uploader_name
        response_data['path'] = '{}/'.format(get_root_url())
        return Response(status=status.HTTP_200_OK, data=response_data)


class NoteView(APIView):
    """Класс методов для работы с заметками"""

    @extend_schema(
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя запрашиваемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={200: NoteResponseSerializer},
        tags=['Заметки'],
    )
    def get(self, request, title):
        """Метод получения заметки"""
        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        note_data = uploader.get(title=unquote(title))
        if not note_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        note_data['source'] = uploader_name
        return Response(status=status.HTTP_200_OK, data=note_data)

    @extend_schema(
        request=NoteAddViewSerializer,
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя создаваемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={200: NoteResponseSerializer},
        tags=['Заметки'],
    )
    def post(self, request, title):
        """Метод создания новой заметки"""
        serializer = NoteAddViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(title)

        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        note_data = uploader.get(title=title)
        if note_data:
            data = {'detail': 'Заметка с таким названием уже существует'}
            return Response(status=status.HTTP_200_OK, data=data)

        note_data = uploader.add(title, data['content'])
        note_data['source'] = uploader_name
        return Response(status=status.HTTP_200_OK, data=note_data)

    @extend_schema(
        request=NoteEditViewSerializer,
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя редактируемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={200: NoteResponseSerializer},
        tags=['Заметки'],
    )
    def put(self, request, title):
        """
        Метод редактирования существующей заметки.
        
        Обязателен как минимум один из параметров в теле: `new_content` или `new_title`.
        """
        serializer = NoteEditViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(title)
        new_title = data.get('new_title')

        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        if not uploader.get(title=title):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if new_title and new_title != title and uploader.get(title=new_title):
            response_data = {'detail': 'Заметка с таким названием уже существует'}
            return Response(status=status.HTTP_200_OK, data=response_data)

        note_data = uploader.edit(title, new_title, data.get('new_content'))
        note_data['source'] = uploader_name
        return Response(status=status.HTTP_200_OK, data=note_data)

    @extend_schema(
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя удаляемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={201: None},
        tags=['Заметки'],
    )
    def delete(self, request, title):
        """Метод удаления заметки"""
        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        note_data = uploader.get(title=unquote(title))
        if not note_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        uploader.delete(title)
        return Response(status=status.HTTP_201_NoContent)
